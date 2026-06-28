# publish-pipeline Specification

## Purpose
TBD - created by archiving change dedicated-title-creator-role. Update Purpose after archive.
## Requirements
### Requirement: 标题由独立角色在正文定稿后生成

系统 SHALL 以一个独立角色 `TitleCreator`（角色 id `publish:TitleCreator`）生成发帖标题，与内容生成解耦以避免单次 LLM 调用的注意力稀释。该角色 MUST `watchKeys=['assembledContent']`，以**最终定稿正文** `assembledContent.finalContent` 为输入（MUST NOT 取草稿 `createdContent.content`——正文经去 AI 味环节改写后才定稿，标题须忠于真正发出的文字），单次短提示产出一个 ≤18 可见字符的钩子标题，写入新黑板字段 `titleSelection`（`{title, source:'llm'|'derived', decidedAt}`）。`source` MUST 如实标注：LLM 真产出为 `'llm'`，任何派生/兜底为 `'derived'`，MUST NOT 把派生标题标为 `'llm'`。

#### Scenario: 正文定稿后激活、据定稿正文产出标题
- **WHEN** `ContentAssembler` 写出 `assembledContent`（含 `finalContent`）
- **THEN** `TitleCreator` 激活，读 `assembledContent.finalContent` 单独生成一个 ≤18 字标题，写入 `titleSelection`，`source='llm'`

#### Scenario: 取定稿正文而非草稿
- **WHEN** 去 AI 味环节把草稿里的某句话删改、`finalContent` 与 `createdContent.content` 不一致
- **THEN** `TitleCreator` 据 `finalContent`（真正发出的版本）拟标题，标题不引用已被删改的草稿句子

#### Scenario: 标题与正文分两次 LLM 调用
- **WHEN** 生成一篇帖子
- **THEN** 正文由 `ContentCreator` 一次调用产出、标题由 `TitleCreator` 在其后另一次调用产出，标题不再作为「标题+正文+标签」单次 JSON 里被稀释的子字段

### Requirement: 标题生成失败则发布失败且绝不造假标题

`TitleCreator` 失败（LLM 调用失败 / 超时 / 多次重试后仍不合规）时系统 MUST 判该次发布失败，MUST NOT 派生或编造一个标题去顶替继续发布。角色失败策略为 `abort`：失败时**不写 `titleSelection`**，下游发布因缺该字段而不激活、本次流水线判 `failed`。角色默认 `timeoutMs=120000`。失败 MUST 即时冒泡为流水线失败，MUST NOT 让流水线干等到 `pipelineTimeoutMs` 才超时。

#### Scenario: 标题 LLM 失败则不发布、判失败
- **WHEN** `TitleCreator` 的 LLM 调用连续失败、重试用尽
- **THEN** 不写 `titleSelection`，`PublishExecutor` 不激活、不下发任何发布指令，本次流水线判 `failed`

#### Scenario: 红线反例——派生假标题顶替（禁止）
- **WHEN** 标题生成失败，有实现想用「正文首行切一段」当标题继续发布
- **THEN** 这违反「失败=发布失败、不造假标题」，MUST 被拒绝；正确行为是判失败、不发布

#### Scenario: 失败即时判定不挂死
- **WHEN** `TitleCreator` `abort`
- **THEN** 流水线即时收敛为 `failed`（与 `ContentCreator` 现有 `abort` 行为一致），MUST NOT 干等到 18 分钟 `pipelineTimeoutMs`

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

人审授权信号到达即 SHALL 触发对应草稿的下发段（通过即切，不等自然空档）。下发 MUST 从落库草稿重建发布输入
（标题 / 正文 / 标签 / 图 / 元数据），下发上线的内容 MUST 与审批卡上所审的那份草稿一致；MUST NOT 在下发时
重新生成内容、MUST NOT 用生成与下发之间变化后的人设 / 配置回灌或改写已定稿草稿（陈旧草稿如实照发，所见即所发）。
下发时若该账号无在线边缘节点，MUST 诚实判 `failed`（不伪造成功、不静默丢弃授权）。

#### Scenario: 授权到达即下发该草稿
- **WHEN** 某 `pending_approval` 草稿的人审授权信号（`approved === true`）到达
- **THEN** 云端即触发该草稿的下发段（让位 → 重建发布输入 → 驱动指令序列 → 回写结果），不等待自然空档

#### Scenario: 下发即所审、不重生成
- **WHEN** 一份草稿在 T0 生成定稿、T1（数小时后）才被批准
- **THEN** 下发上线的标题 / 正文 / 配图 / 元数据为 T0 定稿的那一份（与审批卡一致），MUST NOT 在 T1 重新生成或按 T1 的人设 / 配置改写

#### Scenario: 下发时边缘离线诚实失败
- **WHEN** 授权到达、进入下发段，但该账号此刻无在线边缘节点
- **THEN** 云端 MUST 诚实判该次发布 `failed`（不发指令、不伪造成功），授权 MUST NOT 被静默吞掉；状态可被运营看见并重触发

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
排队或被忽略而 MUST NOT 并发抢同一边缘。生成候审段 SHALL 限制堆积：当某账号已有一份 `pending_approval`
草稿尚未推进终态时，MUST NOT 为该账号再生成新草稿。下发段对同一 `recordId` MUST 幂等：已 `published` 或
正在下发的 `recordId` 重复授权 MUST NOT 触发二次发布。

#### Scenario: 同账号下发串行
- **WHEN** 某账号一份草稿正在下发，另一份草稿的授权同时到达
- **THEN** 第二份的下发 MUST 排队或被跳过、MUST NOT 与第一份并发向同一边缘下发指令

#### Scenario: 每账号至多一份待审草稿
- **WHEN** 某账号已有一份 `pending_approval` 草稿未推进终态，发布又被触发欲为该账号生成新草稿
- **THEN** 生成段 MUST NOT 为该账号再产新草稿（避免堆积与下发撞会话），待现有草稿推进终态后方可再生

#### Scenario: 下发对 recordId 幂等
- **WHEN** 同一 `recordId` 的授权信号被重复投递（重复点击 / 兜底扫描与事件双触发）
- **THEN** 已 `published` 或正在下发的 `recordId` MUST NOT 二次下发 / 二次提交，结果保持单次发布

#### Scenario: 红线反例——并发下发抢同一边缘（禁止）
- **WHEN** 有实现允许同账号两份草稿同时进入下发、并发向同一边缘下发发布指令
- **THEN** MUST 视为违规、不予合入；同账号下发 MUST 串行，杜绝两条发布序列在同一 Chrome 上交错撞页

