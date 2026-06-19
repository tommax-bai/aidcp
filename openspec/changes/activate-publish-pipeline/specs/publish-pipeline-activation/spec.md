# publish-pipeline-activation

## ADDED Requirements

### Requirement: 三扳机触发与 canDo('publish') 闸

系统 SHALL 提供 `PublishScheduler`，在三个扳机任一满足时调用 `PublishOrchestrator.trigger()`：① 概念积累阈值（`ConceptStore` 的新概念计数 `newConceptCount ≥ N`）；② 风控允许窗口（`RiskController.getState().status === 'normal'` 且发布配额足）；③ 手动飞书 `/publish` 命令。两个自动扳机（① 与 ②）MUST 在触发前通过 `riskController.canDo('publish')`；当 `canDo` 返回 false 时，自动扳机 MUST NOT 触发发布、MUST NOT 静默吞掉，而是如实记录被拒原因。手动 `/publish` MAY 越过 `canDo`（人工授权），但越权后产生的任何真机发布仍 MUST 经发布前飞书人审（见「人审默认必过」需求）。`PublishScheduler` MUST 复用 `server.ts` 已持久化的 `RiskController` 单例，MUST NOT 新建第二个实例。

#### Scenario: 概念积累扳机在风控允许时触发

- **WHEN** `ConceptStore` 的 `newConceptCount` 达到阈值 N，且 `riskController.canDo('publish')` 返回 true
- **THEN** `PublishScheduler` 调用 `PublishOrchestrator.trigger()` 启动一次发帖链路，触发输入携带真实概念来源

#### Scenario: 风控不允许时自动扳机被拒且不静默

- **WHEN** 概念积累或风控窗口扳机满足条件，但 `riskController.canDo('publish')` 返回 false（如账号 `warned`/`restricted`/`frozen`）
- **THEN** `PublishScheduler` MUST NOT 调用 `trigger()`，MUST 如实记录该次被拒（含原因），且 MUST NOT 改写风控最终状态

#### Scenario: 手动 /publish 越过 canDo 但保留人审

- **WHEN** 运营在飞书发送 `/publish` 命令，而此时 `riskController.canDo('publish')` 返回 false
- **THEN** `PublishScheduler` 仍调用 `trigger()`（人工授权越过 `canDo`），但后续真机发布仍进入发布前飞书人审，未获 `approved=true` 不发布

#### Scenario: 不复用既有单例属反例

- **WHEN** 任何触发路径在 `PublishScheduler` 内部 `new RiskController()` 另起一个风控实例做闸
- **THEN** 该实现 MUST 被判定为违规（破坏「风控状态单写 / 单例」契约），实现 MUST 改为复用 `server.ts` 注入的同一 `RiskController` 单例

### Requirement: 配图 images[] 端到端与取不到图降级纯文字如实标注

发帖配图 SHALL 端到端打通：协议 `PublishRequestPayload` 以数组 `images?: string[]` 承载配图 URL（取代旧单数 `imageUrl`），`ImageDirective.imageUrl` MUST 映射为 `images: [url]`。edge 接到带图请求时 MUST NOT 直接硬拒，MUST 走「图片 URL → 下载 → 上传」桥真实附图。当图片获取或上传失败时，系统 MUST 降级为纯文字发布，并 MUST 在 `publish.result.imagesOk` 字段中如实标注图片未成功（`imagesOk=false`），MUST NOT 谎报附图成功，也 MUST NOT 因图片失败而把整次发布伪造成 `ok:true` 的带图成功。

#### Scenario: 带图请求端到端附图

- **WHEN** cloud 下发的 `publish.request` 携带 `images: ["https://cdn/x.jpg"]`，且 edge 成功下载并上传该图
- **THEN** edge 真机发布带图帖子，并在回传的 `publish.result` 中标注 `imagesOk: true`

#### Scenario: 取不到图降级纯文字并如实标注

- **WHEN** `publish.request` 携带 `images`，但 edge 下载或上传图片失败
- **THEN** edge 降级为纯文字发布，并在 `publish.result` 中标注 `imagesOk: false`，如实反映图片未附上

#### Scenario: edge 不再对带图请求硬拒

- **WHEN** edge 收到任意携带 `images` 的 `publish.request`
- **THEN** edge MUST NOT 直接返回 `ok:false` 硬拒，MUST 进入图片下载上传桥尝试附图（成功附图 / 失败降级纯文字）

#### Scenario: 图片失败却谎报带图成功属反例

- **WHEN** 图片上传失败，但 edge 回传 `publish.result` 标 `imagesOk: true` 或在纯文字发布时谎称附图成功
- **THEN** 该行为 MUST 被判定为「静默假成功」违规，实现 MUST 改为按真实结果如实标注 `imagesOk`

### Requirement: 人审默认必过，approved!=true 绝不发布

