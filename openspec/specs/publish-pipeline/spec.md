# publish-pipeline Specification

## Purpose
TBD - created by archiving change dedicated-title-creator-role. Update Purpose after archive.
## Requirements
### Requirement: 标题由独立角色在正文定稿后生成

系统 SHALL 以一个独立角色 `TitleCreator`（角色 id `publish:TitleCreator`）生成发帖标题，与内容生成解耦以避免单次 LLM 调用的注意力稀释。该角色 MUST `watchKeys=['assembledContent']`，以**最终定稿正文** `assembledContent.finalContent` 为输入（MUST NOT 取草稿 `createdContent.content`——正文经去 AI 味环节改写后才定稿，标题须忠于真正发出的文字），单次短提示产出一个 ≤18 可见字符的钩子标题，写入新黑板字段 `titleSelection`（`{title, source:'llm'|'derived', decidedAt}`）。`source` MUST 如实标注：LLM 真产出为 `'llm'`，任何派生/兜底为 `'derived'`，MUST NOT 把派生标题标为 `'llm'`。同理，话题亦自 `ContentCreator` 解耦：`ContentCreator` 自话题拆分能力起 SHALL 仅产出正文（及 tone / style），MUST NOT 再产出标签，标题由 `TitleCreator`、话题由 `TopicGenerator` 各自独立调用产出。

#### Scenario: 正文定稿后激活、据定稿正文产出标题
- **WHEN** `ContentAssembler` 写出 `assembledContent`（含 `finalContent`）
- **THEN** `TitleCreator` 激活，读 `assembledContent.finalContent` 单独生成一个 ≤18 字标题，写入 `titleSelection`，`source='llm'`

#### Scenario: 取定稿正文而非草稿
- **WHEN** 去 AI 味环节把草稿里的某句话删改、`finalContent` 与 `createdContent.content` 不一致
- **THEN** `TitleCreator` 据 `finalContent`（真正发出的版本）拟标题，标题不引用已被删改的草稿句子

#### Scenario: 标题、正文、话题分多次 LLM 调用
- **WHEN** 生成一篇帖子
- **THEN** 正文由 `ContentCreator` 一次调用产出（**仅正文**，不含标题、不含标签）、标题由 `TitleCreator`、话题由 `TopicGenerator` 各自另次调用产出；标题与话题 MUST NOT 再作为「标题+正文+标签」单次 JSON 里被稀释的子字段

### Requirement: 标题生成失败则发布失败且绝不造假标题

`TitleCreator` 失败（LLM 调用失败 / 超时 / 多次重试后仍不合规）时系统 MUST 判该次发布失败，MUST NOT 派生或编造一个标题去顶替继续发布。角色失败策略为 `abort`：失败时**不写 `titleSelection`**，下游发布因缺该字段而不激活、本次流水线判 `failed`。角色默认 `timeoutMs` MUST ≥ 单次模型调用天花板（当前 ≥180000）且经 env 可调，并把该超时同传进标题生成的模型调用（不短于模型预算）。失败 MUST 即时冒泡为流水线失败，MUST NOT 让流水线干等到 `pipelineTimeoutMs` 才超时。

#### Scenario: 标题 LLM 失败则不发布、判失败
- **WHEN** `TitleCreator` 的 LLM 调用连续失败、重试用尽
- **THEN** 不写 `titleSelection`，`PublishExecutor` 不激活、不下发任何发布指令，本次流水线判 `failed`

#### Scenario: 红线反例——派生假标题顶替（禁止）
- **WHEN** 标题生成失败，有实现想用「正文首行切一段」当标题继续发布
- **THEN** 这违反「失败=发布失败、不造假标题」，MUST 被拒绝；正确行为是判失败、不发布

#### Scenario: 失败即时判定不挂死
- **WHEN** `TitleCreator` `abort`
- **THEN** 流水线即时收敛为 `failed`（与 `ContentCreator` 现有 `abort` 行为一致），MUST NOT 干等到 `pipelineTimeoutMs`

### Requirement: 发布严格接在标题就绪事件之后

`PublishExecutor` MUST 在「审批门结论 + 标题就绪」两个事件都满足后才激活：`watchKeys=['gateDecision','titleSelection']` 且 `waitAll:true`。由此发送飞书人审卡片时标题 MUST 已生成，审批卡标题栏 MUST 取自 `titleSelection.title`（真实标题），MUST NOT 在标题缺失时发出卡片或发布。

#### Scenario: 标题就绪才发布
- **WHEN** `gateDecision` 与 `titleSelection` 均写出
- **THEN** `PublishExecutor` 激活，先发飞书审批卡、人审通过后下发发布序列

#### Scenario: 审批卡显示真实标题
- **WHEN** `PublishExecutor` 发送飞书人审卡片
- **THEN** 卡片标题栏为 `titleSelection.title`（真正会发出的 ≤18 字标题），而非正文首行派生值；人工「通过」即认可该真实标题+正文+配图

#### Scenario: 标题缺失则审批卡不发、不发布
- **WHEN** `titleSelection` 因标题 `abort` 而从未写出
- **THEN** `PublishExecutor` 不激活，既不发审批卡也不发布（无「标题缺失」的卡片）

### Requirement: 标题长度收口云端一处且记录等于真实发布

标题长度 MUST 在云端**一处**收敛到 ≤18 可见字符，且为字形安全截断：MUST 用按 grapheme 的计数与边界回退（`title-clamp.ts` 的 `clampTitle`），超长时回退到最近词/标点边界、无边界则硬切到 18，**MUST NOT 返回空串**、MUST NOT 从汉字词或 emoji 代理对中间盲切。被收敛后的同一个标题值 MUST 同时用于：`publish_log` 写入、下发 edge 的 `fill_field(title)`、飞书审批卡、以及 `manual_review`/`abort` 状态记录——做到记录==下发==审批卡==真实发布。edge MUST NOT 对标题再做任何截断或策略处理，只原样填入云端下发的标题；edge 填入失败按真实结果如实回报。

#### Scenario: 字形安全截断、不返空
- **WHEN** 标题为 25 个连续汉字、无空格/标点边界
- **THEN** `clampTitle` 返回恰 18 个 grapheme 的非空标题，不从某个汉字中间或 emoji 中间切断

#### Scenario: 记录等于真实发布
- **WHEN** 一次发布成功
- **THEN** `publish_log.title`、下发 edge 的标题、飞书审批卡标题三者为同一个 ≤18 字字符串，等于平台上真正显示的标题

#### Scenario: 红线反例——记录与真发不一致（禁止）
- **WHEN** 有实现让云端存全长标题、靠 edge 盲切到 20 才发布
- **THEN** 这造成 `publish_log` 记录 ≠ 真实发布（失真红线），MUST 被拒绝；长度收口 MUST 发生在 DB 写入与下发之前

#### Scenario: edge 不做标题策略
- **WHEN** edge 收到 `fill_field(title)` 指令
- **THEN** edge 原样把云端标题填入发布页，不截断、不改写；若填入后置校验失败则回 `ok:false` 与真实 error，MUST NOT 自行裁剪标题去"修复"

### Requirement: 标题角色模型可后台独立配置且零回归回落

`TitleCreator` MUST 经按角色取模型通道调用（`roleLlm('publish:TitleCreator')` + `RoleConfigStore`），并在角色目录登记，使管理后台「角色配置页」可独立配置其文本模型与温度。未配置时 MUST 零回归回落全局默认模型（当前 qwen3.7-max），MUST NOT 因缺 `role_config` 行而 brick。

#### Scenario: 未配置回落全局
- **WHEN** `role_config` 无 `publish:TitleCreator` 行
- **THEN** `TitleCreator` 用全局默认模型/温度调用，行为零回归

#### Scenario: 后台独立配置生效
- **WHEN** 运营在「角色配置页」给 `publish:TitleCreator` 设一个模型/温度
- **THEN** 该角色后续调用用所配模型/温度，不影响其他角色

### Requirement: 配图链路决策与执行解耦（ImagePlanner / ImageGenerator）

