# Tasks — publish-content-media-roles（发帖流水线生产段角色细拆，阶段2）

> 本阶段**纯 aidcp-cloud**（分支 `master`），不碰协议 / edge / 下游消费方。
> 回写格式：完成后用 HTML 注释把对应 task 标 `[x]` 并附 `<!-- aidcp-cloud <commit-sha> 备注 -->`，部署 ECS 后追加 `<!-- <date> deployed -->`。
> 铁律：稳定边界 `assembledContent` 逐字同形产出；`ApprovalGatekeeper` / `PublishExecutor` 注册与源码零改动；红线"不静默假成功"贯穿（无图诚实回 `null`、分数失败如实降级）。
> file:line 引用相对 `aidcp-cloud/`，以落地时 `grep` 实测为准。

<!-- aidcp-cloud cc7e732 全 §1-§8 实装：types+6键 / ImagePlanner+ImageGenerator / ContentCleaner+AiFlavorScorer+QualityScorer+瘦身ContentAssembler / ContentTypeSelector+CoverSelector / server 注册 6→11 / 删 image-director.{ts,test} 覆盖迁移 / 7 新角色单测 + orchestrator 11 角色边界等价。assembledContent 边界逐字不变、下游零改动。cloud 全量 228 绿、acceptance 18 绿(AC-PROTO/AC-PUB 不回归)、typecheck 净。未部署(随 A 后续阶段统一)。 -->

## 1. aidcp-cloud — 类型与黑板新键（先行，typecheck 暴露遗漏）

- [x] 1.1 `src/publish-agent/types.ts` 新增 6 个接口：`ContentType { kind: 'image_text' | 'video' | 'text'; selectedAt: number }`、`ImagePlan { wantImage: boolean; imagePrompt: string | null; imageStyle: ImageDirective['imageStyle']; imageCount: number; fallbackStrategy: 'skip' | 'color_placeholder'; plannedAt: number }`、`CleanedContent { content: string; rewritten: boolean; flaggedPhrases: string[]; aiScore: number; cleanedAt: number }`、`AiFlavorScore { aiScore: number; scoredAt: number }`、`QualityReport { qualityScore: number; reviewedAt: number }`、`CoverSelection { imageUrl: string | null; hasCover: boolean; selectedAt: number }`；`imageStyle` / `fallbackStrategy` 复用 `ImageDirective`（`types.ts:95`）联合类型避免漂移。验证：`npm run typecheck` 通过。
- [x] 1.2 `PipelineFields`（`types.ts:133`）增 6 键 `contentType` / `imagePlan` / `cleanedContent` / `aiFlavorScore` / `qualityReport` / `coverSelection`；保留键 `trigger` / `scoutDecision` / `createdContent` / `imageDirective` / `assembledContent` / `gateDecision` / `publishResult` / `retrySignal` 不动。**`AssembledContent`（`types.ts:104`）逐字不改**。验证：`git diff src/publish-agent/types.ts` 中 `AssembledContent` 段 diff 为空、`npm run typecheck` 通过。

## 2. aidcp-cloud — 配图链路细拆（ImageDirector → ImagePlanner + ImageGenerator）