任何真机发布 MUST 经发布前飞书人审，且 MUST 仅在审批信号 `approved === true` 时才点发布（守护 `AC-PUB` 红线：未授权绝不静默发布）。edge 人审挂载条件 SHALL 从旧的 `AIDCP_REAL_PUBLISH === 'true'` 改为 `AIDCP_REAL_PUBLISH !== 'false'`——即缺省、未设、或任何非 `'false'` 取值都 MUST 启用人审；仅显式 `AIDCP_REAL_PUBLISH=false`（本地开发）才 MAY 跳过人审。当审批 `approved !== true`（拒绝、超时、信号缺失）时，系统 MUST NOT 点发布，MUST 返回审批未通过的失败结果。

#### Scenario: 未设环境变量时人审默认启用

- **WHEN** 真机发布执行时 `AIDCP_REAL_PUBLISH` 未设置或为任意非 `'false'` 的值
- **THEN** 系统 MUST 挂载 `approvalGate` 走飞书人审，未获 `approved=true` 不发布

#### Scenario: 仅显式 false 才跳过人审

- **WHEN** 启动时显式设置 `AIDCP_REAL_PUBLISH=false`（本地开发场景）
- **THEN** 系统跳过人审旁路放行，此为唯一被允许跳过人审的取值

#### Scenario: 审批拒绝或超时绝不发布

- **WHEN** 飞书审批信号为 `approved: false`、超时未返回、或信号文件缺失
- **THEN** 系统 MUST NOT 点发布，MUST 返回审批未通过的失败结果（如 `approval_rejected_or_timeout`）

#### Scenario: 缺省即静默直发属反例

- **WHEN** 实现保留旧条件 `=== 'true'`，导致不设 `AIDCP_REAL_PUBLISH` 时旁路人审直接真机发布
- **THEN** 该行为 MUST 被判定为违反 `AC-PUB` 红线，条件 MUST 改为 `!== 'false'` 使人审默认必过

### Requirement: publish.result 经信封 id 回写 publish_log，失败如实记 failed 不假成功

edge 发布完成后回传的 `publish.result` MUST 经原 `publish.request` 的信封 id 关联回写 `publish_log`：edge MUST 用原 `env.id` 回填 `publish.result.id` 并透传 `recordId`；cloud `handler.ts` 收到 `publish.result` 后 MUST 调用回写——`ok=true` 时 `updatePostId()`（状态 `draft/needs_review → published`）、`ok=false` 时 `updateStatus('failed')`，MUST NOT 把 `publish.result` 当作观测消息直接丢弃。回执丢失、回执标 `ok:false`、或回写自身失败时，记录 MUST NOT 被伪造为 `published`；失败 MUST 如实落 `failed`，回执长期缺失的记录 MUST 保留可识别的非成功状态（不假成功）。`HandlerDeps` MUST 注入 `publishLogStore`，`server.ts` 初始化时 MUST 接线。

#### Scenario: 发布成功回写 published

- **WHEN** cloud `handler.ts` 收到 `publish.result` 且 `ok: true`、`postId` 与 `recordId` 齐备
- **THEN** handler 调用 `publishLogStore.updatePostId(recordId, postId)`，将该记录状态从 `draft/needs_review` 更新为 `published`

#### Scenario: 发布失败如实记 failed

- **WHEN** cloud `handler.ts` 收到 `publish.result` 且 `ok: false`
- **THEN** handler 调用 `publishLogStore.updateStatus(recordId, 'failed')`，MUST NOT 将该记录置为 `published`

#### Scenario: 回执丢失不假成功

- **WHEN** edge 发布后 `publish.result` 始终未达 cloud（回执丢失），对应 `publish_log` 记录停留在 `draft/needs_review`
- **THEN** 该记录 MUST 保持非 `published` 状态，系统 MUST NOT 将其伪造为发布成功

#### Scenario: 把 publish.result 当观测消息丢弃属反例

- **WHEN** handler 收到 `publish.result` 后仅打印日志、不调任何回写方法，使 `publish_log` 永远停在 `draft`
- **THEN** 该行为 MUST 被判定为「静默假成功」变体违规，handler MUST 改为按 `ok` 实调 `updatePostId()` / `updateStatus()`

### Requirement: 发帖 envelope 含 title 与 images[]

`PublishExecutor` 构造 `publish.request` envelope 时，其 payload MUST 包含 `title`（来自 `CreatedContent.title`），以满足协议 `PublishRequestPayload` 要求；MUST 包含 `recordId`（用于 `publish.result` 回写关联）。配图 MUST 以数组 `images?: string[]` 承载，MUST NOT 沿用旧单数字段 `imageUrl`。协议 v2 改动 MUST 三处同步：edge / cloud 两份 `src/comm/protocol.ts` 逐字一致 + `command-bridge` 核查（确认 `publish.request` 由 `PublishExecutor` 直造、不经映射、无漂移）+ `docs/protocol.md`（本变更仅改 payload 字段、不新增消息类型，头部计数不变，仅补字段说明）；漂移 MUST 由 `typecheck` 的 `Record<MessageType, true>` 穷举暴露。

#### Scenario: envelope 携带 title 与数组 images

- **WHEN** `PublishExecutor` 为一条配了图的草稿构造 `publish.request`
- **THEN** envelope payload MUST 含 `title`、`recordId`，且配图以 `images: [url]` 数组承载，不出现单数 `imageUrl` 字段

