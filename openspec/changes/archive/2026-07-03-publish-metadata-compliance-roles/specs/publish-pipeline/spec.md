## ADDED Requirements

### Requirement: 按维度拆分的元数据决策角色

发帖黑板流水线 SHALL 为发帖元数据按维度提供独立的 cloud 决策角色（`TopicStrategist`、`MentionStrategist`、`LocationStrategist`、`CollectionStrategist`、`VisibilityDecider`、`PermissionDecider`、`PublishModeDecider`、`ComplianceDecider`），每个角色 MUST 实例化并注册到 `PublishOrchestrator`，MUST NOT 仅作为类型联合或注释里的名字、也 MUST NOT 把多维度决策合并进单一 `MetadataEvaluator`。每个角色 MUST 各写自己的中间黑板键，且无论成败都写键（写降级默认值，遵守黑板 R1 死锁防护）。`TopicStrategist` MUST 在 `createdContent.tags` 基础上产出话题、约束话题数 3-30；`MentionStrategist` MUST 去重并剔除账号自身、上限 10；`PublishModeDecider` 的定时时间 MUST 限定未来且 ≤7 天。

#### Scenario: 各维度角色独立产出中间键
- **WHEN** `createdContent`（含 `tags`）与 `assembledContent` 就绪
- **THEN** 每个元数据维度角色按自己的 watchKeys 激活并写入对应中间键（如 `topicSelection`/`mentionSelection`/`visibilityDecision` 等），各角色 LLM/策略失败时写降级默认值而非不写键

#### Scenario: 话题在已有 tags 基础上扩展并满足 3-30 硬约束
- **WHEN** `TopicStrategist` 基于 `createdContent.tags` 与内容做话题决策
- **THEN** 产出的 `selectedTopics` 数量落在 3-30 闭区间内，且包含/扩展原有 tags，不产出超过 30 个话题

#### Scenario: @提及去重剔除自己且不超过 10
- **WHEN** `MentionStrategist` 决策推荐 @ 用户
- **THEN** `selectedMentions` 去重、不含账号自身、长度 ≤10；无合适人选时回空数组

#### Scenario: 反例——不得编造元数据凑数
- **WHEN** 某维度（如地点/合集/@）无合适候选或 LLM 决策为空
- **THEN** 该维度角色 MUST 如实写空值（`[]` 或 `null`），MUST NOT 为提高覆盖度而编造地点/合集/@ 用户，对应 `metadataScore` 该维度计 0 分

### Requirement: 可见范围云端必选不可为空

`VisibilityDecider` SHALL 产出 `public | friends_only | self_only` 三选一，云端决策端 MUST 必选、MUST NOT 写入 `null`/`undefined`；LLM 或策略失败时 MUST 降级为最保守的 `self_only`，MUST NOT 因失败而隐式落到 `public`（防「静默假成功」式的无意公开）。本要求约束的是「云端必须选出某值」；该值实际应用到边缘页面（指令下发）属 stage-4，不在本阶段。

#### Scenario: 正常决策产出三选一
- **WHEN** `VisibilityDecider` 基于内容与人设决策可见范围
- **THEN** `visibility` 取 `public`/`friends_only`/`self_only` 之一且非空，附 `visibilityReason`

#### Scenario: 决策失败降级最保守值
- **WHEN** `VisibilityDecider` 的 LLM 调用失败或返回非法值
- **THEN** `visibility` 降级为 `self_only`（最保守），而非 `public`

#### Scenario: 反例——不得隐式公开
- **WHEN** 可见范围决策不可用且无明确「公开」依据
- **THEN** 系统 MUST NOT 默认 `public`；缺省/失败一律收敛到 `self_only`

#### Scenario: 可见范围始终非空进入聚合
- **WHEN** `MetadataAggregator` 读取 `visibilityDecision`
- **THEN** `publishMetadata.visibility` 字段始终为三枚举之一、不为 null

### Requirement: 合规声明与 AI 声明强制红线

`ComplianceDecider` SHALL 产出合规声明决策（AI 生成 / 广告 / 原创）及优先级 `ai > ad > origin`。当 `assembledContent.aiScore` 超过强制阈值（硬编码，统一 0.6（对齐 approval-gatekeeper abort））**或** 终稿内容含 AI 生成/合成类关键词时，系统 MUST 强制 `compliance.ai=true` 并置 `compliance.aiEnforced=true`，该标记一经置位 MUST NOT 被后续任何流程降级为 `ai=false`。`PublishExecutor`/`MetadataAggregator` 落库或聚合前若检出 `aiEnforced && !ai` 的篡改态，MUST 记审计日志并拒绝降级（保持 `ai=true`），MUST NOT 静默放行。本红线对齐 2026 合规硬规，不可被人设/用户偏好覆盖。

#### Scenario: AI 味分超阈值强制 AI 声明
- **WHEN** `assembledContent.aiScore > 0.6`
- **THEN** `compliance.ai=true` 且 `compliance.aiEnforced=true`，记一条强制声明日志

