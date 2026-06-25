## MODIFIED Requirements

### Requirement: 配图链路决策与执行解耦（ImagePlanner / ImageGenerator）

配图链路 SHALL 拆为**三个**独立角色，决策与执行解耦、两类决策再分职：`ImageSetPlanner`（图集选题，**决策**）watch `createdContent` 决定要不要图 / 张数 / 每张主题 / 风格倾向，写新键 `imageSetPlan`；`ImagePromptComposer`（配图指令，**决策**）watch `imageSetPlan` 把每个主题翻成一条万相 prompt（共享固定风格基底），写键 `imagePlan`（`imagePrompts: string[]` / `imageStyle` / `imageCount` / `fallbackStrategy`）；`ImageGenerator`（**执行**）watch `imagePlan` 逐张调通义万相（复用现有 `WanxiangClient` / `ImageProvider`）生成 URL，写 `imageDirective`（`imageUrls: string[]`）。生图失败那张 `ImageGenerator` MUST 如实不计入 `imageUrls`（不补空、不复用上次 URL、不伪造）；全失败时按 `fallbackStrategy` 如实表示无图。两个决策角色（`ImageSetPlanner` / `ImagePromptComposer`）MUST NOT 调图源；只有 `ImageGenerator` 调图源。单个角色 MUST NOT 同时承担"配图决策"与"调图源生图"，且决策侧 MUST NOT 由一个角色同时承担"选题"与"话术指令"。

#### Scenario: 选题、指令、生图分属三角色、各自可独立单测

- **WHEN** `createdContent` 就绪、流水线进入配图链路
- **THEN** `ImageSetPlanner` 先 watch `createdContent` 产出 `imageSetPlan`（含 `wantImage` / `imageCount` / `themes` / `styleHint`），`ImagePromptComposer` 再 watch `imageSetPlan` 产出 `imagePlan`（含 `imagePrompts` / `imageStyle` / `imageCount` / `fallbackStrategy`），`ImageGenerator` 再 watch `imagePlan` 产出 `imageDirective`（`imageUrls`）；为 `ImageGenerator` 写单测只需桩图源、为两个决策角色写单测只需桩各自 LLM

#### Scenario: 计划不配图时直接产空 directive

- **WHEN** `imagePlan.wantImage === false` 或 `imagePlan.imagePrompts` 为空
- **THEN** `ImageGenerator` 不调图源，直接写 `imageDirective` 且 `imageUrls` 为空数组、`fallbackStrategy` 为 `imagePlan.fallbackStrategy`，如实表示"本帖无图"

#### Scenario: 逐张生图失败如实不计入且不伪造

- **WHEN** `imagePlan.wantImage === true`，逐张生成中某张 `imageProvider.generate` 返回空 URL / 抛错
- **THEN** `ImageGenerator` 跳过该张（不进 `imageUrls`、不补空、不复用别张），继续其余张；最终 `imageUrls` 仅含真实成功 URL，全链不出现伪造图

#### Scenario: 红线——生图失败谎报有图或决策角色调图源（反例）

- **WHEN** 任一实现在生图失败后把占位 / 复用 URL 写进 `imageUrls`，或让 `ImageSetPlanner` / `ImagePromptComposer` 直接调图源，或一个决策角色同时做"选题 + 话术指令"
- **THEN** MUST 视为违规、不予合入（生图失败如实不计入、决策不碰图源、选题与话术指令分属两角色）

### Requirement: CoverSelector 选封面

流水线 SHALL 以独立角色 `CoverSelector` 从生成图中选封面，watch `imageDirective` 产出新键 `coverSelection { imageUrls, hasCover, selectedAt }`：读 `imageDirective.imageUrls`，**恒取首张**（`imageUrls[0]`，成功序列的钩子图）为封面，`hasCover = imageUrls.length > 0`。无图（`imageUrls` 为空）时 `CoverSelector` MUST 如实产出 `{ imageUrls: [], hasCover: false }`，使组装后封面为 `null`；MUST NOT 在无图时静默选占位图或谎报 `hasCover: true`。本期 MUST NOT 引入封面索引字段、MUST NOT 改动下发侧 `set_cover` 触发条件（选非首图当封面 / 美学或 LLM 选封面留待后续 change）。该角色 SHALL 为可演进的真实角色，MUST NOT 在别处硬编码"一律首图"而绕过。

#### Scenario: 多图恒取首张为封面

