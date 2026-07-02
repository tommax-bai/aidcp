## Context

`/comment <昵称>` 命令（change `comment-search-command`，尚未归档）已能：按昵称定位账号 → 暂结自动浏览独占边端 → 生成搜索词 → 甄选强相关高收藏笔记 → 撰写 → 去 AI 味 → 飞书人审 → 边端发评论。撰写链两条路径共用同一批零件：事件驱动浏览闭环（`comment-composer` → `comment-de-ai-flavor` → `comment-approval-gate`）与命令式（`compose-approve.ts` 串起同样三步）。命令式路径**跳过**风控按天配额与 `canDo('comment')`，只保留「每笔记去重 + 飞书人审」两道闸。

账号侧：`accounts` 主表列由各 store 的 `*_SCHEMA_SQL` 常量在 `init()` 时自愈式建 / 补（本仓**无迁移执行器**，`migrations/*.sql` 仅人审文档）。今天**没有**任何运营可编辑的每账号自由文本字段可复用：`nickname` 平台派生、拒空、64 截断；`label` 恒等 account_id 无编辑口；`group_label` / `machine_label` 有列无写者（恒 NULL）；`persona_ref` 死列。并行 change `editable-account-group-label`（14/16，未提交）正在把 `group_label` 接通成可编辑——它引入的「账号属性单写通道」（账号存储 `setGroupLabel` + 面板 `PUT /api/accounts/:id/group-label` + `PanelDeps.accountAttr`）正是本 change 该复用的模板。

边缘发评论（`aidcp-edge` `browse-session.ts` `executeComment`）：`const body=(text??'').trim()` → 逐字符 `Input.insertText` 敲进 `p#content-textarea`（contenteditable + data-tribute `@`提及编辑器）→ 提交 → 发布后校验只比对 `body.slice(0,12)`。云端撰写链本就有一步 `sanitize` 专剥裸 `@`（正因这个编辑器见 `@` 弹补全）。

约束：无迁移器（DDL 必幂等）；退役保留账号 `default` 全写路径拒；协议 v2 两份 `protocol.ts` 逐字一致；风控最终态由 `RiskController` 单写；MUST NOT 静默假成功；发布 / 评论人审是 AC-PUB 铁红线（未接线 / 超时 / 拒绝一律不发）。

## Goals / Non-Goals

**Goals:**
- 每账号一份**原样存储**的「关联群聊引流码」，后台可粘贴录入 / 清空，读写诚实非乐观。
- `/comment <昵称> group:on` 逐次开启引流、`group:off` 关闭、无开关=零回归。
- 命中开关时把码在**人审卡之前** verbatim 接入评论，保证「审的就是发的」。
- 缺码 fail-closed（黄色告警、本次不发）。
- 坐实并解决「审=发」在边缘的真实约束（trim / `@`提及补全 / 前 12 字校验）。

**Non-Goals:**
- 不做自治浏览闭环的自动引流注入（永不）。
- 不做每账号多群聊码列表（单份，留缝）。
- 不做每账号引流频次上限（留缝，靠 opt-in + 人审）。
- 不动协议 v2、不写 `RiskController`、不加 dispatcher 角色。

## Decisions

### D1. 存储：`accounts` 加一列 + 复用 `accountAttr` 单写通道（不另起旁挂表 / 独立页面）

在 `accounts` 表自愈式加 `group_chat_info TEXT`（`ALTER TABLE ... ADD COLUMN IF NOT EXISTS`，仿 `nickname`），账号存储加孪生单写 `setGroupChatInfo`，面板加 `PUT /api/accounts/:id/group-chat-info` 挂到 `editable-account-group-label` 引入的 `accountAttr` dep，前端复用其编辑范式。