- [x] 2.1 新增 `src/publish-agent/roles/image-planner.ts`：继承 `BasePublishRole`，`watchKeys: ['createdContent']`、`outputKey: 'imagePlan'`、`fallback: 'default'`；承接现 `image-director.ts` Step 1（`buildImagePrompt` `prompts.ts:218` + `parseLlmOutput` + `executeWithFallback` `retry-strategy.ts:42`），含 `imageStyle` 钳到合法联合（默认 `'illustration'`，对齐现 `image-director.ts:96`，避免下游再钳）；LLM 失败 / 无 prompt → `getDefaultOutput` 返回 `wantImage:false` 计划。验证：单测桩 `QwenClient.chat` 覆盖"成功出 prompt / LLM 失败降级写 wantImage:false / 无 prompt 跳过"三路径。
- [x] 2.2 新增 `src/publish-agent/roles/image-generator.ts`：`watchKeys: ['imagePlan']`、`outputKey: 'imageDirective'`、`fallback: 'skip'`；承接现 Step 2（`imageProvider.generate` `image-provider.ts:20`）；`imagePlan.wantImage=false` 或无 `imagePrompt` → 不调图源、直接产空 `imageDirective`（`imageUrl:null`、带 `imagePlan.fallbackStrategy`）；生图失败 / 返回空 URL → 按 `imagePlan.fallbackStrategy` 降级为纯文字、**诚实写 `imageUrl:null`、绝不伪造 / 复用 URL、不维持 wantImage 假象**（spec 红线 Scenario）。`enableImageGeneration` 注入下沉到本角色。验证：单测桩 `ImageProvider.generate` 覆盖"生图成功 / 生图失败回 null 降级 / 计划不配图直接空 directive / enable=false"四路径。
- [x] 2.3 删除 `src/publish-agent/roles/image-director.ts`，把 `test/publish-agent/image-director.test.ts` 覆盖点迁移到 2.1 / 2.2 新单测（LLM 出 prompt / LLM 失败 / 无 prompt → Planner；生图成功 / 失败回 null / enable=false → Generator），不丢覆盖。验证：旧文件已删、`grep -rn ImageDirector src/ test/` 全仓零残留引用。

## 3. aidcp-cloud — 后处理链路细拆（ContentAssembler → Cleaner + AiFlavorScorer + QualityScorer + 瘦身 Assembler）

- [x] 3.1 新增 `src/publish-agent/roles/content-cleaner.ts`：`watchKeys: ['createdContent']`、`outputKey: 'cleanedContent'`、`fallback: 'default'`；**复用现有 `PostProcessor.process`（`post-processor.ts:65`，不改其实现）**，承接现 `content-assembler.ts:55` 清洗步；产出 `cleanedContent`（`PostProcessResult` `types.ts:28` 字段 + `cleanedAt`）。`execute` 内用 `executeWithFallback` 兜底、保证键必写（R1）。验证：单测桩 `PostProcessorLike.process` 覆盖"重写 / 不重写 / 处理异常降级仍写键"。
- [x] 3.2 新增 `src/publish-agent/roles/ai-flavor-scorer.ts`：`watchKeys: ['cleanedContent']`、`outputKey: 'aiFlavorScore'`、无外部依赖；从 `cleanedContent.aiScore` **显式投影**写 `aiFlavorScore { aiScore, scoredAt }`，不重算、不篡改、必写键。验证：单测断言 `aiFlavorScore.aiScore === cleanedContent.aiScore`（恒等投影）。
- [x] 3.3 新增 `src/publish-agent/roles/quality-scorer.ts`：`watchKeys: ['cleanedContent']`、`outputKey: 'qualityReport'`、`fallback: 'default'`；承接现 `content-assembler.ts` Step 2（`buildAssemblerPrompt` `prompts.ts:255` + `parseReviewOutput` 含 `qualityScore` 钳 0-100 + `executeWithFallback`），LLM 失败 / 非法 JSON 降级为 `qualityScore = round((1-aiScore)*70)`（**逐字沿用**现 `content-assembler.ts:66` 公式、绝不硬编码满分）；`execute` 内兜底保证键必写。验证：单测桩评审 LLM 覆盖"评审成功 / LLM 失败走 aiScore 公式（分数随 aiScore 变化）"两路径。
- [x] 3.4 瘦身 `src/publish-agent/roles/content-assembler.ts`：改为 `watchKeys: ['cleanedContent','aiFlavorScore','qualityReport','imageDirective','coverSelection']`、`waitAll: true`、`outputKey: 'assembledContent'`；**删 `llmClient` / `postProcessor` 依赖、纯组装、无 LLM / 无 IO**；字段映射（design D2）：`finalContent ← cleanedContent.content`、`finalTags ← createdContent.tags`（`extractInput` 从 snapshot 取、**不入 watchKeys**）、`imageUrl ← coverSelection.imageUrl`、`aiScore ← aiFlavorScore.aiScore`、`qualityScore ← qualityReport.qualityScore`、`rewritten`/`flaggedPhrases ← cleanedContent`、`assembledAt ← clock()`。验证：单测断言产出 `assembledContent` 八字段齐全且值来自各上游键；类型确认无 `llmClient` / `postProcessor` 依赖。
- [x] 3.5 迁移 `test/publish-agent/content-assembler.test.ts` 旧覆盖点至三处新单测（清洗 / 重写 → Cleaner、质量评审成功 / LLM 失败走公式 → QualityScorer、终稿组装八字段 → 瘦身 Assembler），不丢覆盖。验证：grep 确认旧测试场景均有新归属、无遗漏。

