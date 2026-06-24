# Design — publish-content-media-roles（发帖流水线生产段角色细拆，阶段2）

> 本文 file:line 引用一律相对 `aidcp-cloud/`（唯一受影响仓，分支 `master`）。行号以 change 立项时（2026-06-20）的工作树为准，落地时如有漂移以 `grep` 实测为准。

## Context

发帖流水线是 aidcp-cloud 内一条**黑板式**事件链，与浏览侧 `RoleDispatcher` + `EventBus` 平行但独立。黑板是 `PipelineContext<PipelineFields>`（`src/publish-agent/pipeline-context.ts:4`），角色经 `watch(key, handler)`（`pipeline-context.ts:59`）/ `watchAll(keys, handler)`（`pipeline-context.ts:84`）订阅，经 `write(key, value)`（`pipeline-context.ts:15`）产出；写入即同步触发该键所有 watcher（`pipeline-context.ts:18-35`）与 watchAll 组就绪检查（`pipeline-context.ts:37-55`）。`PublishOrchestrator`（`src/publish-agent/publish-orchestrator.ts:11`）注册角色（`registerRole`，`publish-orchestrator.ts:28`）、写 `trigger` 启动链（`publish-orchestrator.ts:60`），在 `awaitCompletion`（`publish-orchestrator.ts:86`）里等 `publishResult` 写入、或 `scoutDecision.shouldPublish=false` 短路（`publish-orchestrator.ts:103-114`）、或 120s 超时（`publish-orchestrator.ts:117-122`）后结束。

现役生产链路（**6 角色**，注册块 `src/server.ts:327-364`，导出 `src/publish-agent/roles/index.ts:3-8`）：

```
trigger
  → ContentScout      (watch trigger,        write scoutDecision)   content-scout.ts:16-22
  → ContentCreator    (watch scoutDecision,  write createdContent)  content-creator.ts:21-27（guard shouldPublish content-creator.ts:35-37）
  → ImageDirector     (watch createdContent, write imageDirective)  image-director.ts:18-25
  → ContentAssembler  (watchAll createdContent+imageDirective, write assembledContent) content-assembler.ts:26-34
  → ApprovalGatekeeper(watch assembledContent, write gateDecision)  approval-gatekeeper.ts:15-22
  → PublishExecutor   (watch gateDecision,   write publishResult)
```

两处粗角色职责混杂（proposal Why，`proposal.md:5-18`）：

- **`ImageDirector`（`src/publish-agent/roles/image-director.ts`）决策 + 执行合一**：`execute`（`image-director.ts:41`）里 Step 1 是 LLM 算配图 prompt（`image-director.ts:47-64`，调 `buildImagePrompt` `prompts.ts:218` + `parseLlmOutput` `image-director.ts:92`），Step 2 才是真生图（`image-director.ts:67`，调 `imageProvider.generate` `image-provider.ts:20`）。两步共用一个 `fallback: 'skip'`（`image-director.ts:23`）、一个 `timeoutMs: 60000`（`image-director.ts:22`），无法对决策与生图分别设超时 / 重试 / 降级；单测要同时桩 LLM 与 imageProvider（现 `test/publish-agent/image-director.test.ts`）。
- **`ContentAssembler`（`src/publish-agent/roles/content-assembler.ts`）清洗 + 评分 + 组装三合一**：`execute`（`content-assembler.ts:51`）里 Step 1 清洗（`content-assembler.ts:55`，调 `postProcessor.process` `post-processor.ts:65`，算 `aiScore`），Step 2 LLM 质量评审（`content-assembler.ts:58-67`，调 `buildAssemblerPrompt` `prompts.ts:255` + `parseReviewOutput` `content-assembler.ts:86`），Step 3 组装（`content-assembler.ts:74-83`）。三步耦合在一个 `fallback: 'default'`（`content-assembler.ts:32`）、一个 `timeoutMs: 20000`（`content-assembler.ts:31`）里，清洗失败 / AI 味评分 / 评审 LLM 失败的降级语义被压平。

本 change 是 A 重构序列【阶段2 内容生产 + 配图角色细拆】，按版本 A（参数化"种类级"）把生产段细拆，**仅在黑板流水线内部重组**，与浏览侧"一角色一职"对齐。

