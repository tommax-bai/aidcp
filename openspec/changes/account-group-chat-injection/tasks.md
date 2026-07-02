<!-- 回写格式：完成 [ ]→[x] + `<!-- <repo> <sha> 备注 -->`（部署后加 `<!-- <date> deployed -->`）。
     实装前先 openspec list / openspec status 核状态，读本文件定位当前 task。 -->

<!-- 前置阻塞（已解除 2026-07-02）：动手前云端 4 文件曾被 editable-account-group-label + role-thinking-mode-config
     两个未提交 change 交织占用；两者均已提交（role_thinking cloud 3f37324、group-label console b9512a3，cloud
     accountAttr 通道已在 HEAD）。本 change 复用了 group-label 的 accountAttr 通道，未加深交织。三仓工作树落地时均干净。 -->

## 1. aidcp-cloud — 账号存储 `group_chat_info`（复用 accountAttr 单写通道）

- [x] 1.1 `accounts` 表自愈式加列：在账号存储的 `*_SCHEMA_SQL` 加 `ALTER TABLE accounts ADD COLUMN IF NOT EXISTS group_chat_info TEXT`（仿 `nickname`，`init()` 时幂等执行）。验证：全新库与既有库启动均自愈补列、不报错。 <!-- aidcp-cloud a2c8f09 ACCOUNTS_SCHEMA_SQL 加 ALTER（单测断言含该 ALTER） -->
- [x] 1.2 `AccountStore` 接口新增 `setGroupChatInfo(accountId, info): Promise<SetGroupChatInfoResult>` + 导出判别联合 `SetGroupChatInfoResult`（`{ok:true,groupChatInfo}` / `{ok:false,reason:'account_not_found'|'retired_account'}`）。 <!-- aidcp-cloud a2c8f09 -->
- [x] 1.3 `PgAccountStore.setGroupChatInfo` 实现：`UPDATE accounts SET group_chat_info=$2 WHERE account_id=$1 RETURNING group_chat_info`；**verbatim——不 trim、不设长度上限、保留 emoji/换行**（刻意不复用 group-label 的 trim+64 分支）；空/空白/null → 写 NULL（清空）；0 行 → `account_not_found`（不 seed 造行）；拒退役 `default` → `retired_account`（不落库）。 <!-- aidcp-cloud a2c8f09 仅用 trim 判空、非空原样存 -->
- [x] 1.4 读取：加同步读回访问器（供 /comment 任务开始处解析一次；仿 nickname 的内存镜像或直读，二选一，保持与既有账号读一致）。 <!-- aidcp-cloud a2c8f09 采「异步直读 getGroupChatInfo」（低频人工路径可 await PG，无需同步缓存） -->
- [x] 1.5 单测（account-store）：含 emoji/换行/首尾空白的码写后回读**字节一致**（不 trim/不截断）；空 → NULL 清空；不存在 → account_not_found 可区分；`default` → retired_account 且零落库；断言 UPDATE-only（不含 INSERT）。 <!-- aidcp-cloud a2c8f09 account-store.test +7 用例全过（超长不截断 + getGroupChatInfo 直读也覆盖） -->

## 2. aidcp-cloud — 面板 API 写路由（挂到 accountAttr dep）

- [x] 2.1 `PanelDeps`（`panel/types.ts`）的账号属性写依赖 `accountAttr` 新增 `setGroupChatInfo`（复用 group-label 同一 dep 对象，不另起）。 <!-- aidcp-cloud a2c8f09 setGroupChatInfo? 可选挂在既有 accountAttr 上 -->
- [x] 2.2 `panel-server.ts` 新增 `PUT /api/accounts/:id/group-chat-info`：JWT 已覆盖；body `{groupChatInfo}`（''/null/缺省=清空、非 string/null → 400 `invalid_group_chat_info`）；未注入 dep → 503；成功回真态 `{accountId,groupChatInfo}`；not-found → 404；退役 → 400 reason。**不 raw UPDATE、不乐观假成功。** <!-- aidcp-cloud a2c8f09 verbatim：路由不 trim、原样透传给存储 -->
- [x] 2.3 `server.ts` 注入 `accountAttr.setGroupChatInfo`（守卫：仅存储方法存在时注入，否则路由 503）。 <!-- aidcp-cloud a2c8f09 accountStore.setGroupChatInfo 存在时才挂 -->
- [x] 2.4 `PANEL_API_VERSION` 按 /api 形状变更 bump（console 会断言）。 <!-- aidcp-cloud a2c8f09 偏离：**不 bump**——version.ts 只枚举 risk/alert enums（不含 endpoint 列表），console 仅 `panelApiVersion:number` 类型、无硬断言；且 sibling group-label 新增 endpoint 也未 bump。bump 是 cargo-cult、破坏「bump 追 enum 变更」的隐式约定，故不做 -->
- [x] 2.5 单测（panel-server）：未注入→503；成功回真态；verbatim 保真；清空→NULL；not-found→404；`default`→400 退役；坏类型→400；缺 JWT→401。 <!-- aidcp-cloud a2c8f09 panel-server.test +1 全场景用例过（含 verbatim 逐字节断言） -->

