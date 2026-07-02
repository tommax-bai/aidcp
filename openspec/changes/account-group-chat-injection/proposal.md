## Why

运营希望把小红书评论当引流入口：在后台给每个账号存一份「关联群聊引流码」（长按复制式邀请码，含 emoji、多行），再在飞书 `/comment <昵称>` 命令里按需把这串码接到生成的评论末尾，把看到评论的人导进群聊。今天系统里既没有「每账号一份群聊码」的存储 / 录入入口，`/comment` 也只认昵称、没有引流开关，撰写链更是明令禁 @ / 外链、逐字敲进带 @提及的评论框——直接塞码会被改写、被补全劫持、或人审看到的与真发出去的不一致。需要一条从后台录入到命令注入的完整、诚实、可控的通路。

## What Changes

- **【新·每账号群聊码】** 给账号增加一份可在后台粘贴录入的「关联群聊信息」自由文本，**原样存储**（不 trim、不设长度上限、保留 emoji 与换行；与会 trim+64 截断的分组标签相反）。复用正在进行的 `editable-account-group-label` 引入的「账号属性单写通道」，做成其孪生字段（账号存储单写方法 + 面板受 JWT 保护的 PUT + 前端编辑入口），**不另起旁挂表 / 独立页面**。
- **【新·命令引流开关】** `/comment <昵称> group:on` 逐次开启引流；`group:off` 显式关闭；**不带开关 = 今天的普通评论、零回归**。尾部开关解析（大小写不敏感），其余 token 仍当昵称。逐次 opt-in，不做「配了码就每条自动注入」。
- **【新·注入与人审对齐】** 命中开关时，把该账号的群聊码在「去 AI 味 + 反照搬之后、飞书人审卡之前」verbatim 追加到评论——保证人审看到的就是含码完整终稿（`审的就是发的`），且码不被前面的改写步骤吃掉、不进反照搬比对。
- **【新·缺码兜底 fail-closed】** `group:on` 但该账号未配群聊码 → 飞书回黄色告警卡「该账号未配置关联群聊信息」、本次不发；**绝不静默降级成无码评论**（形态镜像现有「未绑人设」闸）。
- **【新·边缘保真闸】** 坐实并解决「审=发」在边缘的真实约束：边缘发评论会 `trim` 首尾空白、逐字符敲进 data-tribute @提及编辑器（emoji 安全、`@`/可能的 `#` 会触发补全劫持后续输入），发布后校验只比对前 12 字。方案二选一：到达人审卡前对码做校验 / 规整（拒或转义 `@`、定并强制换行策略），或改边缘为单次整段插入绕过逐字 / 提及路径；并补一条真机探针核实 `#` / 换行 / 整段插入行为。
- **【仅命令式路径】** 只做飞书 `/comment` 命令式引流；**坚决不接线自治浏览闭环的评论注入点**（浏览闭环永不自动引流——同码高频=最强封号指纹）。
- **【范围裁剪·YAGNI】** 每账号**单份**群聊码（不做多群列表，留干净扩展缝）；**不做**按账号每日引流频次上限（净新增、留缝，靠逐次 opt-in + 人审兜底）；控制台仅做「同码配到多个账号」的轻量告警。

> 非 BREAKING：字段、命令开关、注入均为新增；不带 `group:on` 时 `/comment` 行为一字不变。

## Capabilities

### New Capabilities
- `group-chat-injection`: 每账号「关联群聊引流码」的原样存储与读取契约；`/comment` 的 `group:on/off` 逐次 opt-in 引流开关；命中开关时在人审卡前 verbatim 注入并保证「审=发」；缺码 fail-closed；边缘保真（trim / @提及补全 / 前 12 字校验的真实约束与其处置）；仅命令式、不接自治浏览闭环；跨账号同码告警与「无频次上限」的已知缺口声明。

### Modified Capabilities
- `console-write-operations`: 新增一条 Requirement——账号「关联群聊信息」（`group_chat_info`）经账号存储的一等单写方法编辑，面板层受 JWT 保护、绝不 raw UPDATE、绝不乐观假成功、写后回读真态、拒绝（退役账号 / 坏类型）与成功可区分；**空输入归 NULL（清空）**；且**存储 verbatim**（不 trim、不截断），与既有分组标签写入的 trim+64 截断刻意相反。这与该 spec「写只经拥有者对象、诚实非乐观」的核心不变量同构。

## Impact

- **aidcp-cloud**：`src/account-store.ts`（`accounts` 表自愈式加列 `group_chat_info TEXT` + `AccountStore` 接口与 `PgAccountStore` 加孪生单写 `setGroupChatInfo`，**不 trim / 不截断**）；`src/panel/panel-server.ts` + `src/panel/types.ts`（`PUT /api/accounts/:id/group-chat-info` 挂到 `accountAttr` dep）；`src/server.ts`（注入 dep + `CommentScheduler` 构造处加 `getGroupChatInfo` 解析器）；`src/feishu/commands.ts`（`/comment` 尾部 `group:on/off` 解析 + `HELP_TEXT`）；`src/comment-agent/comment-scheduler.ts`（`triggerManual` 加 `injectGroup`、任务开始处解析一次码、缺码 fail-closed 闸）；`src/comment-agent/compose-approve.ts`（人审前 verbatim 追加）。文档迁移 `migrations/0027_account_group_chat_info.sql`（**0026 已被 role_thinking_mode 占用**）。
- **aidcp-console**：账号录入入口（长文本 Modal + `Input.TextArea`，非乐观、诚实错误、保存不 trim）；「同码配到多个账号」告警。
- **aidcp-edge**：真机探针核实评论框对 `#` / 换行 / 整段插入的行为；若采「整段插入」方案则改 `executeComment` 的输入方式（否则不动边缘）。
- **不触及**：边-云 WebSocket 协议 v2（走既有 `interaction.comment` 信封，仅 text 变长，不动 `command-bridge` / edge-client 白名单）；`RiskController` 最终状态单写（命令式 `/comment` 本就跳过风控配额，保留去重 + 人审）；dispatcher 角色注册数（无新增角色）；同机 isales。
- **协同风险**：云端 `account-store.ts` / `panel-server.ts` / `panel/types.ts` / `server.ts` 现被两个未提交 change（`editable-account-group-label` + `role-thinking-mode-config`）交织占用，group-label 已因此卡在提交 / 部署前。本 change 的 cloud 代码应**复用 group-label 的 `accountAttr` 通道**，并在那摊解结、提交后再落，避免加深交织。