配图链路 SHALL 拆为**三个**独立角色，决策与执行解耦、两类决策再分职：`ImageSetPlanner`（图集选题，**决策**）watch `createdContent` 决定要不要图 / 张数 / 每张主题 / 风格倾向，写新键 `imageSetPlan`；`ImagePromptComposer`（配图指令，**决策**）watch `imageSetPlan` 把每个主题翻成一条万相 prompt（共享固定风格基底），写键 `imagePlan`（`imagePrompts: string[]` / `imageStyle` / `imageCount` / `fallbackStrategy`）；`ImageGenerator`（**执行**）watch `imagePlan` **并行**调通义万相（复用现有 `WanxiangClient` / `ImageProvider`）生成 URL，写 `imageDirective`（`imageUrls: string[]`）。生图失败那张 `ImageGenerator` MUST 如实不计入 `imageUrls`（不补空、不复用上次 URL、不伪造）；全失败时按 `fallbackStrategy` 如实表示无图。两个决策角色（`ImageSetPlanner` / `ImagePromptComposer`）MUST NOT 调图源；只有 `ImageGenerator` 调图源。单个角色 MUST NOT 同时承担"配图决策"与"调图源生图"，且决策侧 MUST NOT 由一个角色同时承担"选题"与"话术指令"。

#### Scenario: 选题、指令、生图分属三角色、各自可独立单测

- **WHEN** `createdContent` 就绪、流水线进入配图链路
- **THEN** `ImageSetPlanner` 先 watch `createdContent` 产出 `imageSetPlan`（含 `wantImage` / `imageCount` / `themes` / `styleHint`），`ImagePromptComposer` 再 watch `imageSetPlan` 产出 `imagePlan`（含 `imagePrompts` / `imageStyle` / `imageCount` / `fallbackStrategy`），`ImageGenerator` 再 watch `imagePlan` 产出 `imageDirective`（`imageUrls`）；为 `ImageGenerator` 写单测只需桩图源、为两个决策角色写单测只需桩各自 LLM

#### Scenario: 计划不配图时直接产空 directive

- **WHEN** `imagePlan.wantImage === false` 或 `imagePlan.imagePrompts` 为空
- **THEN** `ImageGenerator` 不调图源，直接写 `imageDirective` 且 `imageUrls` 为空数组、`fallbackStrategy` 为 `imagePlan.fallbackStrategy`，如实表示"本帖无图"

#### Scenario: 单张生图失败如实不计入且不伪造

- **WHEN** `imagePlan.wantImage === true`，并行生成中某张 `imageProvider.generate` 返回空 URL / 抛错
- **THEN** `ImageGenerator` 跳过该张（不进 `imageUrls`、不补空、不复用别张），其余张不受影响；最终 `imageUrls` 仅含真实成功 URL，全链不出现伪造图

#### Scenario: 红线——生图失败谎报有图或决策角色调图源（反例）

- **WHEN** 任一实现在生图失败后把占位 / 复用 URL 写进 `imageUrls`，或让 `ImageSetPlanner` / `ImagePromptComposer` 直接调图源，或一个决策角色同时做"选题 + 话术指令"
- **THEN** MUST 视为违规、不予合入（生图失败如实不计入、决策不碰图源、选题与话术指令分属两角色）

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

`ContentAssembler` SHALL 瘦身为**纯组装**角色：`watchAll`（`waitAll: true`）`cleanedContent` / `aiFlavorScore` / `qualityReport` / `imageDirective` / `coverSelection` 就绪后仅做字段拼装，MUST NOT 再持有 `llmClient` / `postProcessor`、MUST NOT 做任何 LLM 调用或外部 IO。它 SHALL 产出 `assembledContent`，字段为 `{ finalContent, finalTags, imageUrls, imageUrl, aiScore, qualityScore, rewritten, flaggedPhrases, assembledAt }`：`imageUrls` ← `coverSelection.imageUrls`（上传全集），`imageUrl` ← 封面（`imageUrls[0] ?? null`，保留为向后兼容的单数派生字段）。**自话题拆分能力起，`finalTags` 恒为 `[]`**——话题改由独立 `TopicGenerator` / `TopicEvaluator` 产出、经 `publishMetadata.topics` 落地并成为唯一真源，`finalTags` 不再承载笔记话题；这是话题拆分能力显式许可的语义变更（与多图能力显式新增 `imageUrls` 同类的预期演进），MUST NOT 被读作历史细拆所禁的静默改形。除此显式变更外，其余字段集 / 语义与细拆前一致。下游 `PublishExecutor` 因多图能力 SHALL 读 `imageUrls` 下发上传全集；`ApprovalGatekeeper`（watch `assembledContent`）MUST NOT 因字段拼装方式而改注册。本要求 MUST NOT 触及协议或 edge。

#### Scenario: 瘦身后仅组装、无 LLM / 无 IO

- **WHEN** `cleanedContent` / `aiFlavorScore` / `qualityReport` / `imageDirective` / `coverSelection` 五键全部就绪
- **THEN** `ContentAssembler` 仅做字段映射（`finalContent ← cleanedContent.content`、`finalTags ← createdContent.tags`（因 `createdContent.tags` 自话题拆分起恒 `[]`，`finalTags` 恒 `[]`）、`imageUrls ← coverSelection.imageUrls`、`imageUrl ← imageUrls[0] ?? null`、`aiScore ← aiFlavorScore.aiScore`、`qualityScore ← qualityReport.qualityScore`、`rewritten`/`flaggedPhrases ← cleanedContent`），其依赖中不含 `llmClient` / `postProcessor`

#### Scenario: 多图能力新增 imageUrls 字段、其余形状不变

- **WHEN** 重组后的生产段跑完、`ContentAssembler` 写出 `assembledContent`
- **THEN** `assembledContent` 含 `finalContent` / `finalTags` / `imageUrls` / `imageUrl` / `aiScore` / `qualityScore` / `rewritten` / `flaggedPhrases` / `assembledAt`；`imageUrls` 为上传全集、`imageUrl` 为封面（首张派生），`finalTags` 恒 `[]`（话题移交独立角色），其余字段语义与细拆前等价

#### Scenario: 下游消费方按多图能力读取

- **WHEN** 一轮发布流水线在多图能力下完整跑通
- **THEN** `ApprovalGatekeeper` 仍 watch `assembledContent`、`PublishExecutor` 仍 watch `gateDecision`；`PublishExecutor` 读 `assembledContent.imageUrls` 下发上传全集、读封面字段下发 `cover`，读 `publishMetadata.topics` 作为话题真源，端到端结果（`gateDecision` / `publishResult`）形状与单图等价

#### Scenario: 红线——细拆波及协议或越界改形（反例）

- **WHEN** 任一改动改了 `assembledContent` 除 `imageUrls`（多图能力显式新增）/ `finalTags` 恒空（话题拆分能力显式许可）外的字段集 / 字段名 / 字段语义，或触及协议 / edge
- **THEN** MUST 视为越界、不予合入（稳定边界 `assembledContent` 除各能力显式许可的变更外不可破，且 MUST NOT 触及协议 / edge）

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

### Requirement: 发布须与浏览会话互斥（让位），不计时也不被并发浏览撞页

发布的**下发段**（人审通过后驱动边缘的指令序列：导航 / 配图 / 填写 / 提交）SHALL 与浏览会话互斥并独占边缘（一边缘一 Chrome，物理不可并行），且让位 MUST 仅发生在下发段、绝不发生在生成候审段。**仅在下发段开始**时，云端 MUST 先**干净结束该账号当前浏览会话**
（标记为不可续场，**不触发自动休息/续场**），使下发独占该边缘运行；下发期间 MUST NOT 有并发浏览会话向
同一边缘下发浏览命令。下发**结束**（无论成功 / 失败 / 中止 / 异常，均经下发段的唯一保证终止点）后，云端
SHALL 起一场**全新浏览会话**（须过续场各闸：调度开关 / 人设 / 活跃时段 / 每日上限 / 风控）。下发所耗时间
MUST NOT 计入任何浏览会话的单场时长。

发布的**生成候审段**（生成终稿 + 落库草稿 + 发审批卡 + 等待人审）**MUST NOT** 让位：该段不结束浏览会话、
不独占边缘，浏览在生成与候审全程照常进行（见「生成候审期间不让位浏览」requirement）。让位若因该账号已有
下发在跑而被跳过（未真正开始下发），MUST NOT 结束浏览会话。