## 3. aidcp-console — 录入入口 + 跨账号同码告警

- [x] 3.1 新增账号「关联群聊信息」编辑入口。 <!-- aidcp-console c81bb32 偏离：采**账号表内联多行 TextArea**（autoSize，onBlur 提交、无 onPressEnter 以保多行输入、保存不 trim）而非独立 Modal——最贴合刚落地的 group-label 内联模式、代码最省；长码用 autoSize 展开承载。UX 若嫌挤后续可升 Modal（干净缝） -->
- [x] 3.2 只读表（仪表盘）不接编辑回调 → 保持纯文本、零回归。 <!-- aidcp-console c81bb32 DashboardPage 不传 onEditGroupChat → 该列不渲染，零回归 -->
- [x] 3.3 「同一串群聊码配到多个账号」时给出告警提示。 <!-- aidcp-console c81bb32 codeCounts 检测同码 → 单元格「多账号同码」warning tag -->
- [x] 3.4 前端 DTO 同步（若列表 surface 该字段）。 <!-- aidcp-cloud a2c8f09 + aidcp-console c81bb32 两处手工镜像 PanelAccount.groupChatInfo（cloud panel-store 四点 + console types/api.ts）；编辑器从行 DTO 取当前值，免建独立 GET -->

## 4. aidcp-cloud — `/comment` 引流开关解析

- [x] 4.1 命令解析（`feishu/commands.ts`）：从 `/comment` 参数**尾部**识别 `group:(on|off)`（大小写不敏感），命中即剔除、其余 `join(' ')` 为昵称；trailing-only；产出 `injectGroup` 布尔。更新 `HELP_TEXT` 增 `group:on/off` 用法。 <!-- aidcp-cloud a2c8f09 只认末尾 token、正则 ^group:(on|off)$/i -->
- [x] 4.2 布尔沿链穿透：`CommandActions.comment` 签名 → `runComment` 传参 → `server.ts` actions.comment 实现 → `CommentScheduler.triggerManual` 新增 `injectGroup` 参。 <!-- aidcp-cloud a2c8f09 comment(nickname, {injectGroup}) -->
- [x] 4.3 单测（commands）：`group:on/off` 大小写不敏感=开/关；无 flag=关且昵称完整；含空格昵称+尾部 flag 正确切分；中间出现 `group:on`-样 token 不被误当开关（trailing-only）；昵称字面撞 `group:on` 的长尾。 <!-- aidcp-cloud a2c8f09 feishu-commands.test +9（含 router 透传 injectGroup 断言） -->

## 5. aidcp-cloud — 注入接线 + 缺码 fail-closed

- [x] 5.1 `CommentScheduler` 加 `getGroupChatInfo(accountId)→string|null` 依赖（`server.ts` 构造处接线，读组 1 存储）。 <!-- aidcp-cloud a2c8f09 accountStore.getGroupChatInfo 异步直读 -->
- [x] 5.2 `triggerManual`：`injectGroup=true` 时**任务开始处解析一次**码；缺码（null）→ 早退黄色告警回执、本次不发（fail-closed，镜像 isPersonaBound 闸）；**闸与后续注入用同一个已解析值**（no TOCTOU）。 <!-- aidcp-cloud a2c8f09 解析一次 groupChatCode 带进 runTask -->
- [x] 5.3 注入：把已解析码穿进 `buildComposeAndApprove`（`ComposeApproveDeps` 加 `groupChatCode`），在 `compose-approve.ts` 去 AI 味 + overlapsAny **之后**、`approval.request` **之前** verbatim 追加。码不进 overlap 比对。 <!-- aidcp-cloud a2c8f09 单一 groupChatCode（非空即注入，省去独立 injectGroup 布尔下传） -->
- [x] 5.4 验收测试：需注入+有码 → 人审卡 text 含**完整 verbatim 码**（AC-PUB 审=发）；需注入+无码 → 不静默发、回告警；无 flag → 与今天完全一致（零回归）；码不被去 AI 味改写、不进反照搬；正文长度闸只作用正文。 <!-- aidcp-cloud a2c8f09 compose-approve.test +3 + scheduler.test +4（端到端审=发 + fail-closed + 零回归） -->

## 6. aidcp-edge — 边缘保真（用户拍板：文字逐字输入 + 串码整段粘贴）

