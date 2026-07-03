## Why

发帖黑板流水线（`aidcp-cloud/src/publish-agent`）当前**只决策正文与配图**，发帖**元数据决策几乎是空白**：话题仅来自 `createdContent.tags`，没有任何角色基于内容/人设做话题取舍；@提及、地点、合集、可见范围、评论/保存权限、立即/草稿/定时、合规声明（AI 生成 / 广告 / 原创）**全部无人决策**。下游 `CommandSequencer` 只发 `navigate_entry/select_mode/fill_field/add_with_candidate(topic)`，`submit_publish/capture_postId`；边缘协议虽已登记 `set_option/set_schedule` 与 `add_with_candidate` 的 `candidateKind: mention/location/collection`，但处理器一律回 `kind_not_implemented`（见 `aidcp-edge/src/flows/publish-command-handlers.ts`）。

更关键的是 **2026 合规硬规未覆盖**：含 AI 生成内容必须强制声明，但没有任何角色产出该决策；`aiScore` 已在黑板里就绪（`aiFlavorScore`/`assembledContent.aiScore`）却无人据此强制 AI 声明，存在合规红线缺口。

本 change 是 **A 重构「阶段3 元数据 + 合规决策角色」**，对齐版本 A 的「种类级」决策粒度——**不是 165 全量一步一角色，也不是把所有元数据塞进单一 MetadataEvaluator**，而是按维度拆成若干单一职责决策角色，与阶段2 已落地的生产段细拆（6→11 角色）同风格。

## What Changes

- **新增 7-8 个 cloud 元数据/合规决策角色**（黑板 `BasePublishRole` 子类，纯 cloud 决策，无 edge / 无协议改动）：
  - `TopicStrategist`：话题决策——在 `createdContent.tags` 基础上推荐 3-10 个话题，硬约束 3-30。
  - `MentionStrategist`：@提及决策——推荐 ≤10 个用户，去重、剔除自己；可空。
  - `LocationStrategist`：地点决策——可空。
  - `CollectionStrategist`：合集决策——可空。
  - `VisibilityDecider`：可见范围——`public | friends_only | self_only`，**云端必选不可 null**，失败降级最保守 `self_only`。
  - `PermissionDecider`：评论/保存权限开关。
  - `PublishModeDecider`：立即/草稿/定时 + 定时时间（≤7 天）。
  - `ComplianceDecider`：合规声明（AI 生成 / 广告 / 原创）+ 优先级（ai > ad > origin）。**2026 硬规红线**：含 AI 生成内容或 `aiScore` 超阈值时强制 AI 声明（`aiEnforced=true`），不可被后续流程降级。
- **新增聚合键 `publishMetadata`**：各维度角色各写独立中间键，由 `MetadataAggregator`（waitAll 各维度键）汇合为单一 `publishMetadata` 键，并计算覆盖度 `metadataScore`。`publishMetadata` 是 `assembledContent` 之外的**并行新键**。
- **`assembledContent` 稳定边界逐字不动**：阶段2 刚保住的八字段（`finalContent/finalTags/imageUrl/aiScore/qualityScore/rewritten/flaggedPhrases/assembledAt`）不增不改；元数据**绝不塞进** `assembledContent`。`MetadataAggregator` 与各角色只读 `assembledContent`（取 `aiScore`/`finalContent` 供合规判定），不写它。
- **元数据决策「已决但 edge 应用延后 stage-4」**：本阶段只产出决策 + 落库/血缘（可观测），**不让 `CommandSequencer` 发任何元数据 edge 指令**（`set_option/set_schedule/add_with_candidate(mention/location/collection)` 仍不入序列），类比阶段1 指令链路的「休眠」。`publishMetadata` 可选随 `recordId` 落库，但**不改 `PublishExecutor`/`CommandSequencer` 的既有发布行为**。
- **BREAKING**（内部，无外部协议/接口破坏）：发帖黑板**角色集再次扩张**（阶段2 的 11 + 本阶段约 8 = ~19）、`PipelineFields` **新增多个黑板键**（各维度中间键 + `publishMetadata`）。下游 `ApprovalGatekeeper`/`PublishExecutor` 的现有 watch 与行为不变，故对发布结果零破坏；标 BREAKING 仅因角色集与黑板 schema 的内部契约变更。

## Capabilities

### New Capabilities

- `publish-pipeline`: 发帖黑板流水线的**元数据与合规决策能力**——按维度拆分的 cloud 决策角色产出话题/@/地点/合集/可见范围/权限/发布模式/合规声明，聚合为 `publishMetadata` 并打覆盖度分；在不破坏 `assembledContent` 稳定边界、不下发任何元数据 edge 指令的前提下，把 2026 合规 AI 声明强制为不可降的红线。

### Modified Capabilities

<!-- 无既有 spec 被修改。assembledContent 边界、阶段1 指令链路、阶段2 生产段细拆均落在尚未建 spec 的代码层；本 change 以 publish-pipeline 为新能力承载，不改写 openspec/specs/ 下任何现有 spec。下游 ApprovalGatekeeper/PublishExecutor 行为不变，故不列为 modified。 -->

## Impact

- **aidcp-cloud（唯一改动仓）**：
  - `src/publish-agent/types.ts`：新增 `TopicSelection/MentionSelection/LocationSelection/CollectionSelection/VisibilityDecision/PermissionDecision/PublishModeDecision/ComplianceDecision/PublishMetadata` 类型与 `METADATA_DEFAULT_VALUES` 常量；`PipelineFields` 增各维度中间键 + `publishMetadata`。
  - `src/publish-agent/roles/`：新增约 8 个决策角色文件 + `metadata-aggregator.ts`；`roles/index.ts` 导出。
  - `src/publish-agent/prompts.ts`：新增各 LLM 决策角色的 prompt 构造器（话题/合规等）。
  - `src/server.ts`：`registerRole(...)` 注册新角色（注册顺序无关正确性）。
  - `src/publish-agent/roles/publish-executor.ts`（可选、最小）：仅让 executor 把 `publishMetadata` 随 `recordId` 落库/记录血缘，**不改其发布判定与指令行为**；落库前校验 `compliance.aiEnforced && !compliance.ai` 视为篡改、记审计并拒绝降级。
  - `src/publish-agent/publish-log-store.ts`（可选）：若落库，新增可空元数据列（如 `publish_metadata JSONB`、`ai_enforced BOOLEAN`），DDL 幂等、向后兼容。
  - `test/publish-agent/`：各新角色单测 + `MetadataAggregator` 单测 + orchestrator 整链测（含 `publishMetadata` 产出、且 `assembledContent` 八字段不回归）；`npm test` / `npm run typecheck` / `npm run test:acceptance` 全过。
- **不碰**：
  - **协议** `src/comm/protocol.ts`（两端逐字一致）——本阶段零协议改动，`PROTOCOL_VERSION` 不动。
  - **aidcp-edge** 全仓——不实装任何 `set_option/set_schedule/mention/location/collection` 处理器，继续回 `kind_not_implemented`。
  - **下游发布行为**——`CommandSequencer.buildCommandSequence` 不新增元数据指令；`ApprovalGatekeeper`/`PublishExecutor` 的 AC-PUB 授权闸与发布序列不变。
- **风控**：纯决策 + 落库，不触碰 like/collect/follow/comment/publish 高风险动作计数；无新风控路径。