- **为何**：`/comment` 能用引流的账号集合 == 能编辑该字段的账号集合 == 已有账号表；`editable-account-group-label` 正把「每账号可编辑属性」的单写通道打通。复用它 = 一个字段端到端，避免造平行的「新表 + facade + 3 路由 + 独立页面」栈（初版探索设计的过度设计）。
- **Alternatives**：① 旁挂表 `account_group_chat`（克隆 `persona_config`）——多一张表、一套 facade、一条独立目录页，为存一个可选字段不值当，否决。② 塞进 persona YAML（`Soul` 新字段）——群聊码是运营频改的联系方式、不是人设语义，且要走 YAML 校验 / 解析，语义错配，否决。
- **关键差异**：`group_label` 写入 `trim` + 64 截断；本字段必须 **verbatim**（不 trim、不设长度上限、保留 emoji 与换行）——单写方法要为本字段独立、不复用 group-label 的 trim/cap 分支。空输入归 NULL（清空），对齐既有清空语义。

### D2. 命令语法：`/comment <昵称> group:on`（尾部布尔开关，冒号哨兵）

- **为何 `group:on` 不用 `group:1`**：数据模型是每账号**单份**码，无「第 1/第 2 个群」的索引，`1` 无所指、只能当布尔——那就用自解释的 `on`。冒号哨兵（`group:on`）几乎不撞真实昵称（昵称可含空格，裸词 `group` 会与「昵称叫 group」相撞）。
- **解析**：尾部识别 `group:(on|off)`（大小写不敏感），命中即从 token 流剔除、其余 `join(' ')` 为昵称；**trailing-only**（只认末尾开关），避免把中间某 token 误当开关而错切昵称。无开关 → `injectGroup=false` → 与今天完全一致。
- **Alternatives**：裸词 `group`（撞昵称，否决）；前置 flag `/comment group:on 昵称`（与「/comment 之后整段=昵称」的 publish 同构约定相悖、易吃昵称首词，否决）；码直接进命令（多行 emoji 无法单行承载，否决）。

### D3. 注入点：`compose-approve.ts` 人审卡前 verbatim 追加（命令式路径唯一）

在去 AI 味（PostProcessor）与反照搬（overlapsAny）**之后**、`approval.request` **之前** verbatim 追加群聊码。三重正确性：① 追加在去 AI 味之后 → 不被重写吞掉；② 追加在人审卡之前 → 运营在飞书审到的就是含码完整终稿（AC-PUB「审=发」）；③ overlapsAny 只跑正文 → 码不进反照搬比对。

- **为何不 prompt 内嵌**：LLM 内嵌脆——下游去 AI 味会改写、`sanitize` 剥 `@`，且违反 composer prompt 自己「不要外链 / @」的反检测规矩。只能确定性追加。
- **为何不发送后追加**：人审就失去意义（审的与发的不同），破 AC-PUB。
- **依赖穿线**：任务开始处 `getGroupChatInfo(accountId)` **解析一次**，缺码闸与注入用**同一个已解析值**（避免 gate 与 append 之间二次读产生 TOCTOU / 漂移）。经 `CommentScheduler.triggerManual(injectGroup)` → `runTask` → `buildComposeAndApprove`（`ComposeApproveDeps` 加 `groupChatCode`/`injectGroup`）。
- **长度闸**：`MAX_COMMENT_LEN=50` 跑在 `composeDraft` 内对**正文草稿**、在追加之前 → 终稿=（≤50 正文）+ 码，会 >50，**有意**（码本身长），文档明写非 bug。`sanitize` 剥 `@` 亦在正文阶段、在追加前 → 码里的 `@`/链接得以保留（引流所需）。

### D4. 缺码 fail-closed（镜像 isPersonaBound 闸）

`group:on` 但 `getGroupChatInfo` 返 null → 在 `triggerManual` 早退一张黄色告警回执「该账号未配置关联群聊信息，请先到后台设置；未注入不代发」，本次不发。绝不静默降级成无码普通评论。形态镜像 `comment-scheduler.ts` 现有「未绑人设」闸。

### D5. 边缘保真：先「云端约束码空间」，再按真机结果决定是否改边缘输入方式

「审=发」的真实威胁在边缘，不在云端 JSON（UTF-8 天然保 emoji、React 文本节点无 sanitize）。已核实边缘：`trim` 首尾空白；逐字符敲入 data-tribute `@`提及编辑器（`@`、可能 `#` 触发补全劫持后续键入）；`Array.from` 按码点切分 → **emoji 安全**（代理对 / ZWJ 不裂）；发布后只比对前 12 字。