#### Scenario: 仅下发段开始才结束并发浏览会话
- **WHEN** 某账号的草稿人审通过、进入下发段，且该账号当前有活跃浏览会话
- **THEN** 云端先结束该浏览会话（标记不可续场、不安排休息），下发独占边缘运行，下发期间 MUST NOT 有浏览命令下发到该边缘

#### Scenario: 生成与候审期间不结束浏览会话
- **WHEN** 某账号触发发布、正在云端生成终稿或等待人审，且该账号当前有活跃浏览会话
- **THEN** 云端 MUST NOT 结束该浏览会话、MUST NOT 让位；浏览照常进行，直到该草稿被授权进入下发段才让位

#### Scenario: 下发结束后起新浏览会话
- **WHEN** 下发走完任一终止路径（成功 / 失败 / 中止 / 异常）
- **THEN** 云端经续场各闸起一场全新浏览会话；各闸不过（如超出活跃时段 / 达每日上限 / 风控受限）则诚实不起、MUST NOT 强行重开

#### Scenario: 被跳过的下发不动浏览会话
- **WHEN** 某账号已有下发在跑、又一份授权到达欲下发、本次被跳过（未真正开始）
- **THEN** 云端 MUST NOT 结束当前浏览会话（那次未开始的下发不占用边缘）

#### Scenario: 下发让位的最坏故障是诚实暂停而非撞页
- **WHEN** 下发结束信号异常缺失（保证终止点未能起新会话）
- **THEN** 系统 MUST 停在「无浏览会话」的诚实暂停态（待边缘重连或运营介入），MUST NOT 让浏览会话在下发途中把边缘拽回 feed 造成撞页

### Requirement: 发布拆分为生成候审段与下发段，生成候审期间不让位浏览

笔记发布 SHALL 拆为两段：**生成候审段**（生成终稿 → 落库草稿 → 发飞书审批卡 → 返回）与**下发段**
（人审通过后驱动边缘指令序列上线）。生成候审段 MUST 是纯云端、不碰边缘的过程，MUST NOT 结束浏览会话、
MUST NOT 独占边缘、MUST NOT 内联阻塞等待人审；该段完成后发布编排即收敛为「待审（`pending_approval`）」
并返回，草稿耐久落库（含标题 / 正文 / 标签 / 图 URL / 元数据 / 来源血缘）。下发段 MUST 是唯一碰边缘、
唯一让位的阶段。生成段超时 MUST 只覆盖生成本身，MUST NOT 为容纳人审等待而抬高。

#### Scenario: 生成候审段不碰边缘、不让位、不阻塞等审
- **WHEN** 发布被触发、进入生成候审段
- **THEN** 云端跑生成级联、把终稿落库为 `pending_approval` 草稿、发出飞书审批卡后即返回；全程 MUST NOT 结束该账号浏览会话、MUST NOT 向边缘下发任何发布指令、MUST NOT 内联轮询等待人审

#### Scenario: 草稿耐久落库可供下发重建
- **WHEN** 生成候审段产出终稿
- **THEN** 草稿连同标题 / 正文 / 标签 / 图 URL / 元数据 / 来源血缘耐久落库，状态为 `pending_approval`，其内容足以在下发段无需重生成即重建发布输入

#### Scenario: 生成段超时只覆盖生成
- **WHEN** 配置发布生成段的超时
- **THEN** 该超时只需覆盖生成级联本身（秒至分钟量级），MUST NOT 再为「内联等待人审」预留 15 分钟级时长

#### Scenario: 红线反例——生成候审段让位或阻塞（禁止）
- **WHEN** 有实现在生成或候审阶段就结束浏览会话 / 独占边缘 / 内联阻塞等待人审
- **THEN** MUST 视为违规、不予合入；让位与边缘独占 MUST 推迟到下发段，生成候审段对浏览零影响

### Requirement: 审批通过即下发，下发从落库草稿重建、绝不重生成

人审授权信号到达即 SHALL 触发对应草稿的下发（通过即切，不等自然空档；唯一例外为该账号处于下发熔断——授权保留不烧、人工确认后恢复，见 `publish-dispatch-resilience`）。下发 MUST 从落库草稿重建发布输入（标题 / 正文 / 标签 / 图 / 元数据），下发上线的内容 MUST 与审批卡上所审的那份草稿一致；MUST NOT 在下发时重新生成内容、MUST NOT 用生成与下发之间变化后的人设 / 配置回灌或改写已定稿草稿（陈旧草稿如实照发，所见即所发）。下发时若该账号无在线边缘节点，SHALL 按零副作用失败处理：草稿回 `pending_approval`、作废该次授权信号并通知重批，MUST NOT 伪造成功、MUST NOT 静默丢弃授权、MUST NOT 把可重批的离线失败烧成终态。

#### Scenario: 授权到达即下发该草稿
- **WHEN** 某 `pending_approval` 草稿的人审授权信号（`approved === true`）到达且该账号未处于下发熔断
- **THEN** 云端即触发该草稿的下发段（让位 → 重建发布输入 → 驱动指令序列 → 回写结果），不等待自然空档

#### Scenario: 下发即所审、不重生成
- **WHEN** 一份草稿在 T0 生成定稿、T1（数小时后）才被批准
- **THEN** 下发上线的标题 / 正文 / 配图 / 元数据为 T0 定稿的那一份（与审批卡一致），MUST NOT 在 T1 重新生成或按 T1 的人设 / 配置改写

#### Scenario: 下发时边缘离线回待审可重批
- **WHEN** 授权到达、进入下发段，但该账号此刻无在线边缘节点
- **THEN** 云端不发任何指令，草稿回 `pending_approval`、该次授权信号被作废、运营被如实通知；边缘恢复后重批即可下发，MUST NOT 伪造成功或静默吞掉授权

#### Scenario: 红线反例——下发时重生成或回灌新配置（禁止）
- **WHEN** 有实现在下发时重新调用生成、或用当前人设 / 配置覆盖已落库草稿后再发
- **THEN** MUST 视为违规、不予合入；下发 MUST 忠于审批卡所审的冻结草稿（陈旧亦照发），重生成等于绕过人审所认可的内容

### Requirement: 取消发布审批超时，草稿待审无限期、绝不超时自毁或改判

发布人审 MUST 改为带外异步：发布执行 MUST NOT 内联轮询等待人审、MUST NOT 设「等待人审超时」。`pending_approval`
草稿 SHALL **无限期**等待，其终态只由两条边推进：① 人审授权（`approved === true`）→ 进入下发段；② 运营显式
否决 / 撤稿 → 进入 `rejected` / `discarded` 终态。草稿 MUST NOT 因任何超时被自动改判（如旧 `needs_review`-on-timeout）、
MUST NOT 因任何超时被自动丢弃，**更 MUST NOT** 因久未审批而自动发布（AC-PUB 不变：无 `approved === true` 则永不下发）。

#### Scenario: 久未审批草稿安静待审、不自动发不自毁
- **WHEN** 一份 `pending_approval` 草稿长时间（远超旧 15 分钟窗）无人处理
- **THEN** 草稿保持 `pending_approval` 安静等待，MUST NOT 被自动发布、MUST NOT 被自动改判 `needs_review`、MUST NOT 被自动丢弃；它是一条「待办」而非「故障」

#### Scenario: 删除内联审批轮询与超时
- **WHEN** 审视发布执行路径
- **THEN** MUST NOT 存在「发卡后在固定窗口内每隔数秒轮询授权信号、期满落 `needs_review`」的内联等待逻辑；授权的推进 MUST 由授权信号到达事件驱动

#### Scenario: 运营显式否决推进终态
- **WHEN** 运营在飞书 / 后台显式否决或撤回一份 `pending_approval` 草稿
- **THEN** 草稿进入 `rejected` / `discarded` 终态、MUST NOT 下发；这是终态推进的唯一「不发」路径，与「超时自动改判」无关

#### Scenario: 红线反例——超时自动发布或丢弃（禁止）
- **WHEN** 有实现在草稿超过某时长后自动下发，或自动删除 / 丢弃未审批草稿
- **THEN** MUST 视为违规、不予合入；无 `approved === true` 绝不下发（AC-PUB），未授权草稿只能由人审授权或运营显式否决推进，绝不由超时推进

