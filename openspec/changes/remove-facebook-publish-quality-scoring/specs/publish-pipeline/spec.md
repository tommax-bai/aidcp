## MODIFIED Requirements

### Requirement: 内容质检拆三职（ContentCleaner / AiFlavorScorer / QualityScorer）

内容后处理 SHALL 拆为三个单职责角色：`ContentCleaner`（去 AI 味）watch `createdContent`、复用现有
`PostProcessor`（不改其实现）产出 `cleanedContent`；`AiFlavorScorer`（AI 味分）watch `cleanedContent`
产出 `aiFlavorScore`（其 `aiScore` 为去 AI 味命中归一值）；`QualityScorer`（质量适用策略与非 Facebook
质量分）watch `cleanedContent` 产出 `qualityReport`。

对非 Facebook 平台，`QualityScorer` SHALL 经 LLM 评审产出 `qualityScore` 0-100 和 `status='scored'`；
评审 LLM 失败时 MUST 走既有降级公式 `qualityScore = round((1-aiScore)*70)`，MUST NOT 编造满分或固定高分。
对 Facebook，`QualityScorer` SHALL 不调用 LLM，产出 `qualityScore=null` 和
`status='not_applicable'`，MUST NOT 用任意数字冒充跳过评分。单个角色 MUST NOT 同时承担
“去 AI 味 + AI 味评分 + 质量评审”两项以上职责。

#### Scenario: 非 Facebook 的清洗、AI 味分、质量分分属三角色

- **WHEN** 非 Facebook `createdContent` 就绪、进入内容后处理
- **THEN** `ContentCleaner` 去 AI 味写 `cleanedContent`，`AiFlavorScorer` 写 `aiFlavorScore`，`QualityScorer` 经 LLM 评审写 `qualityReport { status:'scored', qualityScore:<0-100> }`
- **AND** 没有任一角色同时做清洗与质量评审

#### Scenario: Facebook 写不适用结果且不调评分模型

- **WHEN** Facebook `createdContent` 就绪、进入内容后处理
- **THEN** `QualityScorer` SHALL 写 `qualityReport { status:'not_applicable', qualityScore:null }`
- **AND** MUST NOT 构造质量评审 prompt 或调用评分 LLM

#### Scenario: AI 味分如实投影、不重复计算

- **WHEN** `ContentCleaner` 已产出 `cleanedContent.aiScore`
- **THEN** `AiFlavorScorer` 产出的 `aiFlavorScore.aiScore` 恒等于 `cleanedContent.aiScore`（显式收口、留独立演进点），不重算、不篡改

#### Scenario: 非 Facebook 评审 LLM 失败时质量分如实降级

- **WHEN** 非 Facebook `QualityScorer` 的评审 LLM 失败或返回非法 JSON
- **THEN** `QualityScorer` 走降级公式产出 `status='scored'` 与 `qualityScore = round((1-aiScore)*70)` 并记日志
- **AND** 分数随 AI 味浓度如实变化，绝不返回固定满分

#### Scenario: 红线——用数字伪装不适用（反例）

- **WHEN** 任一实现用固定高分、零分或 `NaN` 表示 Facebook “未评分”，或把 `aiScore` 抹零
- **THEN** MUST 视为违规、不予合入；未评分必须使用显式 `null + not_applicable`

### Requirement: ContentAssembler 瘦身但产出同形 assembledContent（稳定边界、下游零改动）

`ContentAssembler` SHALL 瘦身为**纯组装**角色：`watchAll`（`waitAll: true`）`cleanedContent` /
`aiFlavorScore` / `qualityReport` / `imageDirective` / `coverSelection` 就绪后仅做字段拼装，MUST NOT 再持有
`llmClient` / `postProcessor`、MUST NOT 做任何 LLM 调用或外部 IO。它 SHALL 产出
`assembledContent`，字段为 `{ finalContent, finalTags, imageUrls, imageUrl, aiScore, qualityScore,
qualityStatus, rewritten, flaggedPhrases, assembledAt }`：`qualityScore` 与 `qualityStatus` 逐字透传
`qualityReport`；Facebook 为 `null + not_applicable`，非 Facebook 为真实数字 + `scored`。
`imageUrls` ← `coverSelection.imageUrls`，`imageUrl` ← `imageUrls[0] ?? null`。
自话题拆分能力起 `finalTags` 恒为 `[]`，话题继续由 `publishMetadata.topics` 承载。
`ApprovalGatekeeper` 仍 watch `assembledContent`；本要求 MUST NOT 触及协议或 edge。

#### Scenario: 瘦身后仅组装、无 LLM 或 IO

- **WHEN** `cleanedContent` / `aiFlavorScore` / `qualityReport` / `imageDirective` / `coverSelection` 五键全部就绪
- **THEN** `ContentAssembler` SHALL 仅映射既有字段，并逐字透传 `qualityReport.qualityScore` 与 `qualityReport.status`
- **AND** 其依赖中不含 `llmClient` / `postProcessor`