- **WHEN** `imageDirective.imageUrls` 含 M(≥1) 张有效 URL
- **THEN** `CoverSelector` 产出 `coverSelection { imageUrls: <该数组>, hasCover: true }`，封面取 `imageUrls[0]`，组装时封面字段取该首张 URL

#### Scenario: 无图诚实回报空封面

- **WHEN** `imageDirective.imageUrls` 为空（无图 / 全部生图失败降级）
- **THEN** `CoverSelector` 产出 `coverSelection { imageUrls: [], hasCover: false }`，组装后封面为 `null`，如实表示"无封面"

#### Scenario: 本期不引入封面索引、不改 set_cover 触发

- **WHEN** 审视封面选择与下发
- **THEN** `coverSelection` 不含封面索引字段、命令序列 `set_cover` 触发条件保持仅 `images.length > 1`（平台默认首图即封面），非首图封面策略留待后续 change

#### Scenario: 红线——无图谎报有封面（反例）

- **WHEN** 任一实现在无图时仍把封面写成占位图、或把 `hasCover` 写为 `true`，或在别处硬编码"一律首图"绕过 `CoverSelector`
- **THEN** MUST 视为违规、不予合入（无封面必须如实回报，封面选择必须经专职角色）

### Requirement: ContentAssembler 瘦身但产出同形 assembledContent（稳定边界、下游零改动）

`ContentAssembler` SHALL 瘦身为**纯组装**角色：`watchAll`（`waitAll: true`）`cleanedContent` / `aiFlavorScore` / `qualityReport` / `imageDirective` / `coverSelection` 就绪后仅做字段拼装，MUST NOT 再持有 `llmClient` / `postProcessor`、MUST NOT 做任何 LLM 调用或外部 IO。它 SHALL 产出 `assembledContent`，字段为 `{ finalContent, finalTags, imageUrls, imageUrl, aiScore, qualityScore, rewritten, flaggedPhrases, assembledAt }`：`imageUrls` ← `coverSelection.imageUrls`（上传全集），`imageUrl` ← 封面（`imageUrls[0] ?? null`，保留为向后兼容的单数派生字段）。除多图能力显式新增的 `imageUrls` 外，其余字段集 / 语义与细拆前一致。下游 `PublishExecutor` 因多图能力 SHALL 读 `imageUrls` 下发上传全集（这是新能力的预期扩展，非历史细拆所禁的静默改形）；`ApprovalGatekeeper`（watch `assembledContent`）MUST NOT 因字段拼装方式而改注册。本要求 MUST NOT 触及协议或 edge。

#### Scenario: 瘦身后仅组装、无 LLM / 无 IO

- **WHEN** `cleanedContent` / `aiFlavorScore` / `qualityReport` / `imageDirective` / `coverSelection` 五键全部就绪
- **THEN** `ContentAssembler` 仅做字段映射（`finalContent ← cleanedContent.content`、`finalTags ← createdContent.tags`、`imageUrls ← coverSelection.imageUrls`、`imageUrl ← imageUrls[0] ?? null`、`aiScore ← aiFlavorScore.aiScore`、`qualityScore ← qualityReport.qualityScore`、`rewritten`/`flaggedPhrases ← cleanedContent`），其依赖中不含 `llmClient` / `postProcessor`

#### Scenario: 多图能力新增 imageUrls 字段、其余形状不变

- **WHEN** 重组后的生产段跑完、`ContentAssembler` 写出 `assembledContent`
- **THEN** `assembledContent` 含 `finalContent` / `finalTags` / `imageUrls` / `imageUrl` / `aiScore` / `qualityScore` / `rewritten` / `flaggedPhrases` / `assembledAt`；`imageUrls` 为上传全集、`imageUrl` 为封面（首张派生），其余字段语义与细拆前等价

#### Scenario: 下游消费方按多图能力读取

- **WHEN** 一轮发布流水线在多图能力下完整跑通
- **THEN** `ApprovalGatekeeper` 仍 watch `assembledContent`、`PublishExecutor` 仍 watch `gateDecision`；`PublishExecutor` 读 `assembledContent.imageUrls` 下发上传全集、读封面字段下发 `cover`，端到端结果（`gateDecision` / `publishResult`）形状与单图等价

#### Scenario: 红线——细拆波及协议或越界改形（反例）

- **WHEN** 任一改动改了 `assembledContent` 除 `imageUrls` 外的字段集 / 字段名 / 字段语义，或触及协议 / edge
- **THEN** MUST 视为越界、不予合入（稳定边界 `assembledContent` 除本 change 显式新增 `imageUrls` 外不可破，多图能力 MUST NOT 触及协议 / edge）