权威约束：稳定边界 `AssembledContent`（`src/publish-agent/types.ts:104-113`）逐字不改 → 下游 `ApprovalGatekeeper`（`approval-gatekeeper.ts:15`，watch `assembledContent` `approval-gatekeeper.ts:18`）/ `PublishExecutor` 零改动；不碰协议 / edge / 下游；红线"不静默假成功"贯穿（无图诚实回 `imageUrl:null`，沿用现 `getEmptyDirective` `image-director.ts:82-90` 语义，绝不伪造 URL）。base 机制：`BasePublishRole`（`src/publish-agent/roles/base-role.ts:12`）的 `RoleConfig`（`base-role.ts:4`：`name` / `watchKeys` / `waitAll` / `timeoutMs` / `fallback`）+ `register`（`base-role.ts:23`：单键 `watch`、多键 `watchAll`，均 `once:true` `base-role.ts:48-52`）+ `shouldActivate` 守卫（`base-role.ts:65`）+ `extractInput`（`base-role.ts:62`）+ `execute`（`base-role.ts:56`）+ `outputKey`（`base-role.ts:59`）+ `handleError` 按 `fallback` 降级（`base-role.ts:81-94`）+ `getDefaultOutput`（`base-role.ts:97`）。新角色一律继承它。

## Goals / Non-Goals

**Goals**
- 生产段每个角色单一职责：决策类只产计划 / 评分 / 选择，执行类只做外部副作用（生图）。
- 配图链路 `ImageDirector`（`image-director.ts`）→ `ImagePlanner`（决策）+ `ImageGenerator`（执行），各自可独立设 `timeoutMs` / 重试 / `fallback` / 单测。
- 后处理链路 `ContentAssembler`（`content-assembler.ts`）→ `ContentCleaner`（清洗）+ `AiFlavorScorer`（AI 味分）+ `QualityScorer`（质量分）+ `ContentAssembler`（瘦身组装）。
- 新增 `ContentTypeSelector`（类型决策，现恒图文预留）、`CoverSelector`（封面选择，现单图预留多图）。
- `AssembledContent`（`types.ts:104-113`）同形产出，下游 + 协议 + edge 零改动。
- 每个新角色脱 LLM / 脱图源可单测；`test/publish-agent/publish-orchestrator.test.ts` 端到端不回归。

**Non-Goals**
- 不改触发器（`PublishScheduler` / `TriggerInput` `types.ts:59-72` / orchestrator `trigger()` `publish-orchestrator.ts:33`）与触发条件。
- 不做元数据维度决策器（话题 / @ / 地点 / 可见范围 / 合规）——属阶段3。
- 不做来源血缘 `LikedNoteStore`、不删 `temp` 口、不做 edge 配图真上传（stage-1 已诚实回 `kind_not_implemented`）。
- 不改协议（两份 `protocol.ts` / `command-bridge.ts` / `docs/protocol.md`）、不改 edge、不改下游消费方（`approval-gatekeeper.ts` / `publish-executor.ts` / 审批信号文件契约 / `publish-log` 写入）。
- 不改 `PublishOrchestrator` 的终止条件 / 超时机制（`publish-orchestrator.ts:86-124`）与黑板 `PipelineContext`（`pipeline-context.ts`）实现本身。

## Decisions

### D1：配图拆为 ImagePlanner（决策）+ ImageGenerator（执行），新增中间键 `imagePlan`

- **`ImagePlanner`**（新增 `src/publish-agent/roles/image-planner.ts`）：`config.watchKeys = ['createdContent']`、`outputKey = 'imagePlan'`、`fallback: 'default'`（LLM 失败 → `getDefaultOutput` 返回"不配图"计划）。承接现 `ImageDirector` 的 Step 1（`image-director.ts:47-64`），即 `buildImagePrompt`（`prompts.ts:218`）+ `parseLlmOutput`（`image-director.ts:92-104`）+ `executeWithFallback`（`retry-strategy.ts:42`）。产出 `imagePlan { wantImage, imagePrompt, imageStyle, imageCount, fallbackStrategy, plannedAt }`（`wantImage=false` 当 LLM 降级或无 prompt，对齐现 `image-director.ts:61-64` 的"无 prompt 即跳过"判定）。
- **`ImageGenerator`**（新增 `src/publish-agent/roles/image-generator.ts`）：`watchKeys = ['imagePlan']`、`outputKey = 'imageDirective'`、`fallback: 'skip'`（生图失败 → `getDefaultOutput` 走空 directive，对齐现 `getEmptyDirective` `image-director.ts:82-90`）。承接现 Step 2（`image-director.ts:67-75`），调 `imageProvider.generate`（`image-provider.ts:20`，`ImageResult.url` 失败为 null `image-provider.ts:11`）。当 `imagePlan.wantImage=false` 或无 `imagePrompt` → 直接产空 `imageDirective`（`imageUrl:null`），**诚实回 null、绝不伪造 URL**（红线）。
- **取舍**：保留 `imageDirective`（`types.ts:95-101`，形状逐字不改）作为配图链路对外产出键，把决策抽到上游新键 `imagePlan`；这样 `imageDirective` 形状与语义不变，下游 `CoverSelector` / `ContentAssembler` 读法不变。`enableImageGeneration`（现 `image-director.ts:13/34/42`、`server.ts:333`）下沉到 `ImageGenerator` 注入。