- **首选（低风险、纯云端）**：在**码到达人审卡之前**校验 / 规整——拒绝或转义会触发编辑器补全的字符（确证 `@`；`#` 待真机核）、定并强制换行策略（单行，或把换行规整为可被逐字输入安全承载的形式）、告知运营码首尾空白会被边缘 `trim`。这样人审看到的 = 规整后的码 = 边缘能原样敲出的码。
- **备选（更强、需改边缘）**：改 `executeComment` 用**单次整段 `Input.insertText`** 注入码段（绕过逐字节奏 + 提及路径），拟人节奏只保留在正文。
- **决策依赖真机探针**：仿 `comment-search-command` 的 `search-filter-probe` 做一条只读探针，核实 `#` 是否触发主题补全、多行 `\n` 在真编辑器的行为、整段 `insertText` 是否可靠且不触发补全。据结果二选一。**在探针出结论前，本 change 的边缘部分不落**（云端存储 + 录入 + 命令解析 + 注入可先行，注入先走「首选·云端规整」的保守规整）。

## Risks / Trade-offs

- **[平台引流检测 / 封号]** 同一串码被一批账号短时反复发 = 协同 spam 强指纹；命令式 `/comment` 无风控限频、唯一刹车是人审 → **Mitigation**：逐次 opt-in（频率运营逐条掌控）+ 强制人审 + 只做命令式不接浏览闭环 + 控制台「同码配到多个账号」告警。频次上限留缝（净新增），本轮不做，设计里点明为已知缺口。
- **[审=发 被边缘悄悄破坏]** 边缘 `trim` + `@`/`#` 补全会让「发出去的」偏离「人审通过的」→ **Mitigation**：D5 云端先规整码空间；真机探针核实后按需改边缘整段插入；发布后校验对前 12 字（正文前缀）仍诚实报「行出现」，但码尾被打乱不一定抓到——探针阶段一并核实并在必要时把校验覆盖到码尾。
- **[与并行 WIP 交织加深]** 云端 4 文件已被两个未提交 change 占用、group-label 已卡 → **Mitigation**：复用 group-label 的 `accountAttr` 通道（在同一 dep 对象上加一个孪生方法，而非另起）；cloud 代码在那摊解结、提交后再落；迁移文档用 0027（0026 已占）。
- **[verbatim 与既有 trim/cap 惯例相反]** 复用通道但故意不 trim/不 cap，易被后来者「顺手统一」→ **Mitigation**：单写方法为本字段独立分支 + 注释 + 单测锚定（emoji / 换行 / 首尾空白原样回读）。

## Migration Plan

- **DDL**：`group_chat_info TEXT` 经账号存储 `init()` 的幂等 `ADD COLUMN IF NOT EXISTS` 自愈补列；伴随人审文档 `migrations/0027_account_group_chat_info.sql`。无数据回填（新列默认 NULL = 无码）。
- **回滚**：字段与命令开关均为纯新增、`injectGroup` 默认 false，回滚 = 撤代码即回到今天行为；列可留空不删（幂等、无副作用）。
- **部署序列**：cloud 面板层按安全序列（备份 → rsync → restart → healthcheck）；console 构建产物按既有 nginx root 发布（不 `--delete`）；edge 部分（若采整段插入）用户本地 `git pull` 重启 / 重打包。**前置**：group-label / thinking 那摊解结、提交、测试通过。

## Open Questions

- 追加格式：正文与码之间用裸换行，还是加一句引导语（如「感兴趣的姐妹可看这个群」）？引导语更自然但更像模板、更易被识别为营销——影响自然度与被检测概率。（默认：先裸换行 + 码，引导语作为后续可配项留缝。）
- `#`（用户样例码含 `#`、`:/#`）是否触发真编辑器主题补全 → 真机探针定，决定 D5 走「云端规整」还是「边缘整段插入」。
- 多行码是否需要保留换行（影响可读性与边缘输入）→ 探针核实换行在真编辑器行为后定单行 / 多行策略。