### Requirement: 下发段按账号单飞且每账号至多一份待下发草稿

下发段 SHALL 按账号串行（同一账号同一时刻至多一次下发在跑），授权到达时若该账号已有下发在跑，本次 MUST
排队或被忽略而 MUST NOT 并发抢同一边缘。生成候审段的堆积 SHALL 由每账号在途帽约束（「生成中 + 待审」合计
有界，见 `publish-generation-concurrency`），同账号多份 `pending_approval` 草稿在帽内合法并存（多候选挑选
场景）；同一参照稿在途时 MUST NOT 并发重复生成。下发段对同一 `recordId` MUST 幂等：已 `published` 或
正在下发的 `recordId` 重复授权 MUST NOT 触发二次发布。

#### Scenario: 同账号下发串行
- **WHEN** 某账号一份草稿正在下发，另一份草稿的授权同时到达
- **THEN** 第二份的下发 MUST 排队或被跳过、MUST NOT 与第一份并发向同一边缘下发指令

#### Scenario: 帽内多候选合法并存
- **WHEN** 某账号已有两份 `pending_approval` 草稿（未达在途帽），运营对另一篇参照稿触发洗稿
- **THEN** 新一轮正常生成并落第三份待审草稿；三份草稿各自独立可批 / 可驳，下发仍按账号串行推进

#### Scenario: 下发对 recordId 幂等
- **WHEN** 同一 `recordId` 的授权信号被重复投递（重复点击 / 兜底扫描与事件双触发）
- **THEN** 已 `published` 或正在下发的 `recordId` MUST NOT 二次下发 / 二次提交，结果保持单次发布

#### Scenario: 红线反例——并发下发抢同一边缘（禁止）
- **WHEN** 有实现允许同账号两份草稿同时进入下发、并发向同一边缘下发发布指令
- **THEN** MUST 视为违规、不予合入；同账号下发 MUST 串行，杜绝两条发布序列在同一 Chrome 上交错撞页

### Requirement: 发布角色执行超时不得短于其所包裹的模型预算，总闸不得小于关键路径角色预算之和

发布角色的执行超时（`base-role` 的 `executeWithTimeout` 用 `Promise.race` 包裹 `execute()`）**不取消底层模型 HTTP 请求**——只让本角色放弃等待走 fallback。故任何**调用模型的发布角色**其有效模型预算 = min(角色执行超时, 模型调用超时)。系统 MUST 保证外层各级超时不短于其所包裹的模型预算、且总闸不小于其内容物，以避免「角色秒表先于模型答完就掐断 → 每次合法慢调用都误触降级」。具体不变量如下：

- 任何调用模型的发布角色，其**角色执行超时 MUST NOT 短于单次模型调用天花板**（见 `role-llm-config` 的构造默认天花板，当前 ≥180s），且 MUST 把该超时**同步传进底层模型调用**（`chat()/complete()` 的 `opts.timeoutMs`），使底层 HTTP 在同一时限被真正中止、不残留悬空请求。此为 `ContentScout` 已验证的范式（角色闸与模型调用超时同取一个常量），其余调用模型的角色 MUST 遵循。
- 各角色超时 SHALL 经文档化 env 旋钮可调，缺失/非法回落安全默认、绝不 brick。
- 发布**流水线总预算 MUST ≥ 关键路径上各模型角色预算之和**（容器不得小于其内容物），使总闸绝不在某个合法慢角色仍在其自身允许预算内运行时先行掐断整条流水线并丢弃已产出的模型结果。任何角色的执行超时 MUST NOT 大于流水线总预算（否则该角色的诚实降级永不可达）。
- 上述不变量 MUST NOT 削弱既有「MUST NOT 静默假成功」红线：超时后角色仍按各自 fallback 诚实降级（可见/可观测），绝不伪造成功产出。

#### Scenario: 调用模型的角色秒表不短于模型天花板且同传超时
- **WHEN** 一个调用模型的发布角色（如审批闸 / 质量评审 / 去 AI 味 / 配图规划）被激活
- **THEN** 其角色执行超时 ≥ 单次模型调用天花板，且该超时被传进底层模型调用，使一次处于合法耗时内的 thinking 调用不会被角色秒表提前掐断

#### Scenario: 合法慢调用不再误触降级
- **WHEN** 某调用模型的发布角色的模型调用耗时处于 thinking 模型合法范围内（如 60–150s）
- **THEN** 该角色等到模型正常返回并写出真实产出，MUST NOT 因角色秒表短于模型耗时而退化到降级默认

#### Scenario: 总闸不小于关键路径角色预算之和
- **WHEN** 关键路径上串行的模型角色各自在其允许预算内运行（其预算和大于旧总闸）
- **THEN** 流水线总闸 MUST 足以容纳该串行和，MUST NOT 在正文/标题等合法慢角色仍在运行时先行判 `failed` 并丢弃已付费的模型产出

#### Scenario: 红线——角色秒表短于模型预算导致每次都降级（反例）
- **WHEN** 任一调用模型的发布角色其执行超时短于单次模型调用天花板、且未把超时传进模型调用
- **THEN** MUST 视为违规、不予合入（该配置会让合法慢调用每次误触降级、并残留跑满默认超时的悬空请求）

### Requirement: 待审正文草稿可就地编辑，编辑就地改同一记录且下发照旧重读不重生成

系统 SHALL 允许对处于 `pending_approval` 状态的正文草稿就地编辑其标题、正文、可见范围、话题；编辑 MUST 就地 UPDATE **同一条** `publish_log` 记录，MUST NOT 新起草稿行、MUST NOT 触发重生成、MUST NOT 改动配图 / 来源血缘 / `account_id` / `mode` / `publishTime`。下发段 MUST 照旧从该记录重读草稿并逐字发出（保持「下发从落库草稿重建、绝不重生成」不变），从而编辑后的内容原样发布。非 `pending_approval` 状态的记录 MUST 诚实拒绝编辑（`not_pending`），绝不静默改写。

#### Scenario: 就地编辑待审草稿并原样发布
- **WHEN** 运营对一条 `pending_approval` 草稿改动标题 / 正文 / 可见范围 / 话题并保存成功
- **THEN** 系统就地 UPDATE 同一条记录、不新起草稿行、不重生成，且此后下发从该记录重读、逐字发出编辑后的内容

#### Scenario: 拒绝编辑非待审记录
- **WHEN** 目标记录已是 `published` / `failed` / `needs_review`
- **THEN** 编辑被诚实拒绝并返回可区分的 `not_pending`，记录内容不被改写

### Requirement: 每条草稿带内容版本号，作「审核所见即真实发布」的授权凭证

系统 SHALL 为每条 `publish_log` 记录维护一个每行内容版本号（`content_version`，既有行默认 0），每次成功编辑 MUST 使其自增 1。授权（通过 / 驳回）MUST 携带「人当时所见的那一版」版本号；真正触发下发的那次授权，其携带版本 MUST 等于下发那一行的当前版本——即「授权者所见字节 == 真实发布字节」按构造成立。版本一致性是唯一保真判据，签名中的来源字段仅供审计、MUST NOT 作保真闸。

#### Scenario: 编辑自增版本
- **WHEN** 一条草稿被成功编辑
- **THEN** 其 `content_version` 自增 1，并作为后续授权须携带的凭证

#### Scenario: 授权凭证锚定所见版本
- **WHEN** 运营在某一版草稿上点授权
- **THEN** 该授权携带的是当时所见的版本号，而非点击时从活缓存重取的版本

### Requirement: 下发前版本一致性闸，版本不符作废过期签名并留待审

下发段 MUST 在既有「已授权」判定之后再比对授权签名所载版本与记录当前版本：一致 → 照常下发；不一致 → MUST NOT 下发任何内容、MUST 删除该过期授权签名、并将记录**留在 `pending_approval`**（自愈回可重审，带当前内容）。版本作废 MUST NOT 落 `needs_review`、MUST NOT 自毁或改判（与「无授权绝不下发、待审无限期、绝不超时自毁」一致）。缺失版本号在飞书按钮与下发闸两处 MUST 一律当 0（部署向后兼容）。

