## Context

账号那串「关联群聊引流码」在库里是一个原样存储的可选文本（`accounts.group_chat_info`，不 trim / 不截断 / 无格式约束）。上层只有两条语义：非空则在人审卡前 verbatim 追加到评论末尾、为空则 fail-closed 不发。它经飞书 `/comment <昵称> group:on/off` 逐次 opt-in 触发，也被内容排期「群评」动作与精选内容「带群评论」复用同一条命令式评论管线注入。

命名把它锁死在「群聊 / 群码 / 引流」一种载体，但它承载的其实是任意「联系串」：小红书群码、微信号、电话，Facebook 侧的 Zalo 号 / 电话。本 change 把整条链正名为平台无关的「联系方式」（contact info），数据语义与所有安全红线一律不变。

现状盘点（多 agent 审计 + 三路对抗性评审已核，`文件:行` 为当时快照，实装时以真实文件为准）：
- **cloud**：`account-store.ts`（列 `:50` + 方法 `setGroupChatInfo/getGroupChatInfo` + 类型 `SetGroupChatInfoResult`）、`feishu/commands.ts`（`group:on/off` 解析 + `injectGroup` + HELP + 结果卡）、`comment-agent/{comment-scheduler,compose-approve,edge-steps,comment-task-runner}.ts`、`orchestrator/content-scheduler.ts`（群评特性）、`server.ts`（接线 + 结果卡文案 `:2313`）、`panel/{panel-store,panel-server,types,version}.ts`、`config/content-schedule-store.ts`、`comm/protocol.ts`（wire 字段 `groupChatCode`）。
- **edge**：`comm/protocol.ts`（与 cloud 逐字同源的 `groupChatCode`）、`browse/browse-session.ts`（`executeComment` 消费 `payload.groupChatCode`）、probe 脚本。
- **console**：`types/api.ts`（`groupChatInfo` DTO + `hasGroupCode` 等）、`components/AccountsTable.tsx`（「群聊引流」列 + 就地编辑 + 多账号同码告警）、`pages/{AccountsPage,ContentSchedulePage,CuratedContentPage}.tsx`、`api/errorText.ts`、多个 `.test.tsx`。

## Goals / Non-Goals

**Goals:**
- 全栈把「群聊引流码 / 群码 / 引流 / 群评」正名为「联系方式 / 联系评论」（contact / `contactInfo` / `contact_info` / `contactComment`）。
- 命令语法 `group:on/off` → `--contact`（干净切换）。
- 底层物理名也物理改名：DB 列 `group_chat_info → contact_info`、协议 wire 字段 `groupChatCode → contactInfo`——用硬化迁移保数据、保 wire 兼容。
- 保持数据语义、fail-closed、「审=发」、「绝不静默假成功」全部红线不变。
- 跨仓 / 跨端契约原子化：不产生「后台白屏」或「评论悄悄漏贴联系方式」。

**Non-Goals:**
- 不改数据模型（仍是单列可选文本、仍原样存储）。
- 不碰按团队通知路由（`group_label` / `GroupRoute` / `setGroupLabel`）、飞书会话类型（`chatType:'group'`）、facebook 那个语义相反的「contact info」校验器（它**拒绝** AI 文案里的联系方式）、通知联系人名册（`notification-contact-registry`）。
- 不改历史 change slug / archive 目录 / 已应用迁移文件名（作为 provenance 保留）。
- 不改 openspec capability 目录 id `group-chat-injection`（见 Decision 6）。

## Decisions

