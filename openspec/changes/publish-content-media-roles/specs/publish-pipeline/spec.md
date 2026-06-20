# publish-pipeline

发帖流水线生产段以黑板（`PipelineContext` watch/write）协作；本 change 引入"生产段单职责角色"
与"`assembledContent` 稳定边界"契约：配图链路决策与执行解耦、内容质检拆三职、组装瘦身但同形产出，
并补齐内容类型与封面两个前后置角色；黑板新键必须有唯一生产者且不死锁。

## ADDED Requirements

### Requirement: 配图链路决策与执行解耦（ImagePlanner / ImageGenerator）

配图链路 SHALL 拆为两个独立角色：`ImagePlanner`（决策）watch `createdContent` 决定要不要图 / 配图
prompt / 风格 / 张数 / `fallbackStrategy`，写新键 `imagePlan`；`ImageGenerator`（执行）watch `imagePlan`
调通义万相（复用现有 `WanxiangClient` / `ImageProvider`）生成 URL，写 `imageDirective`。生图失败时
`ImageGenerator` MUST 按 `imagePlan.fallbackStrategy` 降级为**纯文字**并如实把 `imageDirective.imageUrl`
置为 `null`；MUST NOT 在生图失败时伪造 URL 或谎报有图。单个角色 MUST NOT 同时承担"配图决策"与"调图源生图"。

#### Scenario: 决策与生图分属两角色、各自可独立单测

- **WHEN** `createdContent` 就绪、流水线进入配图链路
- **THEN** `ImagePlanner` 先 watch `createdContent` 产出 `imagePlan`（含 `wantImage` / `imagePrompt` / `imageStyle` / `imageCount` / `fallbackStrategy`），`ImageGenerator` 再 watch `imagePlan` 产出 `imageDirective`；为 `ImageGenerator` 写单测只需桩图源、无需桩配图决策 LLM

#### Scenario: 计划不配图时直接产空 directive

- **WHEN** `imagePlan.wantImage === false` 或 `imagePlan.imagePrompt` 为空
- **THEN** `ImageGenerator` 不调图源，直接写 `imageDirective` 且 `imageUrl` 为 `null`、`fallbackStrategy` 为 `imagePlan.fallbackStrategy`，如实表示"本帖无图"

#### Scenario: 生图失败降级纯文字并如实标注

- **WHEN** `imagePlan.wantImage === true` 但 `imageProvider.generate` 返回空 URL / 抛错
- **THEN** `ImageGenerator` 按 `imagePlan.fallbackStrategy` 降级为纯文字，写 `imageDirective.imageUrl = null`，下游据此知晓本帖无配图，全链不出现伪造图

#### Scenario: 红线——生图失败谎报有图（反例）

- **WHEN** 任一实现在 `imageProvider.generate` 失败 / 返回空 URL 后，仍把 `imageDirective.imageUrl` 写成占位 URL、复用上一次的 URL、或把 `wantImage` 维持 true 而不置空
- **THEN** MUST 视为违规、不予合入（生图失败必须降级纯文字并如实标 fallback，绝不静默假成功）

### Requirement: 内容质检拆三职（ContentCleaner / AiFlavorScorer / QualityScorer）

内容后处理 SHALL 拆为三个单职责角色：`ContentCleaner`（去 AI 味）watch `createdContent`、复用现有
`PostProcessor`（不改其实现）产出 `cleanedContent`；`AiFlavorScorer`（AI 味分）watch `cleanedContent`
产出 `aiFlavorScore`（其 `aiScore` 为去 AI 味命中归一值）；`QualityScorer`（质量分）watch
`cleanedContent` 经 LLM 评审产出 `qualityReport`（`qualityScore` 为 0-100）。三角色 MUST 如实回报分数——
评审 LLM 失败时 `QualityScorer` MUST 走既有降级公式 `qualityScore = round((1-aiScore)*70)`，MUST NOT 编造
满分或固定高分掩盖失败。单个角色 MUST NOT 同时承担"去 AI 味 + AI 味评分 + 质量评审"两项以上职责。

#### Scenario: 清洗、AI 味分、质量分分属三角色

- **WHEN** `createdContent` 就绪、进入内容后处理
- **THEN** `ContentCleaner` 去 AI 味写 `cleanedContent`，`AiFlavorScorer` 写 `aiFlavorScore`，`QualityScorer` 经 LLM 评审写 `qualityReport`；没有任一角色同时做清洗与质量评审，为 `QualityScorer` 写单测只需桩评审 LLM、无需桩 `PostProcessor`

#### Scenario: AI 味分如实投影、不重复计算

- **WHEN** `ContentCleaner` 已产出 `cleanedContent.aiScore`
- **THEN** `AiFlavorScorer` 产出的 `aiFlavorScore.aiScore` 恒等于 `cleanedContent.aiScore`（显式收口、留独立演进点），不重算、不篡改

#### Scenario: 评审 LLM 失败时质量分如实降级