#### Scenario: 版本一致照常下发
- **WHEN** 授权签名所载版本等于记录当前版本
- **THEN** 下发照旧从落库草稿重建并发出

#### Scenario: 版本不符作废并自愈
- **WHEN** 授权签名所载版本不等于记录当前版本（例如授权后又落了一次编辑）
- **THEN** 系统不发任何内容、删除该过期签名、记录留 `pending_approval` 可被重新审批，且不落 `needs_review`、不自毁

#### Scenario: 缺版本号部署兼容
- **WHEN** 一条部署前在飞的老审批其签名与按钮均无版本号
- **THEN** 两处一律当 0，未编辑草稿（0 == 0）照常发布，不被 deploy 卡死

### Requirement: 编辑标题仍在云端一处收口且合并授权动作遇截断须二次确认

编辑标题 MUST 仍只在云端一处跑 `clampTitle`（≤18 字素、拒空），面板 MUST NOT 写裸标题，以保「记录 == 下发 == 审批面 == 真实发布」收敛。当「保存并批准」这类合并动作把编辑与授权串起时：若收口后标题与提交标题不同（被截断），系统 MUST 中止自动批准、回显截断后的字节、要求人就该版再显式授权一次；仅当标题未被截断改变时方可自动串接授权。

#### Scenario: 编辑标题超长收口
- **WHEN** 运营把标题改到超过 18 字素
- **THEN** 云端 `clampTitle` 截断至 ≤18 字素（拒空），且截断只发生在这一处

#### Scenario: 合并动作遇截断二次确认
- **WHEN** 「保存并批准」发现收口后标题被截断
- **THEN** 自动批准被中止、回显截断后字节，人须就该版再点一次批准，绝不出现「授权的是截断前、发布的是截断后」

### Requirement: 编辑深合并元数据、保留合规字节、不重算合规棘轮

编辑 MUST 以读-改-写方式深合并 `publish_metadata`，只拼接本期可编辑的 `visibility` 与 `topics`，而 `compliance` / `permissions` / `mentions` / `location` / `collection` / `metadataScore` 等未改键 MUST 逐字保留。编辑 MUST NOT 重跑 aiEnforced 合规棘轮、MUST NOT 下调 AI 声明（本期合规不可编辑），从而与合规归一化链解耦。

#### Scenario: 深合并只动可编辑键
- **WHEN** 运营改动 `visibility` 或 `topics`
- **THEN** 系统只更新这两项，`compliance`/`permissions`/`mentions`/`location`/`collection` 前后字节一致

#### Scenario: 合规不可下调
- **WHEN** 编辑请求试图携带更低的合规声明
- **THEN** 编辑忽略合规字段、逐字保留原合规值，不重算棘轮、不下调 AI 声明

### Requirement: 配图上传经 CDP 文件输入桥并以控件成功态真实校验

边缘 `upload_image` 处理器 SHALL 经 **CDP `DOM.setFileInputFiles`** 把已下载到本机的图片喂给发布页的文件输入控件
（复用既有 `CdpClient.send`，零新依赖；自管 `DOM.enable` + `Runtime.evaluate({returnByValue:false})` 解析 `objectId`），
而非 JS 值注入（浏览器安全机制下文件输入不可被 `value` 注入）。上传后 MUST **以该控件自身的成功态（渲染出的缩略图/预览节点）做后置校验**，
经 `LocatingEngine` 定位、绑定式轮询至超时；**MUST NOT 以 `input.files.length > 0` 作为成功的充分条件**——`setFileInputFiles` 同步无条件
填充 `files`，单看它正是要规避的假成功。定位/下载/桥接/校验任一失败 MUST 回 `ok:false` + 真实分类 error（`image_url_rejected` /
`image_fetch_failed` / `image_too_large` / `image_format_unsupported` / `no_target` / `engine_error` / `image_not_attached`），
**MUST NOT 伪造 `ok:true`、MUST NOT 伪造一个 `value` 掩盖失败**。`set_cover` SHALL 经 `LocatingEngine` 的定位+点击+**封面激活态后置校验**
（断言所选图确实成为当前封面，而非仅"点到了"）。配图主路径的具体控件形状（静态隐藏 `<input type=file>` vs 懒加载/拖拽区）与成功态选择器
MUST 经一次运营机实机 CDP 校准确定后再锁定，校准前以 `no_target` 诚实回报而非猜测命中。

#### Scenario: upload_image 经 CDP 桥并校验控件成功态
- **WHEN** 边缘收到 `upload_image {imageUrl}` 且图片下载、`DOM.setFileInputFiles` 写入成功
- **THEN** 处理器 MUST 进一步等待并校验该图的控件成功态节点（缩略图/预览）真实出现后才回 `ok:true`；成功态在超时内未出现 MUST 回 `ok:false, error:'image_not_attached'`

#### Scenario: 红线反例——以 files.length 充数当成功（禁止）
- **WHEN** 有实现在 `DOM.setFileInputFiles` 返回后立即读 `input.files.length > 0` 即回 `ok:true`，未校验控件成功态
- **THEN** MUST 视为违规、不予合入；`files.length > 0` 至多是必要条件，成功 MUST 以控件自身成功态为准，否则即「静默假成功」

#### Scenario: set_cover 校验封面真激活
- **WHEN** 边缘收到 `set_cover` 并点击目标图为封面
- **THEN** 处理器 MUST 后置校验该图已处于封面激活态才回 `ok:true`；点击未改变封面态 MUST 回 `ok:false`

### Requirement: 图文全图失败诚实 failed（编辑器被传图门控）且落库回正

云端 `executePublishSequence` SHALL 如实处理配图失败，并在图文帖全图失败时诚实 `failed`、绝不假装纯文字成功。
依据 task-0 实机校准：小红书图文帖发布页编辑器被"先传图"门控——未上传任何图片前标题/正文控件根本不存在，
上传成功后 `input.files` 还会被平台清零（故 `files.length` 绝非成功依据），因此本产品的图文帖**必须有图**。
具体：`upload_image` 回 `ok:false` 或超时/异常 → 置 `imagesOk=false`、
跳过依赖该图的 `set_cover`；**请求了配图（`images` 非空）而全部失败 MUST 在进 `fill_field` 前即诚实 `failed`（`error:'all_images_failed'`），
绝不进编辑/提交假装纯文字成功**（红线）。非配图指令任一失败仍 MUST 逐步 fail-fast。`imagesOk` MUST 带回 `PublishSequenceResult`。
`set_cover` MUST **仅在多图时下发**（选哪张当封面）；**单图封面自动取该图，MUST NOT 下发 `set_cover`**——发布页无独立设封面控件，
强发会 `no_target`→fail-fast 拖垮整条发布。`PublishExecutor` 在 `imagesOk === false` 时 MUST **回正已预存的 `imageUrl`**
（标 `images_attached=false`），使 `publish_log` 不在失败/无图帖上留下"有图"假信号。
（前向兼容：未请求配图的无图流——若未来启用——仍可走"无图直发"路径，不受本条约束。）

#### Scenario: 图文全图失败 → 诚实 failed，不进编辑/提交
- **WHEN** 请求了配图，但 `upload_image` 全部回 `ok:false`（或超时）
- **THEN** sequencer MUST 置 `imagesOk=false`、不下发 `set_cover`、在 `fill_field` 前返回 `ok:false` + `failedAt.error='all_images_failed'`，绝不下发 `submit_publish`；`PublishExecutor` MUST 标 `images_attached=false`

#### Scenario: 单图不下发 set_cover，多图才下发
- **WHEN** `images.length === 1`
- **THEN** 序列 MUST NOT 含 `set_cover`（封面自动取该图）；仅当 `images.length > 1` 才下发 `set_cover` 选封面

#### Scenario: 非配图指令失败仍 fail-fast
- **WHEN** `fill_field(title/content)` 或 `set_option` 回 `ok:false`（此前配图已成功）
- **THEN** sequencer MUST 仍按既有逐步 fail-fast 停止于该步、记 `failedAt`，`imagesOk` 不被误标