### Decision 1：术语与词形——统一 contact / 联系方式
- 中文文案统一「联系方式」；「群评」→「联系评论」。
- 通用词形：`groupChatInfo`/`groupChatCode`(内部) → `contactInfo`；`injectGroup` → `injectContact`；`setGroupChatInfo`/`getGroupChatInfo` → `setContactInfo`/`getContactInfo`；`SetGroupChatInfoResult` → `SetContactInfoResult`；`groupComment*` → `contactComment*`；action `'group_comment'` → `'contact_comment'`；`hasGroupCode` → `hasContactInfo`。
- 错误码：`invalid_group_chat_info` → `invalid_contact_info`；`no_group_code` → `no_contact_info`；`group_code_missing` → `contact_info_missing`。
- **携带一码一号放松**（change `loosen-group-comment-shared-code` 已归档、晚于本 change 提出）：`shared_group_code`（旧硬拒 reason）**已废除**，改名对象是成功侧警告字段 `sharedGroupCodeWarning` → `sharedContactInfoWarning`。本 change MUST 保留放松语义（共用放行 + 警告），MUST NOT 恢复 `shared_*` 硬阻断；`no_group_code`（无码硬拒）保留、改名为 `no_contact_info`。
- HTTP 路由：`/api/accounts/:id/group-chat-info` → `/contact-info`。
- **Why `--contact` 而非 `--connect`**：与字段 / 概念 / DB 列名 `contact` 全一致，读代码零歧义（用户拍板）。

### Decision 2：命令语法干净切换（无 `group:on` 别名）
- `/comment <昵称> group:on/off` → `/comment <昵称> --contact`。解析仍 **trailing-only**（`--contact` 必须是最后一个 token），「present=on、缺省=off」，对齐今天 `injectGroup=undefined`=不注入的行为。
- 旧 `group:on/off` **立即失效**（用户选干净切换）：若运营误发旧写法，末尾 token 会被当作昵称的一部分 → 走「找不到该昵称账号」的既有诚实失败路径，不会静默注入、不踩红线。
- 飞书 HELP_TEXT 与结果卡里写死的 `/comment group:on` 文案（含 `server.ts:2313` 那句「手动 /comment group:on 不受此限」）一并换成 `--contact`。
- **Why 可以硬切**：命令解析只在云端单点，无分布式滞后；边缘不参与命令语法。

### Decision 3：DB 列物理改名——协调单写迁移（非自愈）
现状 schema 靠启动自建（`CREATE TABLE IF NOT EXISTS` + `ADD COLUMN IF NOT EXISTS`），无迁移器。`ADD COLUMN IF NOT EXISTS` **不会 rename**——若直接把自愈 DDL 改成 `contact_info`，老库会新增空 `contact_info`、老数据留在 `group_chat_info` = 数据分裂。

方案：新增前向迁移 + 幂等 guard，放在自愈 DDL 之前：
```sql
DO $$
BEGIN
  SET LOCAL lock_timeout = '3s';
  IF EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema = current_schema()
               AND table_name='accounts' AND column_name='group_chat_info')
     AND NOT EXISTS (SELECT 1 FROM information_schema.columns
             WHERE table_schema = current_schema()
               AND table_name='accounts' AND column_name='contact_info')
  THEN
    ALTER TABLE accounts RENAME COLUMN group_chat_info TO contact_info;
  END IF;
END $$;
ALTER TABLE accounts ADD COLUMN IF NOT EXISTS contact_info TEXT;
```
硬化点（对抗性评审要求，缺一不可）：
- **schema-qualified**（`table_schema = current_schema()`）——避免多 schema 下 `information_schema` 误判而 `ALTER TABLE accounts` 走 `search_path` 命中另一张表。
- **`SET LOCAL lock_timeout`**——`RENAME` 要 ACCESS EXCLUSIVE，共享 dev 库高竞争时不至于挂起 boot；超时则 `init()` 快速失败（可重试），优于无限等。
- **同一 deploy 删除旧 `ADD COLUMN group_chat_info` 行**——否则未升级的旧构建 `init()` 会把空 `group_chat_info` 复活（僵尸列脑裂：老代码读空列 → 评论漏贴联系方式）。
- **作为协调单写迁移**：dev 共库上先确认无未升级旧 cloud 进程长期并存；cloud 单 ECS + systemd 整体重启，风险窗口≈重启秒级。
- 群评特性的物理列同法迁移：`group_comment_enabled/daily_cap → contact_comment_enabled/daily_cap`、`group_comment_attempts` 表族（`recordGroupCommentAttempt`/`countGroupAttemptsToday` 读写）——各自一段 guarded RENAME。
- 迁移文件：**不改**历史 `0027_account_group_chat_info.sql`（文件名编码旧概念、改它破坏台账）；新建 `migrations/00XX_rename_group_chat_info_to_contact_info.sql`（含群评列）+ 与 `account-store.ts` 自愈 DDL 逐字同源。
- **Alternatives considered**：① 只改上层、DB 列名保留（零迁移风险，但库里残留旧名与代码不一致；用户明确要物理改名，否）；② 双列 dual-write 过渡（写 dual-write + 读 coalesce，复杂度远超收益，否）。

