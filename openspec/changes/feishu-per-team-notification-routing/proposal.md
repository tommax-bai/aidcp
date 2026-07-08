## Why

现在多账号的飞书**出站 I/O 是单例**：所有账号的通知、告警、审批卡都塌缩到同一个默认群——`resolveDefaultChatId`（`aidcp-cloud/src/feishu/chat-target.ts:18`）不接收 accountId，只返回 `bot_chats` 默认群 → `FEISHU_CHAT_ID` → 空串。而数据层（`notification_event.account_id`）与编排层（每连接私有 EventBus + RoleDispatcher + 风控）**本就按账号**，唯独飞书收发没落地这层身份。运营诉求：不同团队 / 客户只收到**自己账号**的通知，能分开接收、处理。

已定平台方案：**一个企业自建应用开启「对外共享」，每个客户 / 团队一个飞书外部群**，机器人按账号把通知投到对应外部群——**单应用、单令牌、单长连接**，不引入多应用。团队键复用已有的 `accounts.group_label`（自由文本，已有 `PUT /api/accounts/:id/group-label`）。核心改动只有一句：**发消息前先按「消息属于哪个账号 → 该账号属于哪个团队 → 该团队对应哪个群」路由，查不到就退回今天的默认群、绝不静默丢。**

## What Changes

- **【新出站路由】** 新增账号级目标解析 `resolveChatIdForAccount(accountId?)`，叠在**不动的** `resolveDefaultChatId` 之上：读账号 `group_label` → 查新表 `group_route` 得 `chat_id`；命不中落回默认群链。**空表 = 今天行为一字不改，未绑定账号一律落默认群、绝不静默丢。**
- **【新映射存储】** 新增 `group-route-store` + 表 `group_route(group_label → chat_id)`，schema 在 `init()` 里 `CREATE TABLE IF NOT EXISTS` **自建**并接入启动 init 链（本仓无 migration runner）；单写者模板（`UPDATE ... RETURNING` 读回为真、可区分地诚实拒绝、审计字段）。新增 `getGroupLabel` 纯读。
- **【自主推送改路由】** 巡视通知（`notifyComments`）、排期发帖 / 评论 / 群评回执、persona / captcha / 参照创作等**自主推送**发送点换用新解析器（accountId 多已在手；无 accountId 的告警落默认群、不单建 scope）。
- **【命令回执走源群】** 命令触发的结果卡 / 审批卡走「**回下命令的那个群**」，不走账号映射（否则从管理群 `/comment` 一个别队账号，异步结果卡会飘到别队群）。精确规则：**命令回执 / 审批走源群；账号→群映射只管自主推送。**
- **【入站作用域·安全闸】** 外部客户群 = **纯通知投递、拒绝命令**；命令 + 审批只在**内部管理群**受理。修 `/bind` 越权（今天任何人 `/bind` 就把自己升为全局默认群）、修带显式 accountId 的 `/status|/pause|/resume` 绕过一切作用域。
- **【后台配置】** 新增 `GET/PUT /api/notification/routes`（管 `group_label→chat` 映射）+ `GET /api/bot-chats`（只读列「机器人实际所在群」供下拉选，杜绝手贴 raw chat_id / 模糊匹配 → 防映射错群）；绑定目标是 opaque `chat_id`（`TEXT` 非枚举，结构性避开 console 枚举漂移白屏）。console 一张映射表。
- **【运营 runbook】** 附「如何开对外共享认证 + 逐客户建外部群 / 拉客户成员 / 加机器人 / 指定自然人群主」的操作手册。

> 非 BREAKING：出站解析层叠加、空表零行为变更；入站作用域默认放行（只收紧内部管理群语义与显式 accountId 路径），不锁死现有运营群。edge 零改动、协议不动、风控单写不动、审批信号文件路径不变。

## Capabilities