- **WHEN** `QualityScorer` 的评审 LLM 失败 / 返回非法 JSON
- **THEN** `QualityScorer` 走降级公式产出 `qualityScore = round((1-aiScore)*70)` 并记日志，分数随 AI 味浓度如实变化，绝不返回固定满分

#### Scenario: 红线——分数造假或职责混杂（反例）

- **WHEN** 任一实现谎报质量 / AI 味分（如失败时硬编码高分、把 `aiScore` 抹零），或一个角色同时做"去 AI 味 + 质量评分"
- **THEN** MUST 视为违规、不予合入（质量 / AI 味分必须如实，清洗与评分必须分属不同角色）

### Requirement: ContentAssembler 瘦身但产出同形 assembledContent（稳定边界、下游零改动）

`ContentAssembler` SHALL 瘦身为**纯组装**角色：`watchAll`（`waitAll: true`）`cleanedContent` /
`aiFlavorScore` / `qualityReport` / `imageDirective` / `coverSelection` 就绪后仅做字段拼装，MUST NOT 再
持有 `llmClient` / `postProcessor`、MUST NOT 做任何 LLM 调用或外部 IO。无论生产段如何细拆，它 SHALL 产出
**同形** `assembledContent`，字段恒为 `{ finalContent, finalTags, imageUrl, aiScore, qualityScore,
rewritten, flaggedPhrases, assembledAt }`，语义与细拆前一致。下游 `ApprovalGatekeeper`（watch
`assembledContent`）与 `PublishExecutor`（watch `gateDecision`）MUST NOT 因本次细拆而改动源码或注册；
本阶段 MUST NOT 触及协议、edge 或下游消费方。

#### Scenario: 瘦身后仅组装、无 LLM / 无 IO

- **WHEN** `cleanedContent` / `aiFlavorScore` / `qualityReport` / `imageDirective` / `coverSelection` 五键全部就绪
- **THEN** `ContentAssembler` 仅做字段映射（`finalContent ← cleanedContent.content`、`finalTags ← createdContent.tags`、`imageUrl ← coverSelection.imageUrl`、`aiScore ← aiFlavorScore.aiScore`、`qualityScore ← qualityReport.qualityScore`、`rewritten`/`flaggedPhrases ← cleanedContent`），其依赖中不含 `llmClient` / `postProcessor`

#### Scenario: 细拆后终稿形状不变

- **WHEN** 重组后的生产段跑完、`ContentAssembler` 写出 `assembledContent`
- **THEN** `assembledContent` 仍恰含 `finalContent` / `finalTags` / `imageUrl` / `aiScore` / `qualityScore` / `rewritten` / `flaggedPhrases` / `assembledAt` 八个字段，无增删改名，`aiScore`/`qualityScore`/`imageUrl`/`flaggedPhrases` 语义与细拆前等价

#### Scenario: 下游消费方不感知细拆

- **WHEN** 一轮发布流水线在细拆后完整跑通
- **THEN** `ApprovalGatekeeper` 仍 watch `assembledContent`、`PublishExecutor` 仍 watch `gateDecision`，二者源码与注册参数零改动，端到端结果（`gateDecision` / `publishResult`）与细拆前等价

#### Scenario: 红线——细拆波及下游或协议（反例）

- **WHEN** 任一细拆改动改了 `assembledContent` 字段集 / 字段名 / 字段语义，或改了 `ApprovalGatekeeper` / `PublishExecutor`，或触及协议 / edge
- **THEN** MUST 视为越界、不予合入（稳定边界 `assembledContent` 不可破，本阶段边界仅限生产段黑板内部）

### Requirement: ContentTypeSelector 产出内容类型

流水线 SHALL 以独立角色 `ContentTypeSelector` 决定内容类型，watch `scoutDecision`、仅在
`scoutDecision.shouldPublish === true` 时激活，产出新键 `contentType`（`kind` 为联合类型
`'image_text' | 'video' | 'text'`，当前实现恒为 `image_text`，结构预留视频 / 文字）。该角色 SHALL 为可演进
的真实角色；MUST NOT 在 `ContentAssembler` 或别处硬编码"一律图文"而绕过该角色，即便当前逻辑简单也必须实体化
角色边界以便后续无伤演进。

#### Scenario: 内容类型由专职角色决定

- **WHEN** `scoutDecision.shouldPublish === true`
- **THEN** `ContentTypeSelector` 激活并产出 `contentType`（现恒为 `image_text`），其 `kind` 结构允许后续扩展为 `video` / `text` 而无需改动其它生产段角色

#### Scenario: 不发布时不激活

- **WHEN** `scoutDecision.shouldPublish === false`
- **THEN** `ContentTypeSelector` 守卫不通过、不写 `contentType`，与 `ContentCreator` 短路语义一致，不阻塞流水线短路结束

#### Scenario: 类型预留结构可演进

- **WHEN** 后续阶段引入视频 / 纯文字类型
- **THEN** 仅需在 `ContentTypeSelector` 内扩展 `kind` 取值与判定逻辑，下游生产段角色与 `assembledContent` 形状无需改动

#### Scenario: 红线——硬编码类型绕过角色（反例）