#### Scenario: 红线反例——失败/无图帖留有图假信号（禁止）
- **WHEN** 配图失败，但 `publish_log` 仍保留生成的 `imageUrl` 且 `images_attached` 未回正，下游据此判定该帖"有图"
- **THEN** MUST 视为违规、不予合入；MUST 伴随 `images_attached=false` 回正，杜绝失败/无图帖被读成带图

### Requirement: 配图 URL 下载安全封套与临时文件生命周期

边缘下载配图 SHALL 施加与"来源为本方云端"相称的纵深防御（非全量 SSRF 代理）：① 仅接受 `https:`（`http:` 仅在显式测试 env 下），
拒绝 `file:` / `data:` / `blob:` / `ftp:`；② **`redirect:'error'`**（拒绝任何 3xx，防原始 URL 白名单被首跳重定向绕过到内网/本地）；
③ `Content-Length` 预检 **+ 流式累计字节上限**（Content-Length 可伪造），超限中断回 `image_too_large`；④ 以 **magic-byte** 判定
jpeg/png/webp（非扩展名 / 非仅凭 Content-Type 头），非图回 `image_format_unsupported`；⑤ `AbortController` + `AIDCP_IMAGE_DOWNLOAD_TIMEOUT_MS`
显式超时，且边缘"下载+CDP 设置+后置校验"总预算 MUST **低于云端单指令超时**，确保慢/过期 URL 时边缘先返回干净 `ok:false` 而非把整条序列拖到云端超时中断；
⑥ 临时文件 MUST 用 `mkdtemp` + 随机名落在专用 `os.tmpdir()/aidcp-img-*` 前缀（非可预测静态路径），`finally` 必清理，并在启动时清扫该前缀的崩溃残留
（单一前缀，MUST NOT 触碰同机 isales 或其它 tmp）。文档/日志 MUST NOT 记录密钥或敏感值，只记路径约定。

#### Scenario: 过期/慢 URL 在云端超时前先返回降级
- **WHEN** DashScope 图 URL 已过期或下载缓慢
- **THEN** 边缘 MUST 在云端单指令超时前因 `AIDCP_IMAGE_DOWNLOAD_TIMEOUT_MS` 触发 `image_fetch_failed` 回 `ok:false`，由云端按配图降级处理，而非拖致整条序列被云端超时中断

#### Scenario: 重定向与非图被拒
- **WHEN** 图 URL 返回 3xx 重定向，或响应体非 jpeg/png/webp magic-byte
- **THEN** 下载 MUST 分别因 `redirect:'error'` 与 magic-byte 校验失败回 `ok:false`（`image_fetch_failed` / `image_format_unsupported`），绝不把重定向目标或非图字节喂给文件输入

#### Scenario: 临时文件清理与崩溃残留回收
- **WHEN** 一次 `upload_image` 完成（成功或失败），以及边缘进程崩溃后重启
- **THEN** 当次临时文件 MUST 在 `finally` 清理；重启时 MUST 清扫 `os.tmpdir()/aidcp-img-*` 前缀残留，且清扫范围 MUST NOT 越出该前缀

### Requirement: v1 整页路径带图显式改道而非静默丢弃

v1 整页发布路径（无上传步骤）收到带图 payload 时 SHALL **显式报错改道指令驱动路径**，MUST NOT 再返回
`images are not supported in phase one` 硬拒、更 MUST NOT 静默丢图后按纯文字假成功。本 change MUST NOT 在近废弃的 v1 路径内新建上传能力、
亦不整体删除 v1（属另案）。

#### Scenario: v1 带图改道指令路径
- **WHEN** v1 `publishPost` 收到 `images.length > 0`
- **THEN** MUST 回 `ok:false` 并显式指向指令驱动路径（配图经 `upload_image` 处理），MUST NOT 静默丢图、MUST NOT 假报成功

#### Scenario: 红线反例——v1 静默丢图后假成功（禁止）
- **WHEN** v1 路径丢弃 `images` 后仍按纯文字返回 `ok:true`
- **THEN** MUST 视为违规、不予合入；带图在 v1 MUST 显式失败改道，绝不静默降级伪装成功

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

### Requirement: 内容生成人设驱动且话题中立

发布内容生成（正文创作 system 与 user prompt，以及选题侦察 / 标题 / 话题 / 质量评分等各脚手架 prompt）SHALL 以账号绑定的人设为准，MUST NOT 硬编码任何特定领域框定（如「技术帖」「技术博主」「小林」等）。正文创作 SHALL 使用管线已传入的账号人设（`trigger.generateInput.soul`），与标题角色一致；脚手架措辞 SHALL 使用领域中立的「笔记」，领域由人设决定。few-shot 范文 MUST NOT 绑定单一领域（如全为技术示例）。

#### Scenario: 内容随人设领域变化

- **WHEN** 账号人设为某非技术领域（如美食），触发发布并生成正文
- **THEN** 生成的正文与标题体现该账号人设的领域与语气，不含「技术帖 / 技术博主」等被写死的技术框定

#### Scenario: 正文创作使用真实人设而非写死默认

- **WHEN** 正文创作角色构建 prompt
- **THEN** prompt 取自 `trigger.generateInput.soul` 的账号人设，而非硬编码的固定人设字符串

#### Scenario: 脚手架话题中立

- **WHEN** 选题侦察 / 标题 / 话题 / 质量评分等 prompt 被构建
- **THEN** 其措辞为领域中立的「笔记」，不出现写死的「技术帖」，领域交由人设体现

### Requirement: 无人设不得发布且不以默认人设代偿

发布管线在账号无绑定人设时 SHALL 以 `no_persona` 诚实拒绝，MUST NOT 回落到任何默认/兜底人设生成内容（红线：不静默假成功）。

#### Scenario: 无人设发布被拒且不生成内容

- **WHEN** 对未绑定人设的账号触发发布
- **THEN** 管线以 `no_persona` 拒绝，不生成正文/标题，不使用任何替代人设代偿

### Requirement: 通用参数化发布指令协议与三处同步

系统 SHALL 通过一对通用消息驱动发帖执行层：`publish.command`（cloud → edge，payload `{recordId, seq, kind, params, timeoutMs?, reason?}`）下发单条参数化原子指令，`publish.command.result`（edge → cloud，payload `{recordId, seq, kind, ok, value?, error?, details?}`）回报单条执行结果。`kind` MUST 为枚举 `PublishCommandKind`，覆盖 A 的 E1-E10：`navigate_entry` / `select_mode` / `upload_image` / `set_cover` / `fill_field` / `add_with_candidate` / `set_option` / `set_schedule` / `submit_publish` / `capture_postId`。协议 MUST 采用「一条通用消息 + `kind` 参数」而非「每个 `kind` 一条消息」，新增消息计数 MUST 恰为 +2（两份 `protocol.ts` 的 `MessageType` 由 47 增至 49）。两份 `src/comm/protocol.ts` MUST 逐字一致，`aidcp-cloud/src/comm/command-bridge.ts` 映射与 `docs/protocol.md`（头部计数 + §2 表 + kind 枚举说明）MUST 同步登记，漂移由 `Record<MessageType,true>` 穷举与 `AC-PROTO-*` 守护暴露。

#### Scenario: 一条通用消息承载所有 kind
- **WHEN** cloud 需要让边缘执行 `fill_field` 与随后的 `submit_publish`
- **THEN** 两步都用同一条 `publish.command` 下发、靠 `kind` 与 `params` 区分，`MessageType` 不为每个 kind 各加一条；两份 `protocol.ts` 的消息总数为 49 且逐字一致，`npm run typecheck` 的穷举守护通过

#### Scenario: 后续新增 kind 不动消息定义
- **WHEN** 后续阶段需支持一个新的执行原子（如某新表单控件）
- **THEN** 只扩 `PublishCommandKind` 枚举与 `PublishCommandParams` 联合类型，`MessageType` 与消息计数维持 49 不变，`publish.command` / `publish.command.result` 两条消息定义不动

#### Scenario: 红线反例——每 kind 一条消息（禁止）
- **WHEN** 有人为 E1-E10 各新增一条独立 `MessageType`（如 `publish.fill_field` / `publish.submit` …）使消息数变成 57
- **THEN** 这违反「一条通用消息 + kind」参数化哲学，MUST 被拒绝；正确做法是仅扩 `PublishCommandKind` 枚举与 `params` 联合类型、消息数维持 49