## 4. aidcp-cloud — 新增类型 / 封面角色（ContentTypeSelector + CoverSelector）

- [x] 4.1 新增 `src/publish-agent/roles/content-type-selector.ts`：`watchKeys: ['scoutDecision']`、`outputKey: 'contentType'`、覆写 `shouldActivate = scoutDecision.shouldPublish === true`（与 `ContentCreator` 守卫一致 `content-creator.ts:35`）；产出 `contentType { kind:'image_text', selectedAt }`（现恒图文、`kind` 联合类型预留 `video`/`text`）；**实体化为真实角色，不得在 `ContentAssembler` 或别处硬编码"一律图文"绕过**（spec 红线）。验证：单测覆盖"shouldPublish=true 产出 image_text / shouldPublish=false 守卫不通过不写键、不阻塞短路"。
- [x] 4.2 新增 `src/publish-agent/roles/cover-selector.ts`：`watchKeys: ['imageDirective']`、`outputKey: 'coverSelection'`、`fallback: 'default'`；单图直选 `{ imageUrl:<URL>, hasCover:true }`；无图（`imageDirective.imageUrl === null`）→ **诚实回 `{ imageUrl:null, hasCover:false }`、绝不选占位图 / 谎报 hasCover**（spec 红线）；多图选择留接口；`execute` 兜底保证键必写。验证：单测覆盖"有图选首图 / 无图回空封面"。

## 5. aidcp-cloud — server 注册替换（6 → 11，下游不动）

- [x] 5.1 `src/publish-agent/roles/index.ts`：移除 `ImageDirectorRole` 导出，新增 `ImagePlannerRole` / `ImageGeneratorRole` / `ContentCleanerRole` / `AiFlavorScorerRole` / `QualityScorerRole` / `ContentTypeSelectorRole` / `CoverSelectorRole` 导出（保留 `ContentScoutRole` / `ContentCreatorRole` / `ContentAssemblerRole` / `ApprovalGatekeeperRole` / `PublishExecutorRole`）。验证：`npm run typecheck` 通过。
- [x] 5.2 `src/server.ts` 替换生产段注册块（现 `server.ts:327-338` 含 import 块 `server.ts:56-61`）：删 `ImageDirectorRole` 注册，按 design D5 拓扑注册 `ContentScout` / `ContentTypeSelector` / `ContentCreator` / `ImagePlanner` / `ImageGenerator` / `CoverSelector` / `ContentCleaner` / `AiFlavorScorer` / `QualityScorer` / 瘦身 `ContentAssembler`；依赖按角色重新分配：`llm`→`ImagePlanner`/`QualityScorer`/`ContentTypeSelector`，`wanxiangClient`→`ImageGenerator`（含 `enableImageGeneration`），`postProcessor`→`ContentCleaner`；瘦身 `ContentAssembler` 注册去掉 `llmClient`/`postProcessor` 注入。验证：启动日志 / `getRoles()`（`publish-orchestrator.ts:135`）列出生产段对应 11 个角色名。
- [x] 5.3 确认 `ApprovalGatekeeperRole`（`server.ts:339`）/ `PublishExecutorRole`（`server.ts:340`）注册块**逐字未动**（仍 watch `assembledContent` / `gateDecision`），未触及协议 / edge / 下游源码。验证：`git diff src/server.ts` 中下游两块注册无改动、`git status` 未触及 `protocol.ts` / `command-bridge.ts` / `approval-gatekeeper.ts` / `publish-executor.ts`。

