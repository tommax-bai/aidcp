## Context

云端飞书是**单例收发**：一个企业自建应用（`FEISHU_APP_ID/SECRET`）、一条入站长连接（`FeishuWsReceiver`）、一个默认群解析 `resolveDefaultChatId`（`aidcp-cloud/src/feishu/chat-target.ts:18`）。约 10 个自主推送发送点全塌缩到这一个群，其中最典型的是巡视通知 `notifyComments`（`src/server.ts:1738`）——闭包里 `ctx.accountId` 明明在手（`:1669` 还用它写了联系人库）却在投递时丢弃。数据层（`notification_event.account_id`）与编排层（每连接私有 EventBus + RoleDispatcher + 风控，`multi-tenant-orchestration`）本就按账号，唯飞书 I/O 没落地这层身份。

运营诉求：不同团队 / 客户只收到**自己账号**的通知。经飞书平台能力核实，**一个自建应用开启「对外共享」即可被拉进任意多个外部群、在每个群收发**（[飞书文档](https://open.feishu.cn/document/develop-robots/add-bot-to-external-group?lang=zh-CN)）。因此采用**单应用 + 每客户一个外部群 + 按账号路由**，不引入多应用。团队键复用已有自由文本 `accounts.group_label`（已有 `PUT /api/accounts/:id/group-label`）。

约束（本仓 CLAUDE.md 铁律）：边轻云重（纯 cloud、edge 零改）；绝不静默假成功；协议四处同步不得触发；风控单写不动；审批信号文件路径为共享 edge↔cloud 契约不得漂移；无 migration 执行器，新表须 `init()` 自建；console 枚举漂移会整页白屏。

## Goals / Non-Goals

**Goals:**
- 按「账号 → 团队（`group_label`）→ 群」把**自主推送**路由到对应（含外部）群；查不到落默认群、绝不静默丢。
- 命令回执 / 审批卡走**源群**，不走账号映射。
- 入站加**作用域安全闸**：外部群纯通知投递、拒命令；`/bind` 不再自助提权；显式 accountId 命令过来源群校验。
- 后台可配 `group_label→chat` 映射，目标从「机器人实际所在群」清单里选，杜绝手贴 / 模糊匹配导致的错映射（= 跨客户 PII 泄漏）。
- 空表 = 今天行为逐字不变；可秒级回滚（清空表 / 关配置即回默认群）。

**Non-Goals:**
- **不做多应用 / ISV**：单应用 + 外部群已满足同 / 跨租户接收方。多应用留作未来 gated 改动。
- **不做 per-account 覆盖层**（某账号路由到本团队之外）——无人提的需求。
- **不做完整团队隔离**：本变更只改「推送去哪」，不动 console 全局管理面、不动 `notification_contacts` 全局可读面（`listContacts(undefined)` 仍返全量 PII）。交付的是「每团队外部群 + 一个看得见一切的内部管理面 / 群」，非租户级隔离。
- **不做内部管理群之间的 per-team 账号细分作用域**：本版把账号命令收口到「管理群 vs 非管理群」二元闸；若将来运营方内部按团队分多个管理群需各管一批账号，再作为独立细化（见 Open Questions）。

## Decisions

### D1: 团队键复用 `accounts.group_label`，不建团队注册表
一个团队绑一行 `group_route(group_label PRIMARY KEY, chat_id, updated_by, updated_at)`，而非 M 个账号各绑一行。`group_label` 已是账号自由文本分组维度、已有编辑入口。
- **备选**：新建 `team` 实体表 + 账号外键。**否**——YAGNI；`group_label` 够用，代价是自由文本拼写不一致会漏配，用 config-gap 日志 + 后台下拉（而非手输团队键）缓解。

### D2: 解析器层叠，`resolveDefaultChatId` 不动
新增 `resolveChatIdForAccount(accountId?, deps)`：`getGroupLabel(accountId)` → 查 `group_route` → 命中返回；否则调用**原封不动**的 `resolveDefaultChatId`。
- **理由**：叠加而非替换 = 空表零行为变更 + 兜底逻辑单点不重复 + 秒级回滚。
- **红线**：每层读各自 try/catch、失败向下穿透，**绝不抛入投递闭包**（`notifyComments` 闭包一旦让 SELECT 异常冒泡，会整批通知作废且连「无可用飞书群」都不打 = 异常路径的静默假成功）。需新增 `getGroupLabel` 纯读（今天只有 `setGroupLabel`）。

### D3: 自主推送按账号、命令回执走源群
- **自主推送**（`notifyComments`、排期发帖 / 评论 / 群评回执、persona / captcha / 参照创作告警）→ `resolveChatIdForAccount(ownerAccountId)`。
- **命令触发**的结果卡 / 审批卡 → 源群（`ws-receiver.ts:239` 已回源群；需把 `sourceChatId` 穿进 `runComment`（`commands.ts:270` 今天没接 `context.chatId`）；`publish-executor.ts:372` 的 `resolveApprovalCardTarget` 保持 `manualApprovalChatId → 默认群`、不插账号层）。
- **无 accountId 告警**（config-error 握手拒绝 `server.ts:1639`、无可解析账号的 captcha）→ 直接默认群，不臆造 scope。`handler.ts:558` 边缘发起审批由 `session.edgeId` 推 accountId、推不出落默认。
- **理由**：源群语义修的是「谁问谁得答」；账号映射修的是「主动通知去对的团队」。混用会让「管理群对别队账号下命令」的异步结果飘到别队群。

### D4: 入站二元作用域闸（管理群 vs 非管理群），管理群独立配置
账号影响类命令只在**显式管理群**受理；外部 / 非管理群一律诚实拒。管理群是独立显式配置（面板 / 独立标志），**不复用** `is_default`、**不由 `/bind` 授予**。带显式 accountId 的 `/status|/pause|/resume`（`requireCommandAccount` `server.ts:1184` 今天直接 `return accountId`）与单账号 / 空昵称短路（`server.ts:987/1192`）都要接来源群、过同一作用域判定。
- **备选**：per-account ∪ per-group 集合并集判定。**否**——并集会让「per-account 绑 A 群、group_label 又映射 B 群」的账号同时落两个集合、B 群能 pause 它 = 跨队泄漏。入站 / 出站**复用同一 resolve**，防两半漂移。
- **理由**：外部群里坐着不可信的客户成员，命令闸是必须；`/bind` 自助提权是现存越权面，必须先堵。

### D5: 后台绑定目标为 opaque `chat_id` + 群选择器
`GET/PUT /api/notification/routes` 管映射；**新增 `GET /api/bot-chats`**（`bot-chat-store` 加 `listActive()` 只读、无 DDL）列机器人实际所在群供下拉。绑定值是 `TEXT` 而非枚举。
- **理由**：绑定目标非枚举 → 结构性避开 console↔cloud 枚举漂移白屏（已知失败模式）；群选择器杜绝手贴错 `chat_id` → 防映射错群的跨客户 PII 泄漏。运营选不到（机器人不在该群）就配不出，天然拦截误配。

### D6: 存储自愈式 schema
`group_route` 在 `init()` 里 `CREATE TABLE IF NOT EXISTS` 自建、接入启动 init 链（仿 `notification-contact-store` 装配），配套迁移文档编号但不依赖执行器。
- **理由**：本仓无 migration runner——`bot-chat-store` 曾因只有迁移文件无 `init()` 自建而是前车之鉴。

## Risks / Trade-offs

- **[映射错群 = 跨客户 PII 泄漏]** 账号→外部群填错，客户 A 通知（含第三方昵称 / 评论原文）进客户 B 群。→ 缓解：查不到**落默认内部群是安全的**（不外泄），危险的只是**错映射**；故强制显式绑定 + 群选择器（D5）+ 精确相等匹配、绝不模糊（spec R6）。
- **[异常路径静默假成功]** 解析层 SELECT 抛异常冒泡进投递闭包 → 整批通知无声作废。→ 缓解：每层 try/catch 穿透（D2、spec R2），回归用例覆盖「读抛错仍落默认群投递」。
- **[自由文本团队键漏配]** `group_label` 大小写 / 空白不一致静默落默认。→ 缓解：config-gap 日志（spec R3）+ 后台下拉团队键（减少手输）。
- **[过渡期非隔离]** 账号没绑 / 键打错，其评论 / @ 通知（含第三方 PII）落共享内部默认群。→ 明确接受：过渡态是「非隔离但不外泄」，随绑定完善收敛；DM / 私聊命令按 D4 一律拒。
- **[外部群平台约束]**（落地前核对，写进 runbook）：仅自建应用支持对外共享（store/ISV 不支持）；机器人不能当外部群群主、须指定自然人；外部成员只拿 open_id、查不到通讯录（对推送无影响，对解析发送者身份的功能失效）；外部群有部分 API 不支持——须核对我们用的 `im/v1/messages`（text + interactive card）+ reactions 均在支持列表；开对外共享需一次性企业 / 团队 / 实名认证。
- **[Ops 读放大]** 出站每条通知多 1–2 次 PG 读（`getGroupLabel` + `group_route`）。→ 巡视频繁时可加进程内小缓存、面板写时失效；入站作用域判定用索引查询、不逐账号全表扫。
- **[审计缺口]** 面板 / 飞书命令today未记「谁 pause 了哪个账号」。→ 本版随作用域闸补 actor 记录（`updated_by`），命令侧 actor 记录列为后续。

## Migration Plan

1. **DB**：`group_route` 由 `init()` 幂等自建，随服务启动生效；无独立迁移步骤。空表 = 零行为变更。
2. **部署**（dev 默认，按 CLAUDE.md §5 安全序列）：备份 → rsync（排除 `.env`/`node_modules`/`.git`）→ restart → healthcheck（`active` + 8787 + 飞书长连接 + PG `select 1`）。
3. **对外共享 & 外部群**（运营 runbook，非代码）：一次性开对外共享认证 → 逐客户建外部群、拉客户成员（对方确认、须在应用可用范围）、加机器人、指定自然人群主 → 面板从 `GET /api/bot-chats` 选群绑定 `group_label`。
4. **回滚**：清空 `group_route`（或关配置）即回默认群单群行为，秒级；代码回滚走既有备份还原。

## Open Questions

- **内部多管理群的 per-team 账号细分**：若运营方内部按团队分多个管理群、各只管一批账号，是否需要把 D4 的二元闸细化为「管理群 → 可管账号集」？本版按 YAGNI 不做，留作独立细化；细化时复用同一 resolve、按 `group_label` 索引查询、绝不集合并集。
- **无归属告警是否要独立 ops 群**：config-error / 无账号 captcha 现落默认群即可（有人盯即可），是否单拆一个 ops 群由运营定，不阻塞本版。
- **多应用（Phase 2）**：仅当将来出现「客户要自己品牌的独立机器人」或真正的凭证硬隔离诉求才启动；届时加一列 `bot_id`（additive）并建多应用运行时。本版不预建任何接缝基础设施。
