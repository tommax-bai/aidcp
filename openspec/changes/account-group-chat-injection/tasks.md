<!-- 回写格式：完成 [ ]→[x] + `<!-- <repo> <sha> 备注 -->`（部署后加 `<!-- <date> deployed -->`）。
     实装前先 openspec list / openspec status 核状态，读本文件定位当前 task。 -->

<!-- 前置阻塞（务必先读）：云端 account-store.ts / panel-server.ts / panel/types.ts / server.ts 现被
     两个未提交 change（editable-account-group-label + role-thinking-mode-config）交织占用，group-label
     已因此卡在提交/部署前。本 change 的 cloud 存储/面板部分复用 group-label 的 accountAttr 通道——
     应在那摊解结、提交后再落，避免加深交织。命令解析（组 4）与部分注入（组 5）在独立文件，可较早并入。 -->

## 1. aidcp-cloud — 账号存储 `group_chat_info`（复用 accountAttr 单写通道）

- [ ] 1.1 `accounts` 表自愈式加列：在账号存储的 `*_SCHEMA_SQL` 加 `ALTER TABLE accounts ADD COLUMN IF NOT EXISTS group_chat_info TEXT`（仿 `nickname`，`init()` 时幂等执行）。验证：全新库与既有库启动均自愈补列、不报错。
- [ ] 1.2 `AccountStore` 接口新增 `setGroupChatInfo(accountId, info): Promise<SetGroupChatInfoResult>` + 导出判别联合 `SetGroupChatInfoResult`（`{ok:true,groupChatInfo}` / `{ok:false,reason:'account_not_found'|'retired_account'}`）。
- [ ] 1.3 `PgAccountStore.setGroupChatInfo` 实现：`UPDATE accounts SET group_chat_info=$2 WHERE account_id=$1 RETURNING group_chat_info`；**verbatim——不 trim、不设长度上限、保留 emoji/换行**（刻意不复用 group-label 的 trim+64 分支）；空/空白/null → 写 NULL（清空）；0 行 → `account_not_found`（不 seed 造行）；拒退役 `default` → `retired_account`（不落库）。
- [ ] 1.4 读取：加同步读回访问器（供 /comment 任务开始处解析一次；仿 nickname 的内存镜像或直读，二选一，保持与既有账号读一致）。
- [ ] 1.5 单测（account-store）：含 emoji/换行/首尾空白的码写后回读**字节一致**（不 trim/不截断）；空 → NULL 清空；不存在 → account_not_found 可区分；`default` → retired_account 且零落库；断言 UPDATE-only（不含 INSERT）。

## 2. aidcp-cloud — 面板 API 写路由（挂到 accountAttr dep）

- [ ] 2.1 `PanelDeps`（`panel/types.ts`）的账号属性写依赖 `accountAttr` 新增 `setGroupChatInfo`（复用 group-label 同一 dep 对象，不另起）。
- [ ] 2.2 `panel-server.ts` 新增 `PUT /api/accounts/:id/group-chat-info`：JWT 已覆盖；body `{groupChatInfo}`（''/null/缺省=清空、非 string/null → 400 `invalid_group_chat_info`）；未注入 dep → 503；成功回真态 `{accountId,groupChatInfo}`；not-found → 404；退役 → 400 reason。**不 raw UPDATE、不乐观假成功。**
- [ ] 2.3 `server.ts` 注入 `accountAttr.setGroupChatInfo`（守卫：仅存储方法存在时注入，否则路由 503）。
- [ ] 2.4 `PANEL_API_VERSION` 按 /api 形状变更 bump（console 会断言）。
- [ ] 2.5 单测（panel-server）：未注入→503；成功回真态；verbatim 保真；清空→NULL；not-found→404；`default`→400 退役；坏类型→400；缺 JWT→401。

## 3. aidcp-console — 录入入口 + 跨账号同码告警

- [ ] 3.1 新增账号「关联群聊信息」编辑入口：因码又长又多行，用长文本 Modal + `Input.TextArea`（autoSize），复用人设页编辑范式；`apiPut('/api/accounts/:id/group-chat-info')`；**非乐观**（成功后 invalidate `['accounts']`）；诚实错误映射；**保存不 trim**（区别于通知联系人页的 draft.trim）。
- [ ] 3.2 只读表（仪表盘）不接编辑回调 → 保持纯文本、零回归。
- [ ] 3.3 「同一串群聊码配到多个账号」时在录入/列表处给出告警提示（跨账号同码=引流指纹，非阻断、仅提醒）。验证：两账号配相同码 → 出现告警；不同码/单账号 → 无告警。
- [ ] 3.4 前端 DTO 若需要在列表surface该字段则同步 `PanelAccount`（console↔cloud 两处手工镜像）；若仅走独立编辑接口取详情则免动列表 DTO——按 3.1 选型定，避免无谓两处镜像。

## 4. aidcp-cloud — `/comment` 引流开关解析