#### Scenario: 内容含 AI 生成关键词强制声明
- **WHEN** 终稿正文命中「AI 生成/合成/AIGC」等关键词而 aiScore 未超阈值
- **THEN** 仍强制 `compliance.ai=true`、`aiEnforced=true`

#### Scenario: 反例——强制 AI 声明不可被降级
- **WHEN** 后续流程或用户偏好试图把 `aiEnforced=true` 的记录改为 `compliance.ai=false`
- **THEN** 系统 MUST 拒绝该降级、保持 `ai=true`，记审计日志，MUST NOT 静默落库为 `ai=false`

#### Scenario: 非 AI 内容不强制声明
- **WHEN** aiScore 低于阈值且无 AI 关键词
- **THEN** `compliance.ai` 不被强制（可由策略决定是否声明广告/原创），`aiEnforced` 为 false 或缺省

### Requirement: publishMetadata 聚合键与 assembledContent 边界

系统 SHALL 由唯一生产者 `MetadataAggregator`（waitAll 各维度中间键）汇合产出单一黑板键 `publishMetadata`，并按维度覆盖度计算 `metadataScore`（0-1）。`MetadataAggregator` 与所有元数据角色 MUST 只读 `assembledContent`、MUST NOT 写 `assembledContent`；`assembledContent` 的八字段（`finalContent/finalTags/imageUrl/aiScore/qualityScore/rewritten/flaggedPhrases/assembledAt`）MUST 逐字保持不变、MUST NOT 因本阶段新增字段。`publishMetadata` MUST 是 `assembledContent` 之外的并行键。各维度缺失/失败时 `metadataScore` 对应项计 0，整体可低至 0、上限 1。

#### Scenario: 聚合产出 publishMetadata 与覆盖度分
- **WHEN** 各维度中间键全部就绪（含降级默认值）
- **THEN** `MetadataAggregator` 写入 `publishMetadata`（含各维度选择 + `compliance` + `metadataScore` + `decidedAt`），`metadataScore` 按各维度有效性加权求和

#### Scenario: assembledContent 八字段不回归
- **WHEN** 本阶段流水线跑完一轮
- **THEN** `assembledContent` 仍为且仅为原八字段、值与阶段2 同形，未被注入任何元数据字段

#### Scenario: 单一生产者无死锁
- **WHEN** 某些维度角色降级写默认值、其余正常产出
- **THEN** `MetadataAggregator` 的 waitAll 仍因「各维度键无论成败都写」而满足并触发一次，产出 `publishMetadata`，不挂起

#### Scenario: 反例——元数据不得污染 assembledContent
- **WHEN** 任一元数据角色或聚合器运行
- **THEN** 它们 MUST NOT 调用 `ctx.write('assembledContent', ...)`，元数据只落 `publishMetadata` 等并行键

### Requirement: 本阶段不下发元数据 edge 指令

本阶段 SHALL 只产出元数据/合规决策并可选落库/记录血缘，MUST NOT 让 `CommandSequencer` 把任何元数据相关指令（`set_option`/`set_schedule`/`add_with_candidate` 的 `mention`/`location`/`collection`/可见范围/权限/各声明）加入发布指令序列；`buildCommandSequence` 的指令集 MUST 与本阶段前保持一致。edge 对这些 kind 仍回 `kind_not_implemented`，本阶段 MUST NOT 实装其 edge 处理器。`PublishExecutor` 的发布判定、AC-PUB 授权闸与既有发布行为 MUST 不变；若落库 `publishMetadata`，MUST NOT 借此改变是否发布/发什么指令。

#### Scenario: 指令序列不含元数据指令
- **WHEN** 已授权的 auto_publish 走 `CommandSequencer.executePublishSequence`
- **THEN** 下发的指令仍为 `navigate_entry/select_mode/fill_field/add_with_candidate(topic)/submit_publish/capture_postId`，不含 `set_option/set_schedule/add_with_candidate(mention|location|collection)`

#### Scenario: 元数据已决但暂不应用
- **WHEN** `publishMetadata` 已产出（含可见范围/权限/合规声明等决策）
- **THEN** 这些决策仅落库/可观测，不转化为任何下发到 edge 的指令（应用延后 stage-4）

#### Scenario: 落库不改发布行为
- **WHEN** `PublishExecutor` 把 `publishMetadata` 随 `recordId` 落库
- **THEN** 发布是否进行、走哪条路径（指令驱动/旧整页）、授权判定均与未落库时完全一致

#### Scenario: 反例——edge 元数据 kind 仍诚实拒绝
- **WHEN** 任何路径意外向 edge 下发 `set_option`/`set_schedule`
- **THEN** edge MUST 回 `kind_not_implemented`、MUST NOT 假成功，且本阶段 MUST NOT 为消除该拒绝而实装 edge 处理器