### New Capabilities
- `feishu-notification-routing`: 账号 → 团队（`group_label`）→ 飞书群的**出站目标解析**能力——含 `group_route` 存储与自愈式 schema、`resolveChatIdForAccount` 逐层 try/catch 穿透与诚实兜底（未绑定 / 读失败一律落默认群、config-gap 可观测、绝不静默丢或抛入投递闭包）、自主推送 vs 命令源群的路由分工、映射错群防线（显式绑定 + 群选择器 + 不模糊匹配）、以及路由配置的面板 API（`/api/notification/routes`、`/api/bot-chats`）与账号隔离 / PII 红线。外部群平台约束（仅自建应用支持对外共享、机器人不能当群主、外部成员只拿 open_id、部分 API 不支持、需一次性认证）作为落地前置记录。

### Modified Capabilities
- `feishu-command-ingestion`: 命令入站新增**作用域闸**——外部群命令一律拒（外部客户群纯通知投递）、命令 + 审批只在内部管理群受理；`/bind` 不再对任意群授予全局默认 / 管理语义（管理群改为独立显式配置）；带显式 accountId 的 `/status|/pause|/resume` 必须校验来源群有权管理该账号，否则诚实拒。

## Impact

- **aidcp-cloud（全部工作量集中于此，edge / 协议零改）**
  - 新模块 `src/cache/group-route-store.ts` + 表 `group_route`（`init()` 自建，接入 `src/server.ts` 启动 init 链，仿 `notification-contact-store` 装配）。
  - `src/account-store.ts`：新增 `getGroupLabel(accountId)` 纯读（今天只有 `setGroupLabel`）。
  - `src/feishu/chat-target.ts`：新增 `resolveChatIdForAccount(accountId?, deps)`；`resolveDefaultChatId` 保持不动作为兜底末端。
  - `src/server.ts`：自主推送发送点（`notifyComments` ~1738、评论审批卡 ~1607、persona-setup 告警 ~1624、排期回执 ~2153/2180/2222、参照创作 ~2681）换用新解析器；`comm/captcha-coordinator.ts` 的 `resolveChatId` 注入换成账号级（accountId 可选，undefined 落默认）；无 accountId 的 config-error 告警（~1639）直接默认群；`comm/handler.ts:558` 边缘发起审批由 `session.edgeId` 推 accountId、推不出落默认。
  - `src/feishu/commands.ts` + `src/server.ts`：`runComment` 接 `context.chatId`（结果卡回源群）；`CommandActions` 三启停动作接来源群、非管理群拒；`requireCommandAccount`（server ~1184）显式 accountId 路径加来源群作用域校验；`/bind`（`runBind` ~393）改为不授予全局 / 管理语义或挪 panel-only。
  - `src/cache/bot-chat-store.ts`：新增 `listActive()` 只读（无 DDL）。
  - `src/panel/panel-server.ts` + `src/panel/types.ts`：新增 `GET/PUT /api/notification/routes`（写者注入 `PanelDeps`，仿 `notificationContact`）+ `GET /api/bot-chats`（复用已注入 `botChatStore`）。
- **aidcp-console**：新增一张 `group_label→chat` 映射表（下拉数据来自 `GET /api/bot-chats` + 自由文本兜底）；无新枚举、绑定目标为 opaque `chat_id`。
- **DB**：新表 `group_route`（自愈式 `CREATE TABLE IF NOT EXISTS`，配套迁移文档编号）；不改 `accounts` / `bot_chats` / `notification_event` 结构。
- **协议 v2**：不触发四处同步（纯 cloud 出站解析 + 配置 + 入站作用域，不跨 8787 边界）。
- **红线**：静默假成功双向防（值路径未绑定落默认 + config-gap 日志；异常路径每层 try/catch 穿透、绝不抛入投递闭包）；**映射错群 = 跨客户 PII 泄漏**（客户 A 通知含第三方昵称 / 评论进客户 B 外部群）——查不到落默认内部群安全，危险的是错映射，故强制显式绑定 + 群选择器 + 不模糊匹配；审批信号文件路径 `/tmp/aidcp-publish-approve-<requestId>.json` 不变；不动 `notification_contacts` 全局可读面与 console 全局管理面（诚实边界写进 design）。
- **不做（YAGNI）**：不建 JSONB `channel_ref` / `scope_type/scope_key` 多态 / `bot_id` 列 / per-account 覆盖层 / 多应用运行时；将来真要多应用（分租户 / 品牌硬隔离）加一列 `bot_id` 是 additive 一行的事，design 留一句 gated 说明、不预建接缝。