#### Scenario: Facebook 组装结果保留未评分事实

- **WHEN** `qualityReport={ status:'not_applicable', qualityScore:null }`
- **THEN** `assembledContent.qualityStatus` SHALL 为 `not_applicable` 且 `qualityScore` SHALL 为 `null`
- **AND** MUST NOT 在组装层回落成数字

#### Scenario: 非 Facebook 组装结果保留真实分数

- **WHEN** `qualityReport={ status:'scored', qualityScore:72 }`
- **THEN** `assembledContent.qualityStatus` SHALL 为 `scored` 且 `qualityScore` SHALL 为 `72`

#### Scenario: 下游消费方保持同一发布门

- **WHEN** 一轮发布流水线完成组装
- **THEN** `ApprovalGatekeeper` 仍 SHALL watch `assembledContent`，`PublishExecutor` 仍 SHALL watch `gateDecision`
- **AND** `PublishExecutor` 继续读 `imageUrls` 上传全集、读 `publishMetadata.topics` 作为话题真源

#### Scenario: 红线——组装层发明平台策略（反例）

- **WHEN** 任一实现让 `ContentAssembler` 自行判断平台、调用模型或把 `null` 改成数字
- **THEN** MUST 视为越界；平台适用策略属于评分与 admission 角色，组装层只透传

### Requirement: 内容质量评审随品类与人设自适应（不改放行闸与降级公式）

对启用质量评分的非 Facebook 平台，`QualityScorer` 的评审 SHALL 随本帖**内容品类**与账号**人设**
自适应，MUST NOT 用单一“干货 / 信息密度”口味评判所有品类：干货类看信息量 / 实用性，情感 / 审美 /
生活类看共鸣 / 画面感 / 真实体验；“真实感”判据 SHALL 为“是否贴合该账号人设声音”。账号人设 SHALL
作为一等入参接入评审 prompt。评审 LLM 失败时仍走 `qualityScore = round((1-aiScore)*70)`，MUST NOT
编造高分；非 Facebook 的 `ApprovalGatekeeper` 放行 / 人审 / 拒绝分支阈值不变。

Facebook 不适用本质量评审要求：MUST NOT 构造该 prompt 或调用对应 LLM，并 SHALL 由平台 admission
确定性进入 `manual_review`。

#### Scenario: 非 Facebook 情感类不因缺硬信息被压低

- **WHEN** 一篇启用质量评分的情感或生活类内容进入质量评审
- **THEN** 评审 SHALL 按共鸣、画面感、真实体验等品类子标准打分
- **AND** MUST NOT 仅因缺少具体数据而系统性压低质量分

#### Scenario: 非 Facebook 评审接人设声音

- **WHEN** 构造非 Facebook `QualityScorer` 评审 prompt
- **THEN** prompt SHALL 含账号人设，并把真实感表述为是否贴合该人设声音

#### Scenario: Facebook 不进入自适应质量评审

- **WHEN** 发布平台为 Facebook
- **THEN** MUST NOT 构造品类/人设质量评审 prompt，MUST NOT 调用质量评分 LLM

#### Scenario: 非 Facebook 不动放行闸与降级公式

- **WHEN** 非 Facebook 评审 LLM 失败，或审视其 `ApprovalGatekeeper` 放行逻辑
- **THEN** `QualityScorer` 仍走 `round((1-aiScore)*70)` 降级
- **AND** 既有 `auto_publish` / `manual_review` / `retry` / `abort` 阈值与分支保持不变

## ADDED Requirements

### Requirement: 质量 admission 按平台适用且保持单生产者

`ApprovalGatekeeper` SHALL 继续作为 `gateDecision` 的唯一生产者。对 Facebook，它 MUST NOT 调用
Gatekeeper LLM，必须确定性返回 `needsApproval=true`、`recommendedAction='manual_review'` 和稳定安全原因码；
对非 Facebook，它 SHALL 继续使用既有质量分、AI 味和禁用词规则与 LLM/fallback。

#### Scenario: Facebook Gatekeeper 零模型调用

- **WHEN** `assembledContent.qualityStatus='not_applicable'` 且平台为 Facebook
- **THEN** `ApprovalGatekeeper` SHALL 不构造 prompt、不调用 LLM
- **AND** SHALL 产出 `manual_review`，使既有 `PublishExecutor` 激活

#### Scenario: Facebook 不会因空分数进入 retry

- **WHEN** Facebook `qualityScore=null`
- **THEN** 系统 MUST NOT 把 `null` 转成 0 或据此选择 `retry` / `abort`

#### Scenario: 非 Facebook 缺质量分失败安全

- **WHEN** 非 Facebook admission 收到 `qualityStatus!='scored'` 或 `qualityScore=null`
- **THEN** 系统 SHALL 诚实拒绝该候选，MUST NOT 自动发布或回落高分