## 6. aidcp-cloud — 黑板拓扑健壮性（唯一生产者 + 不死锁，spec 第 6 项 Requirement）

- [x] 6.1 核对每个新键恰有唯一 `outputKey` 生产者：`contentType←ContentTypeSelector`、`imagePlan←ImagePlanner`、`imageDirective←ImageGenerator`、`cleanedContent←ContentCleaner`、`aiFlavorScore←AiFlavorScorer`、`qualityReport←QualityScorer`、`coverSelection←CoverSelector`、`assembledContent←ContentAssembler`，无两角色写同键；各生产者 `watchKeys` 指向真实上游键。验证：grep 各 `outputKey` 无重复、`npm run typecheck` 零报错。
- [x] 6.2 核对 `ContentAssembler` 的 `waitAll` 五键（`cleanedContent`/`aiFlavorScore`/`qualityReport`/`imageDirective`/`coverSelection`）各由"无论成败必写自己键"的角色生产（R1）：`ContentCleaner`/`QualityScorer`/`CoverSelector` 经 `fallback:'default'` + `execute` 内 `executeWithFallback` 兜底、`ImageGenerator` 经 `fallback:'skip'` + `getDefaultOutput`、`AiFlavorScorer` 纯投影必写。验证：各降级单测断言异常时仍写键；端到端注入"配图失败 + 评审失败"仍触发组装、不超时（见 6.5）。

## 7. aidcp-cloud — 测试（新角色单测 + orchestrator 不回归 + 全量回归）

- [x] 7.1 新角色单测齐全：`test/publish-agent/` 下 `image-planner` / `image-generator` / `content-cleaner` / `ai-flavor-scorer` / `quality-scorer` / `content-type-selector` / `cover-selector` 各一个；每个脱 LLM / 脱图源单测（桩 `QwenClient.chat` / `ImageProvider.generate` / `PostProcessorLike.process`）。验证：`npm test -- test/publish-agent` 新增用例全绿。
- [x] 7.2 更新瘦身后 `test/publish-agent/content-assembler.test.ts`：断言纯组装产出八字段、值来自 `cleanedContent`/`aiFlavorScore`/`qualityReport`/`coverSelection`/`createdContent`，确认无 LLM / IO。验证：该测试全绿。
- [x] 7.3 更新 `test/publish-agent/publish-orchestrator.test.ts`（现注册块 `:79-95` 与 `:174-179`）：注册改为 11 角色集，断言端到端**仍产出同形 `assembledContent`**（八字段 + 等价值，R5）、`gateDecision` / `publishResult` 与细拆前等价、`scoutDecision.shouldPublish=false` 短路仍 `skipped`、重复 `trigger` 仍 `skipped`、`getRoles()` 返生产段 11 名。验证：该测试全绿，断言覆盖稳定边界与角色集。
- [x] 7.4 安全红线回归：`npm run test:acceptance`（`AC-PROTO-*`（两份 protocol.ts 不漂移）/ `AC-PUB-*`（含审批信号文件契约不漂移）/ `AC-RISK-*` / `AC-E-*` 全过）。验证：acceptance 全绿。
- [x] 7.5 全量回归：`npm test` 全绿 + `npm run typecheck` 通过。验证：两命令均成功。

## 8. 收尾

- [x] 8.1 `openspec validate publish-content-media-roles --strict` 通过。验证：命令零报错。
- [x] 8.2 回写各 task 的 `[x]` + `<!-- aidcp-cloud <commit-sha> 备注 -->`；如部署 ECS（中控 §5 安全序列）则追加 `<!-- <date> deployed -->`。验证：tasks.md 全 `[x]` 且带回写注释。
