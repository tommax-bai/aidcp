# publish-pipeline

本阶段为 A 重构收口层：补齐生产触发器、把元数据/配图应用到边缘、接通真实来源血缘、人审默认必过、
元数据防篡改落库，并删除 temp 触发旁路。requirement 名与 stage-1/2/3 的 `publish-pipeline` delta 互不重叠，
归档时依序并入同一 spec。

## ADDED Requirements

### Requirement: PublishScheduler 三扳机触发与授权闸

系统 SHALL 新增 `PublishScheduler`，由三个扳机任一触发 `PublishOrchestrator.trigger()`：① **概念积累**——`ConceptStore`
新概念计数 ≥ 阈值 N；② **风控允许窗口**——`RiskController.getState().status === 'normal'` 且发布配额足；③ **手动飞书 `/publish`**。
自动扳机（① ②）MUST 先过 `riskController.canDo('publish')`，返回 false 时 MUST NOT 触发；手动 `/publish` 可越过 `canDo`
（人工授权），但 MUST NOT 越过发布前飞书人审（AC-PUB）。`PublishScheduler` MUST 复用 server 已持久化的 `RiskController` /
`ConceptStore` 单例，MUST NOT 新建独立实例。同一时刻 MUST NOT 重入触发（`PublishOrchestrator` 已运行时忽略新扳机）。

#### Scenario: 概念积累扳机过 canDo 后触发
- **WHEN** `ConceptStore` 新概念计数达到阈值 N 且 `riskController.canDo('publish')` 返回 true
- **THEN** `PublishScheduler` 调用 `PublishOrchestrator.trigger()` 启动一轮指令驱动发布流水线，使用 server 既有 `RiskController` / `ConceptStore` 单例

#### Scenario: 风控窗口扳机在非 normal 态不触发
- **WHEN** 发布配额足但 `riskController.getState().status` 为 `warned` / `restricted` / `frozen`（或 `canDo('publish')` 为 false）
- **THEN** `PublishScheduler` 的自动扳机 MUST NOT 触发 `trigger()`，等待回到 normal 且配额足

#### Scenario: 手动 /publish 越过 canDo 但仍走人审
- **WHEN** 运营在飞书发 `/publish`，此时 `canDo('publish')` 为 false（如配额已尽）
- **THEN** `PublishScheduler` 接受手动触发（人工授权越过 `canDo`）启动流水线，但 `submit_publish` 前 MUST 仍过飞书人审 `approved === true`，未授权则截止在提交前

#### Scenario: 红线反例——自动扳机绕过 canDo（禁止）
- **WHEN** 有实现让自动扳机（概念积累 / 风控窗口）在 `canDo('publish')` 为 false 时仍触发 `trigger()`，或新建独立 `RiskController` 实例绕过单例真实状态
- **THEN** MUST 视为违规、不予合入；自动扳机 MUST 以共享单例的 `canDo('publish') === true` 为硬前提，仅手动 `/publish` 凭人工授权越过 `canDo`（且仍过人审）

### Requirement: CommandSequencer 将 publishMetadata 编排进指令序列

`CommandSequencer.buildCommandSequence` SHALL 在已授权序列中，依据 `publishMetadata` 追加并下发元数据指令：从 `publishMetadata`
emit `add_with_candidate`（`mention` / `location` / `collection`）/ `set_option`（`visibility` / `permissions` / 各合规声明）/
`set_schedule`（`mode === 'scheduled'` 时按 `publishTime`）。`PublishExecutor` MUST 读取 `publishMetadata` 并传入 sequencer；
读取 MUST 有竞态保险（`publishMetadata` 未就绪时取保守默认而非崩溃 / 跳过人审）。任一元数据指令失败 MUST 如实记录失败步，
MUST NOT 伪造该步成功。未授权时（AC-PUB 第二闸）元数据指令仍 MAY 在 `submit_publish` 前下发、但 `submit_publish` /
`capture_postId` 截止不入序列。

配图上传与 `upload_image` / `set_cover` 的最终语义不归本 requirement 收口；其已由后续并已归档的 `publish-media-upload`
专门定义和实现（包括 CDP 文件输入桥、全图失败诚实 failed、`imagesOk`/落库回正、v1 带图显式改道），本 requirement MUST NOT
重新定义或削弱该能力。

#### Scenario: 已授权序列携带元数据指令
- **WHEN** 人审通过、`publishMetadata` 含 `mentions` / `location` / `visibility` / `mode==='scheduled'`
- **THEN** `buildCommandSequence` 产出含 `add_with_candidate(mention|location)` / `set_option(visibility)` / `set_schedule` 的有序序列，`PublishExecutor` 读 `publishMetadata` 传入 sequencer 后逐条 `send→await→advance`

#### Scenario: publishMetadata 未就绪时竞态保险
- **WHEN** `PublishExecutor` 读取 `publishMetadata` 时该键尚未就绪（决策与门禁并行、无强序）
- **THEN** executor MUST 取保守默认（如可见范围 `self_only`、不发元数据指令）继续，MUST NOT 崩溃、MUST NOT 因缺元数据而跳过 AC-PUB 人审或伪造发布成功