### Decision 4：协议 wire 字段改名——硬化过渡（双发 + 双读），绝不硬切
`groupChatCode` 是 §2 协议四处同步热点 + cloud/edge **分离部署**（cloud 单 ECS、edge 跑分散且部署滞后的运营机）。边缘读法 `payload.groupChatCode ?? ''`——**字段名不匹配即静默降级**：评论照发但不带联系方式、回执 `ok`、无 reason。这正是「静默假成功」红线，且协议穷举 typecheck（`Record<MessageType,true>`）**抓不到 payload 内部字段改名**。

硬化过渡（多版本，绝不单侧硬切）：
1. **同一 commit** 改两份 `protocol.ts`：payload 同时声明 `contactInfo?` 与 `groupChatCode?`（都 optional），逐字同源。
2. 边缘消费改双读：`payload.contactInfo ?? payload.groupChatCode`（`browse-session.ts`）——先升级边缘、保证既能读新键也能读旧键。
3. 云端生产者 **dual-emit 两键**（`edge-steps.ts` 发 `{ contactInfo, groupChatCode }` 同值）——过渡期让任何版本边缘都能对上。
4. 待所有运营机升级到含双读的 edge 后，云端切成只发 `contactInfo`。
5. 再下一版把 `groupChatCode` 从两份 protocol 删除、边缘去掉旧键兜底。
- **Why 不硬切**：「所有运营机已升级」不可证（无 per-edge 版本握手）；一台滞后即静默漏贴。dual-emit 是评审确认的唯一安全形态。
- 协议路由白名单（§2 第四处，`edge-client.ts` 的 `interaction.comment` 放行）**不涉及**——路由按消息 type、非 payload 字段，命令照常到处理器，只是字段名要对上。
- 补 `docs/protocol.md`：现根本没记 `interaction.comment` 的注入字段，本次 ADD（非 find/replace）。

### Decision 5：跨仓 panel 契约同波（cloud + console）
四个 wire 面单边改即白屏 / 静默失效：
- DTO 字段 `groupChatInfo`（cloud `panel-store.ts` ↔ console `types/api.ts`）+ `version.ts` 的 `PANEL_ACCOUNT_FIELDS` 指纹（`_AssertNever` 强制键一致，**必须同 commit**，不能加别名）。
- HTTP 路由 `/contact-info` ↔ console 请求。
- 请求 / 响应体字段。
- 错误码。
策略：cloud + console **同一波**（先 cloud、console 紧随）；路由与错误码过渡期**新旧双认**（cloud 同时接 `/contact-info` 与 `/group-chat-info`、console `errorText` 同匹配新旧串）吸收静态资源缓存滞后；DTO 字段与指纹硬同波。
- **精选内容 `withGroup` 是隐藏的第五个 wire 面**（评审补出）：console 发 `{withGroup}` → 云端 `panel-server.ts` 读 `parsed.withGroup`（body 是 `as unknown`，typecheck 抓不到）。只改一边 → 云端读 `undefined` → 不注入、无报错 = 红线。`withGroup → withContact` 必须与前端**同波**。

### Decision 6：openspec capability 目录 id 保留
`group-chat-injection` 目录 id 是文档 / 契约标识、非运行系统命名、非代码符号。本 change 用 RENAMED + MODIFIED 把其 6 条需求的**标题与正文**全部正名为「联系方式 / --contact」，但**保留目录 id**（类比保留迁移文件名、change slug 作 provenance）。彻底搬迁目录要重写所有指向它的 delta 路径、复杂化归档合并，收益仅整洁——不做。若后续要彻底正名，另开轻量 change。