### D2：后处理拆为 ContentCleaner + AiFlavorScorer + QualityScorer + 瘦身 ContentAssembler

- **`ContentCleaner`**（新增 `src/publish-agent/roles/content-cleaner.ts`）：`watchKeys = ['createdContent']`、`outputKey = 'cleanedContent'`、`fallback: 'default'`。复用现有 `PostProcessor.process`（`post-processor.ts:65`，**不改其实现**，含其内部重写失败退回原文 `post-processor.ts:82-90`）；承接现 `content-assembler.ts:55` 的清洗步。产出 `cleanedContent { content, rewritten, flaggedPhrases, aiScore, cleanedAt }`（即 `PostProcessResult` `types.ts:28-37` + `cleanedAt`）。
- **`AiFlavorScorer`**（新增 `src/publish-agent/roles/ai-flavor-scorer.ts`）：`watchKeys = ['cleanedContent']`、`outputKey = 'aiFlavorScore'`。从 `cleanedContent.aiScore` 投影写 `aiFlavorScore { aiScore, scoredAt }`。
  - 取舍：`aiScore` 本就由清洗（`aiScoreFromHits` `post-processor.ts:45`）算出，`AiFlavorScorer` 是一层**显式投影 / 收口**角色，便于将来把 AI 味评分换成独立模型而不动清洗。不重复计算，只搬运 + 留扩展点；不依赖外部、**必写键**（保障 D5 watchAll 就绪，见 R1）。
- **`QualityScorer`**（新增 `src/publish-agent/roles/quality-scorer.ts`）：`watchKeys = ['cleanedContent']`、`outputKey = 'qualityReport'`、`fallback: 'default'`（LLM 失败 → 由 aiScore 推 `qualityScore = Math.round((1 - aiScore) * 70)`，**逐字沿用**现 `content-assembler.ts:66` 的降级公式）。承接现 `ContentAssembler` 的 Step 2（`content-assembler.ts:58-67`），即 `buildAssemblerPrompt`（`prompts.ts:255`）+ `parseReviewOutput`（`content-assembler.ts:86-92`，含 `qualityScore` 钳到 0-100 `content-assembler.ts:91`）。产出 `qualityReport { qualityScore, reviewedAt }`。
- **`ContentAssembler`（瘦身）**（改造 `src/publish-agent/roles/content-assembler.ts`）：`watchKeys = ['cleanedContent','aiFlavorScore','qualityReport','imageDirective','coverSelection']`、`waitAll: true`、`outputKey = 'assembledContent'`。**仅纯组装、无 LLM、无 IO**（删 `llmClient` / `postProcessor` 依赖 `content-assembler.ts:35-41`）。字段映射（替代现 `content-assembler.ts:74-83`）：
  - `finalContent ← cleanedContent.content`（现 `ppResult.content` `content-assembler.ts:75`）
  - `finalTags ← createdContent.tags`（现 `content-assembler.ts:76`，从 snapshot `extractInput` 取，**不入 watchKeys**，见取舍）
  - `imageUrl ← coverSelection.imageUrl`（等价细拆前 `imageDirective.imageUrl` `content-assembler.ts:77`）
  - `aiScore ← aiFlavorScore.aiScore`（现 `ppResult.aiScore` `content-assembler.ts:78`）
  - `qualityScore ← qualityReport.qualityScore`（现 `review.qualityScore` `content-assembler.ts:79`）
  - `rewritten ← cleanedContent.rewritten` / `flaggedPhrases ← cleanedContent.flaggedPhrases`（现 `content-assembler.ts:80-81`）
  - `assembledAt ← clock()`（现 `content-assembler.ts:82`）
  - 取舍：组装也读 `createdContent`（拿 tags），但其"触发就绪"由 watchAll 五个生产键决定；`createdContent` 早已就绪、用 `extractInput`（对齐现 `content-assembler.ts:44-49`）从 snapshot 取即可，不必列入 watchKeys（否则与 `cleanedContent` 重复触发条件）。