#### Scenario: 红线反例——元数据指令失败仍报成功（禁止）
- **WHEN** `set_option(visibility)` 或 `add_with_candidate(mention)` 回报 `ok:false`，但程序把整帖标记为成功 / 跳过该失败继续直发
- **THEN** MUST 视为违规、不予合入；失败步 MUST 如实记入 `failedAt`，元数据失败不得静默吞，绝不伪造该步成功

### Requirement: 边缘实装元数据 kind 处理器并逐条后置校验

边缘 SHALL 实装 stage-1 预留的元数据处理器：`set_option`（按 `optionKind` 路由 `visibility` / `permissions` / 各声明开关/单选）、
`set_schedule`（定位时间选择器填 `publishTime`），并支持 `add_with_candidate` 的 `mention` / `location` / `collection` 候选应用路径。
每个处理器 MUST 复用既有定位与后置校验机制做「定位 + 原子操作 + 后置校验」，MUST 在执行后按真实结果回报
`publish.command.result`（成功 `ok:true` + `value`，失败 `ok:false` + 真实 `error` 如 `no_target` / `post_validation_failed`）。
MUST NOT 谎报成功、MUST NOT 在无法定位时回 `ok:true`。

配图处理器 `upload_image` / `set_cover` 与 v1 带图改道由 `publish-media-upload` capability 负责，本 requirement 不重复定义。

#### Scenario: set_option 按 optionKind 路由并校验
- **WHEN** 边缘收到 `set_option {optionKind:'visibility', optionValue:'self_only'}`
- **THEN** 处理器经 `LocatingEngine` 定位对应开关/单选、设置后后置校验当前选中态等于期望值，回报 `ok:true`；校验不符回 `ok:false, error:'post_validation_failed'`

#### Scenario: set_schedule 定时时间后置校验
- **WHEN** 边缘收到 `set_schedule {publishTime}`
- **THEN** 处理器定位时间选择器并设置时间，设置后后置校验已进入期望定时态；定位或校验失败回 `ok:false`

#### Scenario: 红线反例——元数据控件失败谎报成功（禁止）
- **WHEN** 元数据控件定位失败或后置校验不符，但处理器回 `ok:true`
- **THEN** MUST 视为违规、不予合入；MUST 回 `ok:false` + 真实 `error`，绝不静默假成功

### Requirement: 人审默认必过且 submit_publish 前强制授权

边缘审批闸 SHALL 默认开启：触发条件由 `AIDCP_REAL_PUBLISH === 'true'` 改为 `!== 'false'`——仅当显式 `AIDCP_REAL_PUBLISH=false`
才跳过人审，缺省 / 任何其它值一律挂闸。`submit_publish` 指令 MUST 在 `approved === true`（严格相等，复用既有审批信号文件机制、
路径契约 `/tmp/aidcp-publish-approve-<requestId>.json` 两端一致）后才下发；信号缺失 / 解析失败 / `approved !== true` 时 MUST 截止在提交前。
手动 `/publish` 越过 `canDo` 后 MUST 仍过此人审闸。MUST NOT 把缺省 / 异常当放行。

#### Scenario: 缺省即挂人审闸
- **WHEN** 未设置 `AIDCP_REAL_PUBLISH`（或设为非 `false` 的任意值）
- **THEN** 边缘审批闸开启，`submit_publish` 前 MUST 等到 `approved === true` 才放行，缺省即「未授权 == 不发布」

#### Scenario: 仅显式 false 才跳过人审
- **WHEN** 显式设置 `AIDCP_REAL_PUBLISH=false`
- **THEN** 人审闸跳过（仅供受控测试），其余任何取值 / 缺省均不跳过

#### Scenario: 手动 /publish 越权后仍过人审
- **WHEN** 手动 `/publish` 已越过 `canDo('publish')` 启动流水线
- **THEN** 到 `submit_publish` 前 MUST 仍读审批信号、严格 `approved === true` 才下发提交，未授权则截止在提交前

#### Scenario: 红线反例——缺省直发（禁止）
- **WHEN** 有实现把人审闸缺省关闭（保留 `=== 'true'` 才挂），或把信号缺失 / 异常当作放行下发了 `submit_publish`
- **THEN** MUST 视为违规、不予合入；缺省 MUST 挂闸（`!== 'false'`），缺失 / 异常一律按未授权处理，严格相等 + 提交前截止保证未明确授权绝不发布

### Requirement: LikedNoteStore 接通真实来源血缘

系统 SHALL 新增 `LikedNoteStore`（`liked_notes` 表），在真实 `like` 互动完成时把被赞内容来源落库；发布记录的来源血缘 MUST 用真实值——
`sourceConcepts` 取真实概念、`sourceLikedIds` 由 `LikedNoteStore.listSince()`（或等价时间窗回取）取真实点赞 id。`publish_log.source_liked_ids`
MUST NOT 再写死 `[]`。无真实点赞来源时 MUST 如实写空数组，MUST NOT 编造 id 凑数。