<!-- 决策变更 2026-07-02（用户）：不再等真机探针二选一——直接走「正文逐字 + 串码整段插入」。
     故正文（text）与串码（groupChatCode）**分开**下发：正文边缘逐字拟人敲、串码单次 Input.insertText 整段插入，
     绕过 @/# data-tribute 提及/主题补全的逐字触发，从根上消除码被劫持/篡改。实现：cloud 77faef0 + edge d714b9f。 -->

- [x] 6.1 只读真机探针（仿 search-filter-probe）：核实评论框对 ① `#`/`:/#`、② 多行 `\n`、③ 单次整段 `Input.insertText` 的行为。 <!-- aidcp-edge 1385fef scripts/comment-verbatim-probe.ts。用户已直接拍板走整段插入，探针**降级为可选验证**（想复核整段插入在真机的落字仍可跑）；不再是落地前置 -->
- [x] 6.2 采**方案 B·分层送达**：正文 `text` 边缘逐字敲（拟人，保留反检测节奏）；串码 `groupChatCode` 单次 `Input.insertText` 整段插入（绕过逐字补全）。协议 `interaction.comment` 加可选 `groupChatCode`（两份 protocol.ts 逐字一致）；云端正文与码**分开**返回/下发（compose-approve `{text,groupChatCode}`、edge-steps.post 三参、runner/scheduler 透传）；人审卡仍展示合并终稿（审=发）。 <!-- aidcp-cloud 77faef0 + aidcp-edge d714b9f；AC-PROTO 绿、两份 protocol.ts byte-identical、comment-agent 测试 46/46 -->
- [x] 6.3 码送达失败即诚实失败：整段 `Input.insertText` 若 CDP 层抛错 → executeComment 外层 try/catch 兜成 honest-fail（reportActionCompleted ok:false）；发布后校验确认正文前缀出现 + 编辑器清空（评论确已落地）。 <!-- aidcp-edge d714b9f。判断：整段插入比逐字可靠得多，专门比对码尾 DOM 属 YAGNI（码长/含 emoji 会被编辑器视觉变形，比对易假阴），故不加码尾断言；CDP 抛错路径已覆盖诚实失败 -->
- [x] 6.4 回归：无 `groupChatCode` → 边缘行为与今天逐字一致（零回归）；有码 → 正文逐字 + 码整段插入；edge `npm run typecheck` 绿。 <!-- aidcp-edge d714b9f typecheck 通过；executeComment 结构上「无码走原路径」。edge 未加 executeComment 单测（无现成 CDP-mock 夹具）——真机闭环并入 7.5 -->

## 7. 校验 / 回归 / 部署

- [x] 7.1 cloud：`npm run test:acceptance`（AC-* 全过）→ 全量 `npm test` → `npm run typecheck`。确认无协议漂移、人审仍铁红线、风控未被触碰。 <!-- aidcp-cloud a2c8f09 acceptance 27/27、full 1076/1076、typecheck 全绿；无协议/风控改动 -->
- [x] 7.2 console：`tsc --noEmit` + `npm run build` 绿。 <!-- aidcp-console c81bb32 tsc 0 error、build ✓ -->
- [x] 7.3 edge：`npm run typecheck` 绿。 <!-- aidcp-edge 1385fef src typecheck 全绿（仅加脚本、无 src 改动；探针不在 tsconfig include） -->
- [x] 7.4 `openspec validate account-group-chat-injection --strict` 通过。 <!-- aidcp 通过 -->
- [ ] 7.5 手动/端到端：后台粘贴含 emoji/多行码 → 保存 → 刷新持久且原样；清空 → 无码；`/comment <昵称> group:on`（有码）→ 人审卡含完整码 → 发出闭环；`group:on`（无码）→ 告警不发；`/comment <昵称>`（无 flag）→ 普通评论零回归；同码配多账号 → 前端告警。 <!-- 待部署后真机验证；本地不起 cloud（部署铁律） -->
- [ ] 7.6 提交 + 部署：代码已全部提交推送（cloud a2c8f09 存储/面板/命令/注入 + 77faef0 分层送达 / console c81bb32 / edge 1385fef 探针 + d714b9f 分层输入）。边缘保真**已定案**（分层送达，不再 probe-gated）。**新部署前置**：① 云端工作树当前被并发方未提交 WIP 污染（publish/feishu，含 1 处类型错误）——`rsync` 会连带打包他们的半成品，**须待其提交/还原、工作树干净后再部署**，或从干净 checkout 部署；② 标准 e2e（7.5）。文档迁移 `migrations/0027_account_group_chat_info.sql`。序列：cloud 面板层备份→rsync→restart→healthcheck；console 按既有 nginx root（不 --delete）；edge 用户本地 pull/重启；**绝不碰同机 isales**。 <!-- injectGroup 默认 off，未部署时零影响；HEAD 已是干净的、可部署的代码，唯工作树被并发方污染 -->