### D3：新增 ContentTypeSelector（前置）与 CoverSelector（后置）

- **`ContentTypeSelector`**（新增 `src/publish-agent/roles/content-type-selector.ts`）：`watchKeys = ['scoutDecision']`、`outputKey = 'contentType'`、`shouldActivate = scoutDecision.shouldPublish === true`（与 `ContentCreator` 守卫一致 `content-creator.ts:35-37`，覆写 base `shouldActivate` `base-role.ts:65`）。产出 `contentType { kind: 'image_text', selectedAt }`（现恒图文；`kind` 联合类型预留 `'video' | 'text'`）。
- **`CoverSelector`**（新增 `src/publish-agent/roles/cover-selector.ts`）：`watchKeys = ['imageDirective']`、`outputKey = 'coverSelection'`、`fallback: 'default'`。产出 `coverSelection { imageUrl, hasCover, selectedAt }`：单图 → 直接选；无图（`imageDirective.imageUrl === null`，`types.ts:96`）→ `imageUrl: null, hasCover: false`（**诚实回报，红线**）。多图选择逻辑预留接口。
- **取舍**：`ContentTypeSelector` 当前不阻塞配图链路（配图仍由 `createdContent` 触发 `ImagePlanner`），其产出供组装记录 / 将来按类型分流用；这样阶段2 不引入新阻塞依赖、行为等价，类型分流留后续（见 Open Questions）。这两个角色即便逻辑简单也必须实体化为真实角色（spec 红线 `specs/publish-pipeline/spec.md:88-91`），不得在 `ContentAssembler` 硬编码"一律图文 / 一律首图"绕过。

### D4：黑板键扩充，`PipelineFields` 增 6 键，`AssembledContent` 不动

在 `src/publish-agent/types.ts` 新增 6 个接口与 `PipelineFields`（`types.ts:133-143`）6 个键：

| 新键 | 接口 | 形状 |
| --- | --- | --- |
| `contentType` | `ContentType` | `{ kind: 'image_text' \| 'video' \| 'text'; selectedAt: number }` |
| `imagePlan` | `ImagePlan` | `{ wantImage: boolean; imagePrompt: string \| null; imageStyle: ImageDirective['imageStyle']; imageCount: number; fallbackStrategy: 'skip' \| 'color_placeholder'; plannedAt: number }` |
| `cleanedContent` | `CleanedContent` | `{ content: string; rewritten: boolean; flaggedPhrases: string[]; aiScore: number; cleanedAt: number }` |
| `aiFlavorScore` | `AiFlavorScore` | `{ aiScore: number; scoredAt: number }` |
| `qualityReport` | `QualityReport` | `{ qualityScore: number; reviewedAt: number }` |
| `coverSelection` | `CoverSelection` | `{ imageUrl: string \| null; hasCover: boolean; selectedAt: number }` |

`imageStyle` / `fallbackStrategy` 复用 `ImageDirective`（`types.ts:95-101`）的联合类型，避免漂移。保留键不动：`trigger` / `scoutDecision` / `createdContent` / `imageDirective` / `assembledContent` / `gateDecision` / `publishResult` / `retrySignal`（`types.ts:134-142`）。**`AssembledContent`（`types.ts:104-113`）逐字不改**——`npm run typecheck` 暴露任何遗漏，`git diff` 验证该接口 diff 为空。

### D5：触发拓扑（细拆后，11 角色）

```
trigger
  └─ ContentScout            → scoutDecision        (watch trigger)
       ├─ ContentTypeSelector → contentType         (watch scoutDecision, guard shouldPublish)
       └─ ContentCreator      → createdContent       (watch scoutDecision, guard shouldPublish)
            ├─ ImagePlanner    → imagePlan           (watch createdContent)
            │    └─ ImageGenerator → imageDirective  (watch imagePlan)
            │         └─ CoverSelector → coverSelection (watch imageDirective)
            └─ ContentCleaner  → cleanedContent      (watch createdContent)
                 ├─ AiFlavorScorer → aiFlavorScore   (watch cleanedContent)
                 └─ QualityScorer  → qualityReport   (watch cleanedContent, fallback default)
ContentAssembler  watchAll[cleanedContent, aiFlavorScore, qualityReport, imageDirective, coverSelection]
  → assembledContent  ──(稳定边界 types.ts:104-113，下游零改动)──▶
ApprovalGatekeeper → gateDecision → PublishExecutor → publishResult
```