#### Scenario: 真实 like 完成落库
- **WHEN** 边缘真实完成一次 `like` 并经事件回到云端
- **THEN** `LikedNoteStore` 向 `liked_notes` 插入一条被赞内容来源记录（含可回取的来源 id），供后续发布血缘回取

#### Scenario: 发布记录回取真实点赞血缘
- **WHEN** `PublishExecutor` 落库一条发布记录
- **THEN** `source_liked_ids` 由 `LikedNoteStore.listSince()` 回取的真实点赞 id 填充、`source_concepts` 为真实概念，二者均非写死值

#### Scenario: 无来源时如实空数组
- **WHEN** 时间窗内无真实点赞来源
- **THEN** `source_liked_ids` 如实写 `[]`，MUST NOT 编造或复用历史 id 凑数

#### Scenario: 红线反例——血缘写死或编造（禁止）
- **WHEN** 有实现保留 `sourceLikedIds: []` 写死、或在无真实来源时填入伪造 id
- **THEN** MUST 视为违规、不予合入；血缘 MUST 来自 `LikedNoteStore` 真实落库的点赞记录，缺则如实空

### Requirement: publishMetadata 防篡改落库

系统 SHALL 把 `publishMetadata` 随发布记录落库：`publish_log` 新增 `publish_metadata JSONB` 与 `ai_enforced BOOLEAN` 列；
`PublishExecutor` 落库时写入 `publishMetadata` 与 `ai_enforced`。落库前若检出 `aiEnforced && !ai` 的篡改态，MUST 拒绝该降级
（保持 `ai = true`）、记审计日志，MUST NOT 静默落库为 `ai = false`（对齐 stage-3 合规红线）。落库 MUST NOT 改变是否发布 / 走哪条路径 /
授权判定——它是发布结果的如实持久化。

#### Scenario: 元数据随记录落库
- **WHEN** 一轮发布完成、`PublishExecutor` 写 `publish_log`
- **THEN** 同一行写入 `publish_metadata`（JSONB，含各维度选择 + `compliance` + `metadataScore`）与 `ai_enforced`，可供审计回查

#### Scenario: aiEnforced 篡改态被拒绝降级
- **WHEN** 落库前检出 `publishMetadata.compliance.aiEnforced === true` 但 `ai === false`
- **THEN** MUST 拒绝该降级、强制持久化 `ai = true`，记一条审计日志，MUST NOT 写入 `ai = false`

#### Scenario: 落库不改发布行为
- **WHEN** 开启 `publishMetadata` 落库
- **THEN** 是否发布、走指令驱动 / 旧整页、AC-PUB 授权判定均与未落库时完全一致，落库仅为如实持久化

#### Scenario: 红线反例——静默落库篡改的 ai=false（禁止）
- **WHEN** 有实现对 `aiEnforced && !ai` 的态不拒绝、直接落库 `ai=false`，或为发帖通过率人为抹掉 `ai_enforced`
- **THEN** MUST 视为违规、不予合入；强制声明一经 `aiEnforced` 置位即不可降级，落库点 MUST 拒绝并审计

### Requirement: 删除 temp 触发旁路后无绕过指令驱动与 AC-PUB 的入口

系统 SHALL 删除两个 temp 触发旁路：`server.ts` 的 `/debug/publish` HTTP 端口与 CLI `trigger:publish-temp`
（整个 `src/cli/trigger-publish-temp.ts` 及 `package.json` 对应脚本）。删除后正式触发 MUST 仅经飞书 `/publish` →
`PublishScheduler` → `PublishOrchestrator.trigger()` 走指令驱动路径，并受 AC-PUB 人审约束。删除后 MUST NOT 残留任何
绕过指令驱动（直接发 `publish.request` 整页）或绕过 AC-PUB 人审的发布入口。

#### Scenario: temp 入口删除
- **WHEN** 检视代码库
- **THEN** `/debug/publish` 端口与 `trigger:publish-temp` CLI / `src/cli/trigger-publish-temp.ts` 均已删除，`package.json` 无对应脚本

#### Scenario: 正式触发走指令驱动
- **WHEN** 运营发飞书 `/publish`
- **THEN** 触发经 `PublishScheduler` 调 `PublishOrchestrator.trigger()` 走指令驱动 + AC-PUB 人审，而非旧 `publish.request` 整页路径

#### Scenario: 无残留绕过入口
- **WHEN** 全仓搜索发布触发入口
- **THEN** 除飞书 `/publish` 经 `PublishScheduler` 的路径外，MUST NOT 存在任何直接构造 `publish.request` 并下发、或绕过 AC-PUB 人审的发布入口

#### Scenario: 红线反例——保留 temp 旁路（禁止）
- **WHEN** 有实现以「方便调试」为由保留 `/debug/publish` 或 `trigger:publish-temp`，使其可绕过 `PublishScheduler` / 指令驱动 / AC-PUB 直发
- **THEN** MUST 视为违规、不予合入；调试需求 MUST 经 `AIDCP_REAL_PUBLISH=false` 受控关闭人审，而非保留可绕过授权链的独立触发口