#### Scenario: 协议三处同步缺一即失败
- **WHEN** 只改了 cloud `protocol.ts` 新增两条消息，未同步 edge `protocol.ts` / `command-bridge` / `docs/protocol.md`
- **THEN** `npm run typecheck` 的 `Record<MessageType,true>` 穷举守护与 `AC-PROTO-*` 报漂移、构建失败，MUST NOT 合并

### Requirement: 边缘指令运行时逐条执行并每条后置校验如实回报

边缘 SHALL 以 `PublishCommandDispatcher` 逐条分发 `publish.command`：每个 `kind` 对应一个参数化处理器，处理器 MUST 复用既有 `LocatingEngine`（`resolveAndAct` 与三道闸：后置校验、重试上限 + 升级、反污染回写）完成「定位 + 原子操作 + 后置校验」，MUST NOT 在发布层另起一套硬编码整页流程绕开定位引擎。每条指令执行后边缘 MUST 按真实结果回报一条对应 `recordId+seq` 的 `publish.command.result`：成功带 `ok:true` 与 `value`，失败带 `ok:false` 与真实 `error`（如 `no_target` / `post_validation_failed`），`details` 带 `actionId/outcome/attempts`。

#### Scenario: 逐条执行逐条回报
- **WHEN** cloud 依次下发 `navigate_entry`、`fill_field(title)`、`fill_field(content)`
- **THEN** 边缘 `PublishCommandDispatcher` 逐条分发到对应处理器，每条经 `LocatingEngine` 定位 + 操作 + 后置校验后回一条带相同 `recordId+seq` 的 `publish.command.result`，`ok/value/error` 反映该条真实结果

#### Scenario: 处理器复用而非绕开定位引擎
- **WHEN** 实现 `fill_field` 处理器
- **THEN** 它构造 `ActionRequest` 交 `LocatingEngine.resolveAndAct` 执行、用 validator 做后置校验、继承三道闸（缓存反污染的 stage→confirm、重试上限→escalated），而非自写 `querySelector` + 直填的整页脚本

#### Scenario: 后置校验失败如实回报
- **WHEN** `fill_field` 执行后读 DOM 校验不到刚填入的内容（后置校验失败）
- **THEN** 边缘回报 `publish.command.result {ok:false, error:'post_validation_failed'}`，`details` 带 `actionId/outcome/attempts`，MUST NOT 回报 `ok:true`

#### Scenario: 红线反例——谎报成功（禁止）
- **WHEN** 某指令找不到目标元素或后置校验失败
- **THEN** 边缘 MUST NOT 伪造 `ok:true` 或用 `count||1` 等兜底掩盖失败；MUST 回报 `ok:false` 与真实 `error`（如 `no_target` / `post_validation_failed`），自愈不自残

### Requirement: 云端 CommandSequencer 编排有序指令并诚实驱动

云端 SHALL 新增 `CommandSequencer`，把「终稿 +（占位）元数据」经 `buildCommandSequence` 编排成有序指令序列，并以 `executePublishSequence` 驱动 `send → await result → advance`。某指令失败时 `CommandSequencer` MUST 重试到上限后 `escalate`（诚实失败：返回 `{ok:false, failedAt:{seq,kind,error}}`），MUST NOT 在失败后继续下发后续指令、MUST NOT 上报假成功。`CommandSequencer` MUST 取代 `PublishExecutor` 末段「发一条 `publish.request` 且不等待」的旧下发模型；上游 6 角色产出的终稿仍为其输入。

#### Scenario: 终稿编排为有序指令序列
- **WHEN** `PublishExecutor` 拿到 6 角色产出的终稿与（占位）元数据
- **THEN** `CommandSequencer.buildCommandSequence` 产出有序序列（如 `navigate_entry → fill_field(title) → fill_field(content) → add_with_candidate(tag)×N → submit_publish → capture_postId`），由 `executePublishSequence` 逐条下发并等待结果再推进

#### Scenario: 失败到重试上限即 escalate 停止
- **WHEN** 10 条指令序列执行到第 5 条，重试到上限仍 `ok:false`
- **THEN** `CommandSequencer` 停止，第 6-10 条 MUST NOT 被下发，返回 `{ok:false, failedAt:{seq:5, kind, error}}`，发布记录最终态为失败

#### Scenario: 红线反例——序列中途失败仍报发布成功（禁止）
- **WHEN** 序列在 `fill_field(content)` 处失败（`ok:false`），但程序仍将整个发布标记为成功 / 继续下发后续指令
- **THEN** 这违反诚实失败红线，MUST NOT 发生；`CommandSequencer` MUST 在该失败步即停、返回 `{ok:false, failedAt}`，不伪造发布成功、不跑到 `submit_publish`

#### Scenario: 红线反例——绕开 sequencer 整页下发（禁止）
- **WHEN** 有人在新路径上保留「`PublishExecutor` 直接 `pusher.pushToEdges(publish.request)` 后不等结果、由边缘整页脚本跑完」
- **THEN** 这是被本阶段取代的旧执行模型，新发布执行 MUST 走 `CommandSequencer` 的逐条 `send→await→advance`，不得在新路径上保留无等待的整页下发

### Requirement: submit_publish 前强制人审闸（AC-PUB）

系统 SHALL 在 `submit_publish` 指令下发前强制通过人审授权，**复用现有审批信号文件机制**（cloud `getApprovalSignalPath` ↔ edge `buildPublishApprovalSignalPath`，路径 `/tmp/aidcp-publish-approve-<requestId>.json`，两端契约 MUST 一致）。授权 MUST 以严格相等 `approved === true` 判定；信号文件缺失、解析失败或 `approved !== true` 时，`CommandSequencer` MUST 在序列中止于 `submit_publish` 之前、绝不下发提交指令、发布记录置为失败，MUST NOT 静默发布。

#### Scenario: 已授权才下发 submit_publish
- **WHEN** `/tmp/aidcp-publish-approve-<requestId>.json` 存在且 `approved === true`
- **THEN** `CommandSequencer` 在序列中加入并下发 `submit_publish`，随后 `capture_postId` 抓取真实 postId

#### Scenario: 未授权时序列截止在提交前
- **WHEN** 审批信号文件不存在 / 解析失败 / `approved !== true`
- **THEN** `CommandSequencer.buildCommandSequence` 截止在 `submit_publish` 之前（不加入提交指令），返回失败，发布记录最终态为失败

#### Scenario: 红线反例——缺省直发（禁止）
- **WHEN** 审批信号缺失（文件不存在）或为 false，但程序把缺省 / 异常当作放行仍下发了 `submit_publish`
- **THEN** 这违反 AC-PUB，MUST NOT 发生；严格相等判定 + 提交前截止 MUST 保证「未明确授权 == 不发布」，缺省与异常一律按未授权处理

#### Scenario: 两端审批信号路径不漂移
- **WHEN** 修改发布链时改动了审批信号文件路径
- **THEN** cloud `getApprovalSignalPath` 与 edge `buildPublishApprovalSignalPath` MUST 仍产出同一路径 `/tmp/aidcp-publish-approve-<requestId>.json`，`AC-PUB-*` 验收 MUST 仍全过

### Requirement: 指令与结果按 recordId+seq 关联

系统 SHALL 以 `recordId + seq` 作为指令与结果配对的**业务级永久关联键**：`publish.command` 与其对应 `publish.command.result` MUST 携带相同的 `recordId` 与 `seq`，`CommandSequencer` MUST 以 `recordId:seq` 为键维护 pending map 并据此配对回报、推进序列。`envelope.id` 仅供日志追踪、MUST NOT 用于业务关联。`CommandSequencer` MUST 在结果到达时按键 resolve 并删除 pending 项；结果在 `timeoutMs`（缺省 30s）内不到达时 MUST reject 并自动清理该 pending 项、记 error 日志，pending map MUST NOT 泄漏。

#### Scenario: recordId+seq 配对请求与结果
- **WHEN** cloud 下发 `publish.command {recordId:100, seq:3, kind:'fill_field'}`，边缘回报 `publish.command.result {recordId:100, seq:3, ok:true}`
- **THEN** `CommandSequencer.onResult` 以 `recordId:seq`（`100:3`）找到对应 pending 项并 resolve，推进到下一条指令