注册顺序在 `src/server.ts:327-364` 替换：删 `ImageDirectorRole` 注册（`server.ts:330-334`），按上图加 7 个新角色 + 瘦身 `ContentAssembler`（`server.ts:335-338` 改造，去掉 `postProcessor` 注入 / 改注入到 `ContentCleaner`，去掉 `llmClient` 注入 / 改注入到 `QualityScorer`）；`ApprovalGatekeeper`（`server.ts:339`）/ `PublishExecutor`（`server.ts:340-364`）注册逐字不动。导出在 `roles/index.ts:5` 移除 `ImageDirectorRole`、新增 7 个角色导出（保留 `ContentAssemblerRole` `roles/index.ts:6`）。注册顺序无关正确性（黑板靠键就绪触发，`base-role.ts:23-53` + `pipeline-context.ts:66/98` 对"已就绪键"立即补触发），但建议按拓扑排列便于阅读。

## Risks / Trade-offs

- **R1 watchAll 就绪时序（最高优先级）**：`ContentAssembler` watchAll 由现 2 键（`content-assembler.ts:29`）改为 5 键。`PipelineContext` 的 watchAll 是严格 AND（`pipeline-context.ts:40` `ready.size === keys.length` 才触发），任一键不写则组装永不触发 → orchestrator 120s 超时（`publish-orchestrator.ts:117-122`）。缓解：清洗 / 评分 / 配图链路各角色 `fallback` 必须保证"无论成败都写自己的键"——`ContentCleaner` / `QualityScorer` / `CoverSelector` 用 `fallback:'default'` + `getDefaultOutput`（经 base `handleError` `base-role.ts:81-94` 在异常时也写键）；`AiFlavorScorer` 不依赖外部、纯投影、必写。注意 base `handleError` 仅对 `fallback:'skip'` 自动写 `getDefaultOutput`（`base-role.ts:83-88`），`fallback:'default'` 是"子类自行处理"（`base-role.ts:93`），故 default 类角色须在 `execute` 内部用 `executeWithFallback`（`retry-strategy.ts:42`）兜底返回、保证 `execute` 不抛、键必写（对齐现 `content-scout.ts:36-49` / `content-assembler.ts:58-67` 写法）。回归靠 `publish-orchestrator.test.ts` 端到端 + 各角色降级单测。
- **R2 角色数 6→11 的注册测试回归（BREAKING）**：`getRoles()`（`publish-orchestrator.ts:135`）名称集变化、`server.ts:327-364` 注册块变化、`publish-orchestrator.test.ts:79-95` 与 `:174-179` 两处注册块需改。缓解：明确 BREAKING（proposal `## What Changes` `proposal.md:22-24`），tasks 含"更新 orchestrator 测试断言为新角色集 + 验证端到端仍产同形 `assembledContent`"。
- **R3 `aiScore` 双角色读取**：`AiFlavorScorer` 与 `QualityScorer` 都 watch `cleanedContent`（`pipeline-context.ts:59` 同键多 watcher，`pipeline-context.ts:18-35` 顺序同步触发）。AiFlavorScorer 取 `aiScore`、QualityScorer 取 `content` 评审且降级也用 `aiScore`，二者并行、互不依赖、各写各键，无竞态（写为同步、单线程事件循环；watcher 异常互不阻塞 `pipeline-context.ts:24-28`）。
- **R4 过度细拆的成本**：角色数翻倍带来注册 / 编排样板。权衡后接受——与浏览侧"一角色一职"对齐、单测 / 演进收益大于样板成本；base 已把样板收敛到 `config` + 三个抽象方法（`base-role.ts:56-62`）。
- **R5 行为等价验证**：细拆后端到端结果必须与细拆前等价（同 `createdContent` 输入 → 同 `assembledContent` 八字段值）。缓解：扩展 `publish-orchestrator.test.ts`，断言 `assembledContent` 字段集与值等价；旧 `test/publish-agent/image-director.test.ts` / `content-assembler.test.ts` 的覆盖点迁移到对应新角色单测，不丢覆盖（迁移映射见 Migration §2）。
- **R6 `imageStyle` 类型穿越**：现 `parseLlmOutput`（`image-director.ts:92-104`）把 `imageStyle` 钳到合法联合并默认 `'illustration'`（`image-director.ts:96-97`）。拆分后该钳制逻辑随 Step 1 一起搬到 `ImagePlanner`，`ImageGenerator` 直接信任 `imagePlan.imageStyle`，避免两处各钳一次产生语义漂移。