- [ ] 4.1 命令解析（`feishu/commands.ts`）：从 `/comment` 参数**尾部**识别 `group:(on|off)`（大小写不敏感），命中即剔除、其余 `join(' ')` 为昵称；trailing-only；产出 `injectGroup` 布尔。更新 `HELP_TEXT` 增 `group:on/off` 用法。
- [ ] 4.2 布尔沿链穿透：`CommandActions.comment` 签名 → `runComment` 传参 → `server.ts` actions.comment 实现 → `CommentScheduler.triggerManual` 新增 `injectGroup` 参。
- [ ] 4.3 单测（commands）：`group:on/off` 大小写不敏感=开/关；无 flag=关且昵称完整；含空格昵称+尾部 flag 正确切分；中间出现 `group:on`-样 token 不被误当开关（trailing-only）；昵称字面撞 `group:on` 的长尾（诚实 not_found/ambiguous，不回落 default）。

## 5. aidcp-cloud — 注入接线 + 缺码 fail-closed

- [ ] 5.1 `CommentScheduler` 加 `getGroupChatInfo(accountId)→string|null` 依赖（`server.ts` 构造处接线，读组 1 存储）。
- [ ] 5.2 `triggerManual`：`injectGroup=true` 时**任务开始处解析一次**码；缺码（null）→ 早退黄色告警回执「该账号未配置关联群聊信息，请先到后台设置；未注入不代发」、本次不发（fail-closed，镜像 isPersonaBound 闸）；**闸与后续注入用同一个已解析值**（no TOCTOU）。
- [ ] 5.3 注入：把已解析码 + `injectGroup` 穿进 `buildComposeAndApprove`（`ComposeApproveDeps` 加 `groupChatCode`/`injectGroup`），在 `compose-approve.ts` 去 AI 味 + overlapsAny **之后**、`approval.request` **之前** verbatim 追加。码不进 overlap 比对。
- [ ] 5.4 验收测试：需注入+有码 → 人审卡 text 含**完整 verbatim 码**（AC-PUB 审=发）；需注入+无码 → 不静默发、回告警；无 flag → 与今天完全一致（零回归）；码不被去 AI 味改写、不进反照搬；正文长度闸只作用正文、终稿可 >上限（有意）。

## 6. aidcp-edge — 边缘保真（真机探针先行，按结果二选一）

- [ ] 6.1 只读真机探针（仿 `comment-search-command` 的 search-filter-probe）：登录 XHS 停在笔记详情，核实评论框对 ① `#`/`:/#`（用户样例含）是否触发主题/提及补全劫持；② 多行 `\n` 的真实承载行为；③ 单次整段 `Input.insertText` 是否可靠且不触发补全。产物落 `/tmp/aidcp-comment-verbatim-probe-*`。
- [ ] 6.2 据 6.1 结论二选一：**A·云端规整**（首选、纯云端）——在码到达人审卡前校验/规整触发字符（拒或转义 `@`、按探针定换行策略、告知首尾空白会被边缘 trim），使人审文本=边缘可原样敲出的文本；**B·边缘整段插入**——改 `executeComment` 用单次整段 `Input.insertText` 送达码段、绕过逐字/提及路径，拟人节奏留在正文。
- [ ] 6.3 若走 B：发布后校验覆盖到码尾（现只比对前 12 字，正文前缀）——确保码尾被打乱能被 honest-fail 抓到，不谎报成功。
- [ ] 6.4 回归断言：正文仍逐字拟人输入；码段按 6.2 选型送达；任一步空/超时/阻断 honest-fail（no_target/state_unchanged/blocked_by_captcha）。

## 7. 校验 / 回归 / 部署

- [ ] 7.1 cloud：`npm run test:acceptance`（AC-PROTO-*/AC-PUB-*/AC-RISK-* 全过）→ 全量 `npm test` → `npm run typecheck`。确认无协议漂移、人审仍铁红线、风控未被触碰。
- [ ] 7.2 console：`tsc --noEmit` + `npm run build` 绿。
- [ ] 7.3 edge：`npm run typecheck` +（若改 6.2-B）`npm test`/`npm run test:acceptance` 绿。
- [ ] 7.4 `openspec validate account-group-chat-injection --strict` 通过。
- [ ] 7.5 手动/端到端：后台粘贴含 emoji/多行码 → 保存 → 刷新持久且原样；清空 → 无码；`/comment <昵称> group:on`（有码）→ 人审卡含完整码 → 发出闭环；`group:on`（无码）→ 告警不发；`/comment <昵称>`（无 flag）→ 普通评论零回归；同码配多账号 → 前端告警。
- [ ] 7.6 提交 + 部署：**前置**——先解 group-label/thinking 那摊交织并提交、测试通过（安全序列①）。文档迁移用 `migrations/0027_account_group_chat_info.sql`（0026 已被 role_thinking_mode 占）。cloud 面板层按安全序列（备份→rsync→restart→healthcheck），console 按既有 nginx root 发布（不 --delete），edge（若改）用户本地 pull/重启；**绝不碰同机 isales**。