#### Scenario: envelope.id 不用于关联
- **WHEN** 同一发布的多条指令复用或重发导致 `envelope.id` 变化、但 `recordId+seq` 不变
- **THEN** 配对仍以 `recordId+seq` 为准、不受 `envelope.id` 影响；`envelope.id` 仅落日志用于追踪单次请求

#### Scenario: 结果到达即释放 pending 项
- **WHEN** 某 `seq` 的结果正常到达
- **THEN** `onResult` 按 `recordId:seq` 找到 pending 项 resolve 后将其从 map 删除，不残留

#### Scenario: 超时清理不泄漏
- **WHEN** 边缘崩溃 / 断连使某 `seq` 结果在 `timeoutMs`（缺省 30s）内不到达
- **THEN** 该 pending 项超时 reject、自动从 map 清理并记 error 日志，pending map MUST NOT 泄漏

### Requirement: 参照洗稿发布记录持久化来稿快照

当发布触发输入含有人工或阅读旁路指定的单条 `referenceNote` 时，系统 SHALL 将该参照来稿作为发布记录的来源血缘快照持久化到 `publish_log`。快照 SHALL 至少包含来源类型、精选行 id（若来自精选池）、执行账号、源笔记 `sourceId`、标题、正文、作者、话题、来源链接与触发时刻。普通发布或仅抽样素材参与的发布 SHALL 将该字段置空，MUST NOT 编造来源。

该快照 MUST 以触发时输入为准，MUST NOT 在内容页展示时再依赖当前 `curated_content` 行；精选行后续被删除、清空或更新时，历史发布记录仍 SHALL 展示当时的来稿件。来稿快照只用于审计与面板展示，MUST NOT 改变参照洗稿的 prompt 红线、人审闸、发布下发、配图收口或失败判定。

#### Scenario: 参照洗稿记录带来稿快照

- **WHEN** 运营从精选页对一条正文非空的精选图文触发参照洗稿，并生成一条 `pending_approval` 或 `failed` 发布记录
- **THEN** 该发布记录持久化一个 `sourceReference` 快照，包含该精选行触发时的标题、正文、作者、话题、sourceId、sourceUrl 与触发时刻

#### Scenario: 普通发布不编造来源

- **WHEN** 发布由普通 `/publish`、自动发布或抽样精选素材触发，且没有单条 `referenceNote`
- **THEN** 发布记录的来源快照为空，面板不展示「洗稿来源」

#### Scenario: 来源行删除后历史仍可查看

- **WHEN** 一条参照洗稿发布记录已持久化来源快照，之后对应 `curated_content` 行被删除或正文被清理
- **THEN** 内容页仍能从 `publish_log` 快照查看当时来稿件，MUST NOT 因当前精选行缺失而显示断链或伪造空态

#### Scenario: 来源快照不改变发布行为

- **WHEN** 系统为参照洗稿记录写入来源快照
- **THEN** 生成、质量评分、人审、下发与失败处理语义保持不变；该字段只读展示，不参与是否发布的判定

### Requirement: 参照洗稿走保真专用角色链后再进入既有发布下游

当 `TriggerInput.generateInput.referenceNote` 存在时，发布管线 SHALL 走参照专用保真角色链，而不是常规自由创作角色链。常规 `ContentScout` 和 `ContentCreator` MUST NOT 在参照路径产出选题/正文；参照路径 SHALL 由 `ReferenceAnalyzer`、`FaithfulRewritePlanner`、`FaithfulDraftWriter`、`FidelityAuditor` 四个 LLM 角色完成，且只有 `FidelityAuditor` 判定通过后才能写入标准 `createdContent` 字段。`createdContent` 写入后，既有配图、去 AI 味、质量评分、标题、话题、元数据、人审和下发链路 SHALL 原样复用。

四个保真角色职责如下：

- `publish:ReferenceAnalyzer`：抽取原稿主旨、结构、事实/数据/人物/时间线、核心论点和禁止新增清单。
- `publish:FaithfulRewritePlanner`：生成段落级改写计划，明确每段保留点、可改表达和不可新增内容。
- `publish:FaithfulDraftWriter`：按计划写成小红书正文草稿，只写 `faithfulDraft`，MUST NOT 直接写 `createdContent`。
- `publish:FidelityAuditor`：对比参照原文与草稿，检查事实覆盖、未授权新增、视角/身份漂移、结构偏离和近似照抄；通过才写 `createdContent`，失败 MUST 中止管线。

#### Scenario: 参照路径旁路常规创作

- **WHEN** `trigger.generateInput.referenceNote` 非空
- **THEN** `ContentScout` / `ContentCreator` 不产出常规 `scoutDecision` / `createdContent`，由保真角色链产出候选正文

#### Scenario: 审核通过后才进入下游

- **WHEN** `FidelityAuditor` 判定草稿忠实且非近似照抄
- **THEN** 其将草稿转换为 `createdContent`，下游既有配图 / 标题 / 话题 / 人审 / 发布链继续运行

#### Scenario: 审核失败中止

- **WHEN** `FidelityAuditor` 发现草稿新增原稿没有的事实、虚构个人经历、改变原作者身份视角、遗漏关键结论或近似照抄
- **THEN** 该角色 MUST 写 `pipelineAbort` 并使本次发布失败，不得落待审草稿

#### Scenario: 常规发布不受影响

- **WHEN** 普通 `/publish` 或自动发布触发且无 `referenceNote`
- **THEN** 仍走既有 `ContentScout` → `ContentCreator` 常规创作路径，保真角色链不激活

### Requirement: 保真洗稿禁止未授权新增事实

参照保真改写产物 SHALL 只使用参照原文中存在的信息以及账号人设允许的表达风格。系统 MUST 禁止新增参照原文未出现的测试结果、百分比数据、部署经验、身份背书、时间线、人物关系、外部结论或案例；若需要补背景，只能使用泛化过渡句，不得构成新的事实主张。FidelityAuditor MUST 将未授权新增事实判为失败。

#### Scenario: 禁止虚构实测数据

- **WHEN** 原文未提供「我方实测延迟降低 58%」等数据
- **THEN** 保真成稿不得新增该数据；若新增则审核失败

#### Scenario: 保留原稿身份边界

- **WHEN** 原文由项目早期成员/committer 复盘项目史
- **THEN** 成稿不得改写成「我作为使用者刚接入试了试」的身份视角，除非原文明确给出该视角

### Requirement: Manual Feishu publish approvals route to the triggering conversation

When a publish generation is triggered by a Feishu command event, the generated publish approval card SHALL be sent to the same Feishu conversation that delivered that command when the event provides a source `chatId`. A private-chat `/publish` command SHALL therefore receive its approval card in that private chat, and a group-chat `/publish` command SHALL receive its approval card in that group. Publish triggers without a source conversation SHALL continue to use the configured default approval group.

The system MUST NOT treat a failed approval-card send as a successful delivery. If the source or default target rejects the card send, the system SHALL log the failed delivery and keep the draft in an honest pending state; it MUST NOT claim that the card was sent.

#### Scenario: Private command receives approval card in private chat

- **WHEN** a Feishu private-message command `/publish <nickname>` triggers a publish generation and the event includes `chatId=P`
- **THEN** the publish approval card is sent to `P`
- **AND** the default approval group is not used for that manual command

#### Scenario: Group command receives approval card in triggering group

- **WHEN** a Feishu group-message command `/publish <nickname>` triggers a publish generation and the event includes `chatId=G`
- **THEN** the publish approval card is sent to `G`
- **AND** the default approval group is not used for that manual command

#### Scenario: Non-command publish still uses default approval group

- **WHEN** a publish generation is triggered by an automatic, scheduled, panel/reference, mock, or edge-originated flow without a source Feishu `chatId`
- **THEN** the publish approval card is sent using the existing default approval group resolution

#### Scenario: Approval card send failure is honest

- **WHEN** the chosen Feishu approval target rejects the approval card send
- **THEN** the failure is logged with the request or record context
- **AND** the system MUST NOT report that the approval card was successfully sent