- **WHEN** 任一实现在 `ContentAssembler` 或别处直接默认"一律图文"而不经 `ContentTypeSelector` 角色产出 `contentType`
- **THEN** MUST 视为违规、不予合入（预留角色边界即便逻辑简单也必须实体化为真实角色）

### Requirement: CoverSelector 选封面

流水线 SHALL 以独立角色 `CoverSelector` 从生成图中选封面，watch `imageDirective` 产出新键
`coverSelection { imageUrl, hasCover, selectedAt }`：单图场景直接选该图为封面，多图场景预留选择逻辑接口。
无图（`imageDirective.imageUrl` 为 `null`）时 `CoverSelector` MUST 如实产出 `{ imageUrl: null,
hasCover: false }`，使组装后 `assembledContent.imageUrl` 为 `null`；MUST NOT 在无图时静默选一个占位图或谎报
`hasCover: true`。该角色 SHALL 为可演进的真实角色，MUST NOT 在别处硬编码"一律首图"而绕过。

#### Scenario: 单图直选为封面

- **WHEN** `imageDirective.imageUrl` 为一个有效 URL
- **THEN** `CoverSelector` 产出 `coverSelection { imageUrl: <该URL>, hasCover: true }`，组装时 `assembledContent.imageUrl` 取该 URL

#### Scenario: 无图诚实回报空封面

- **WHEN** `imageDirective.imageUrl` 为 `null`（无图 / 生图失败降级）
- **THEN** `CoverSelector` 产出 `coverSelection { imageUrl: null, hasCover: false }`，组装后 `assembledContent.imageUrl` 为 `null`，如实表示"无封面"

#### Scenario: 多图选择逻辑预留接口

- **WHEN** 后续 `imageDirective` 携带多张生成图
- **THEN** `CoverSelector` 的选择接口可扩展多图封面策略（首图 / 美学 / LLM 选），当前单图场景行为不变

#### Scenario: 红线——无图谎报有封面（反例）

- **WHEN** 任一实现在无图时仍把 `coverSelection.imageUrl` 写成占位图、或把 `hasCover` 写为 `true`，或在别处硬编码"一律首图"绕过 `CoverSelector`
- **THEN** MUST 视为违规、不予合入（无封面必须如实回报，封面选择必须经专职角色）

### Requirement: 黑板新键有唯一生产者且不死锁

本 change 新增的六个黑板键 SHALL 全部在 `PipelineFields` 登记类型，且每个键 SHALL 恰有一个角色作为唯一生产者。
具体而言，`contentType` / `imagePlan` / `cleanedContent` / `aiFlavorScore` / `qualityReport` /
`coverSelection` 各由唯一角色（`outputKey`）生产，watch 链接必须接对（生产者的 `watchKeys` 指向已有上游生产者）。`ContentAssembler`
的 `waitAll` 依赖键 SHALL 全部由"无论成败都必写自己键"的角色生产——决策 / 评分 / 配图 / 封面链路各角色 MUST 经
`fallback`（`default` / `skip` + `getDefaultOutput`）保证在失败时仍写键，使 `waitAll` 不会因某键永不就绪而
死锁导致流水线超时。

#### Scenario: 每个新键恰有唯一生产者

- **WHEN** 审视生产段角色注册表
- **THEN** `contentType ← ContentTypeSelector`、`imagePlan ← ImagePlanner`、`imageDirective ← ImageGenerator`、`cleanedContent ← ContentCleaner`、`aiFlavorScore ← AiFlavorScorer`、`qualityReport ← QualityScorer`、`coverSelection ← CoverSelector`、`assembledContent ← ContentAssembler`，每键恰一个 `outputKey`，无两个角色写同一键

#### Scenario: watch 链接对上、键全部登记

- **WHEN** 运行 `npm run typecheck`
- **THEN** 六个新键均在 `PipelineFields` 有类型登记，各生产者 `watchKeys` 指向真实存在的上游键（`ImageGenerator` watch `imagePlan`、`CoverSelector` watch `imageDirective`、`AiFlavorScorer`/`QualityScorer` watch `cleanedContent`），类型检查零报错

#### Scenario: 失败链路仍写键、waitAll 不死锁

- **WHEN** 配图 / 清洗 / 质量评审任一环节失败降级
- **THEN** 对应角色经 `fallback` + `getDefaultOutput` 仍写出自己的键（`ImageGenerator`/`CoverSelector` 写空值、`ContentCleaner`/`QualityScorer` 写降级值、`AiFlavorScorer` 不依赖外部必写），`ContentAssembler` 的 `waitAll` 五键终能全就绪、组装触发，流水线不超时

#### Scenario: 红线——新键无生产者或 watch 错接致死锁（反例）

- **WHEN** 新增某键但无任何角色写它、或某 `waitAll` 依赖键的生产者在失败时不写键、或 `watchKeys` 指向不存在 / 永不写入的键
- **THEN** MUST 视为缺陷、不予合入（每个 `waitAll` 依赖键必须有保证写入的唯一生产者，杜绝流水线死锁超时）