#### Scenario: 两份 protocol.ts 逐字一致

- **WHEN** 修改 `PublishRequestPayload` / `PublishResultPayload` / `PublishApprovalRequestPayload` / `ActionCompletedPayload` 字段
- **THEN** edge 与 cloud 两份 `src/comm/protocol.ts` 对应定义 MUST 逐字一致，`docs/protocol.md` §2 表与字段说明 MUST 同步

#### Scenario: 协议漂移被 typecheck 暴露

- **WHEN** 两份 `protocol.ts` 的 `MessageType` 或 payload 定义出现不一致
- **THEN** `npm run typecheck` 中 `Record<MessageType, true>` 穷举 MUST 失败，阻止漂移合入

#### Scenario: 漏填 title 属反例

- **WHEN** `PublishExecutor` 构造 envelope 时漏填 `title`，与 `PublishRequestPayload` 要求不符
- **THEN** 该实现 MUST 被判定为残废 bug，MUST 补齐 `title`（取自 `CreatedContent.title`）

### Requirement: 来源血缘 sourceConcepts 与 sourceLikedIds 真实

`PublishExecutor` 落库时，`sourceConcepts` MUST 为真实概念（来自触发输入 / `ConceptStore`），MUST NOT 用 `tags` 充数；`sourceLikedIds` MUST 为真实点赞笔记 id，MUST NOT 写死为 `[]`。系统 SHALL 新增轻量点赞存储 `LikedNoteStore`（`liked_notes` 表），在真实 `like` 完成且 note 详情可得时落库，为 `sourceLikedIds` 与点赞统计提供诚实数据源。为支撑落库，协议 `ActionCompletedPayload` MUST 新增 `noteId` 字段，cloud handler MUST 透传该 `noteId`，`server.ts` MUST 订阅 `interaction.occurred` 在点赞成功时写入 `liked_notes`。

#### Scenario: 落库使用真概念与真点赞 id

- **WHEN** `PublishExecutor` 为一条帖子落库，触发输入含真实概念、近期点赞含真实 noteId
- **THEN** 记录的 `sourceConcepts` 来自真实概念（非 tags），`sourceLikedIds` 为真实点赞笔记 id（非写死 `[]`）

#### Scenario: 点赞成功时落库 liked_notes

- **WHEN** edge 上报 `action.completed`，`action='like'`、`ok=true` 且携带 `noteId`，note 详情可得
- **THEN** cloud 经 `interaction.occurred` 订阅将该笔记写入 `liked_notes`（note_id 唯一），供后续 `sourceLikedIds` 引用

#### Scenario: sourceLikedIds 写死空数组属反例

- **WHEN** 实现仍把 `sourceLikedIds` 硬编码为 `[]`、`sourceConcepts` 用 `tags` 充数
- **THEN** 该行为 MUST 被判定为来源血缘断裂违规，MUST 改为引用 `LikedNoteStore` 真实点赞 id 与真实概念

#### Scenario: 无真实数据源时不得编造

- **WHEN** 某次发帖确无对应的真实点赞笔记（`liked_notes` 中无相关记录）
- **THEN** `sourceLikedIds` MUST 如实为空，MUST NOT 编造或填入不相关的 id

### Requirement: 删 temp 调试口后无绕过流水线的发布路径

系统 MUST 删除两个 TODO(temp) 调试口：cloud `/debug/publish`（127.0.0.1:8788 HTTP 端口，含其端口读取与 HTTP server 块）与 CLI `trigger:publish-temp`（含 `src/cli/trigger-publish-temp.ts` 整文件与 `package.json` 脚本行）。删除后，触发发帖的唯一入口 MUST 是 `PublishScheduler` 的三扳机（概念积累 / 风控窗口 / 飞书 `/publish`）；MUST NOT 存在任何绕过 `PublishOrchestrator` 触发链与发布前人审的旁路发布路径。现网手动触发 SHALL 改用飞书 `/publish` 命令。

#### Scenario: 调试 HTTP 端口已移除

- **WHEN** 删除后向 cloud 的 127.0.0.1:8788 `/debug/publish` 发起请求
- **THEN** 该端口不再监听、不再受理任何触发发布的请求

#### Scenario: CLI temp 脚本已移除

- **WHEN** 运维尝试运行 `npm run trigger:publish-temp` 或调用 `src/cli/trigger-publish-temp.ts`
- **THEN** 该脚本与 `package.json` 脚本行均已删除、不可用，手动触发改走飞书 `/publish`

#### Scenario: 所有触发入口都经过流水线与人审

- **WHEN** 任意来源（自动扳机或手动命令）触发发帖
- **THEN** 该触发 MUST 经 `PublishScheduler` → `PublishOrchestrator.trigger()`，且真机发布 MUST 经发布前飞书人审

#### Scenario: 残留绕过流水线的旁路属反例

- **WHEN** 代码中仍保留任何可直接构造 `publish.request` 或绕过 `PublishOrchestrator` 与人审直发的调试/捷径入口
- **THEN** 该路径 MUST 被判定为违规，MUST 一并移除，确保发布只能经三扳机流水线