## Risks / Trade-offs

- [wire 字段单侧改 → 评论悄悄漏贴联系方式（红线）] → Decision 4 双发 + 双读 + 多版本过渡；两份 protocol.ts 同 commit 逐字同源；acceptance 断言注入路径。
- [DB `RENAME` 在共享 dev 库挂起 boot / 僵尸列脑裂] → `lock_timeout` + schema-qualified guard + 同 deploy 删旧 `ADD COLUMN` 行 + 迁移前备份库；cloud 单 ECS 整体重启压缩并存窗口。
- [panel DTO / 指纹单边改 → 后台整页白屏] → Decision 5 同波 + 路由 / 错误码双认 + DTO 硬同 commit；cloud typecheck 的 `_AssertNever` 先兜底键一致。
- [`comment-task-runner.ts` 的 `CommentTaskSteps` 接口漏改 → cloud typecheck 失败] → 纳入 cloud 阶段改名清单（评审补出的必改点）。
- [遗漏用户可见旧命令文案（HELP / 结果卡 `server.ts:2313`）→ 运营仍看到 `group:on`] → 明确列入任务。
- [误伤同名不同义概念] → Non-Goals 列出 mustNotTouch；实装用「先读上下文再改」而非全局 `s/group/`。
- [语义撞车] → facebook「contact info」校验器语义相反，保持两套、评论注入串绝不过该校验器。

## Migration Plan

部署波次（dev 默认目标，走安全序列：备份 → rsync → restart → healthcheck → 失败回滚；绝不碰同机 isales）：
1. **cloud 内部 + DB + 命令**（一波）：账号存储方法 / 类型 / 命令 `--contact` / 调度 / 撰写 / 边侧适配 / `comment-task-runner` / 群评特性 / 结果卡文案 + **新增前向迁移**（guarded RENAME）。edge-steps **dual-emit** 两键。关卡：`test:acceptance` → `test` → `typecheck`（AC-PROTO / fail-closed 全过）。迁移前 dev 备份库。
2. **cloud panel + console**（强制同波，先 cloud、console 紧随）：DTO / 路由 / 错误码 / `version.ts` 指纹 / `withGroup→withContact` 云端接收端 + console 全量文案与测试。关卡：cloud `typecheck`（`_AssertNever`）+ console `typecheck` + `test`。
3. **edge**（与 cloud 协调）：`protocol.ts` 双声明（同 commit 逐字同源）+ `browse-session` 双读 + probe 文案。关卡：edge `test:acceptance` → `test` → `typecheck`。待运营机全升级。
4. **收尾切换**（下一版）：确认运营机全升级 → cloud 只发 `contactInfo` → 再下一版删两份 protocol 的 `groupChatCode` 与边缘旧键兜底。
5. **文档 + archive**：补 `docs/protocol.md`、回写 tasks.md（sha 标注）、真机项登记 backlog、`openspec validate --strict` → archive。

**回滚**：任一波 healthcheck 失败即回滚该仓上一版本；DB 迁移幂等，回滚代码后旧列名已 rename，旧代码读 `group_chat_info` 会 500——故 cloud 阶段 1 回滚需连迁移一起评估（保守：回滚到迁移前备份，或临时把列名 rename 回去）。这是「物理改名」的固有代价，已随 Decision 3 接受。

## Open Questions

- 群评特性的**物理列**（`group_comment_enabled/daily_cap`、`group_comment_attempts` 表族）是否也物理 RENAME（本设计按「连群评一起正名 + 物理改名」默认纳入）；若只想改代码 / UI 面、DB 物理列保留，可在 apply 时缩小该子项。
- 运营机全升级的确认方式（Decision 4 第 4 步的前置）：目前无 per-edge 版本握手，靠运维确认；若需要可作为后续 change 加边缘版本上报。