## Migration Plan

1. **类型先行**：`types.ts` 增 6 键接口 + `PipelineFields`（`types.ts:133-143`）6 键；`AssembledContent`（`types.ts:104-113`）不动。`npm run typecheck` 暴露遗漏，`git diff src/publish-agent/types.ts` 验证 `AssembledContent` 段无改动。
2. **新角色逐个落地 + 单测（覆盖点迁移，不丢覆盖）**：
   - `image-planner.ts` + `image-generator.ts`：承接 `image-director.ts` Step 1 / Step 2；旧 `test/publish-agent/image-director.test.ts` 的"LLM 出 prompt / LLM 失败降级 / 无 prompt 跳过"覆盖点拆到 `ImagePlanner` 单测，"生图成功 / 生图失败回 null / enable=false"拆到 `ImageGenerator` 单测。删 `image-director.ts`。
   - `content-cleaner.ts` + `ai-flavor-scorer.ts` + `quality-scorer.ts` + 瘦身 `content-assembler.ts`：旧 `test/publish-agent/content-assembler.test.ts` 的"清洗 / 重写"→ `ContentCleaner`、"质量评审成功 / LLM 失败走公式"→ `QualityScorer`、"终稿组装八字段"→ 瘦身 `ContentAssembler`。
   - `content-type-selector.ts`（guard 覆盖）+ `cover-selector.ts`（有图选首图 / 无图回空）。
   - `roles/index.ts:3-8` 更新导出（移除 `ImageDirectorRole`，加 7 个新角色，保留 `ContentAssemblerRole`）。
   每个角色脱 LLM / 脱图源单测（桩 `QwenClient.chat` / `ImageProvider.generate` / `PostProcessorLike.process`，对齐现 `content-assembler.ts:10-12` 的 `PostProcessorLike` 接口）。
3. **server 注册替换**：`server.ts:330-334` 删 `ImageDirectorRole`，按 D5 加 7 个新注册 + 改造 `ContentAssembler` 注册（`server.ts:335-338`），依赖（`llm` / `wanxiangClient` `server.ts:332` / `postProcessor` `server.ts:337`）按角色重新分配（`llm`→Planner/QualityScorer/TypeSelector，`wanxiangClient`→Generator，`postProcessor`→Cleaner）；`server.ts:339-364` 下游两块逐字不动；同步 import 块（`server.ts:56-61`）。
4. **回归**：`npm run test:acceptance`（安全红线 `AC-PROTO-*` / `AC-PUB-*`（含审批信号契约不漂移）/ `AC-RISK-*` / `AC-E-*` 必过）→ 全量 `npm test`（含 `publish-orchestrator.test.ts` 端到端等价、`getRoles()` 返 11 名）→ `npm run typecheck`。
5. **本地仅代码级验证**，cloud 正式运行只在 ECS（CLAUDE.md §5）；部署走中控 §5 安全序列（本 change 不强制即时部署）。

## Open Questions

- `ContentTypeSelector` 当前不阻塞配图链路（仅产出供记录 / 将来分流，D3 取舍）；阶段3 引入视频 / 文字时，类型是否应改为配图链路前置阻塞依赖（按类型决定走不走 `ImagePlanner`）？本阶段先解耦，分流逻辑留后续。
- `AiFlavorScorer` 现为对 `cleanedContent.aiScore`（`post-processor.ts:45` 算出）的显式投影，是否值得独立成角色（vs 让组装直接读 `cleanedContent.aiScore`）？本阶段按"一职一角色 + 留独立演进点"保留独立角色；若后续证明无演进价值可在阶段3 评估合并（且合并会破坏 watchAll 五键、需谨慎）。
- 多图封面选择策略（美学 / 首图 / LLM 选）留待真正支持多图生成（现 `imageProvider.generate` `image-provider.ts:20` 单图）后定；本阶段 `CoverSelector` 仅实现单图直选 + 无图回空。
- `QualityScorer` 的降级公式 `qualityScore = round((1 - aiScore) * 70)` 本阶段**按重构纪律原样保留**（逐字沿用现 `content-assembler.ts:66`，不在重构中改行为）。该线性假设（无 AI 味时基准 70 分）是历史黑盒，其业务合理性未经论证；是否应参数化 / 引入可调阈值留后续评估，实现时 `QualityScorer` 把该公式收敛在一处（便于将来单点调参）。
