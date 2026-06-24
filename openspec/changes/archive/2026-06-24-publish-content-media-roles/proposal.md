# 发帖流水线生产段角色细拆（阶段2）：内容生产 + 配图按"一角色一职"重组

## Why

- **粗角色把决策与执行揉在一起，难独立重试 / 降级 / 测试**：
  - `ImageDirectorRole`（`aidcp-cloud/src/publish-agent/roles/image-director.ts`）一个角色既做**决策**
    （LLM 算配图 prompt / 风格 / 要不要配图）又做**执行**（调通义万相 `imageProvider.generate` 拿 URL、失败降级）。
    决策 LLM 失败和图片生成失败混在同一个 `execute` / 同一个 `fallback: 'skip'` 里，无法对"决策"和"生图"
    分别设超时、分别重试、分别降级；单测要同时桩 LLM 与 imageProvider 才能覆盖一条路径。
  - `ContentAssemblerRole`（`aidcp-cloud/src/publish-agent/roles/content-assembler.ts`）一个角色三合一：
    **清洗**（`postProcessor.process` 去 AI 味）+ **评分**（`aiScore` 由清洗算、`qualityScore` 由 LLM 评审算）
    + **组装**（拼 `assembledContent`）。三步耦合在一个 `execute` 里，清洗失败、AI 味评分、质量评审 LLM 失败
    各自的降级语义被压成一个 `fallback: 'default'`；想单独回归"质量评审"或"去 AI 味"必须连带跑整段。
- **与浏览侧"一角色一职"不对齐**：浏览闭环（`RoleDispatcher` + 15 角色）已是细粒度单职责角色，
  每个角色一件事、可独立替换与单测；发帖流水线生产段却仍是 2~3 件事一个角色的粗粒度，演进路线不统一。
- **细拆收益**：决策与执行解耦后，可对"生图"单独加重试 / 切换图源 / A-B，对"质量评分"单独调阈值与回归，
  对"去 AI 味"单独迭代禁用词；每个新角色一个 watch / 一个 write，符合黑板流水线（`PipelineContext`
  watch/write）的协作模型，且每个角色都能脱 LLM / 脱图源单测。

## What Changes

- **BREAKING（流水线角色重组）**：发帖流水线**生产段**的粗角色按"种类级"（版本 A，参数化但仍按内容种类划分）
  细拆。`PublishOrchestrator.getRoles()` 注册角色集合与名称发生变化（6 → 11），依赖角色名 / 注册数的测试需更新。
  仅重组**黑板流水线（`PipelineContext` watch/write）内部**的生产段，不改协议、不改 edge、不改下游消费方。
- **`ImageDirector` → `ImagePlanner` + `ImageGenerator`**：
  - `ImagePlanner`（决策）：watch `createdContent` → 决定要不要图 / 配图 prompt / 风格 / 张数，写新键 `imagePlan`。
  - `ImageGenerator`（执行）：watch `imagePlan` → 调通义万相生成 URL，失败按计划的 `fallbackStrategy` 降级，写 `imageDirective`。
- **`ContentAssembler` → `ContentCleaner` + `AiFlavorScorer` + `QualityScorer` + `ContentAssembler`（瘦身）**：
  - `ContentCleaner`（清洗）：watch `createdContent` → 复用现有 `PostProcessor`（`post-processor.ts`）去 AI 味，写新键 `cleanedContent`。
  - `AiFlavorScorer`（AI 味评分）：从清洗结果产出 `aiScore`，写新键 `aiFlavorScore`。
  - `QualityScorer`（质量评分）：watch `cleanedContent` → LLM 质量评审产出 `qualityScore`，写新键 `qualityReport`。
  - `ContentAssembler`（瘦身）：watchAll 清洗 / 评分 / 配图就绪 → **仅组装终稿**，写**同形** `assembledContent`。
- **新增 `ContentTypeSelector`**：watch `scoutDecision` → 决定内容类型（图文 / 视频 / 文字；现恒图文，预留），写新键 `contentType`。
- **新增 `CoverSelector`**：watch `imageDirective` → 从生成图里选封面（现单图直接用，预留多图），写新键 `coverSelection`。
- **`ContentScout` / `ContentCreator` 保持不变**。
- **稳定边界铁律**：`assembledContent` 形状不变——下游 `ApprovalGatekeeper`（watch `assembledContent`）与
  `PublishExecutor`（watch `gateDecision`）**零改动**；细拆只改生产段，最终仍产出同形
  `assembledContent { finalContent, finalTags, imageUrl, aiScore, qualityScore, rewritten, flaggedPhrases, assembledAt }`。
- **不做**（划出本阶段边界）：
  - 触发器（`PublishScheduler` / `trigger`）与触发逻辑不动。
  - 元数据维度决策器（话题 / @ / 地点 / 可见范围 / 合规）属阶段3，不做。
  - 来源血缘 `LikedNoteStore`、删 `temp` 口、edge 配图上传（stage-1 已诚实回 `kind_not_implemented`，真上传属后续）。
  - 不碰协议（`docs/protocol.md` / 两份 `protocol.ts`）、不碰 edge、不碰下游消费方。

## Capabilities

### New Capabilities

- `publish-pipeline`：发帖流水线（黑板式生产段编排）的角色职责与稳定边界契约。本阶段引入"生产段单职责角色 +
  `assembledContent` 稳定边界"要求。与发帖流水线 stage-1（边缘指令运行时）属同一 capability 演进序列，
  归档时合并入 `openspec/specs/publish-pipeline/`。

### Modified Capabilities

<!-- 无既有 spec 被修改：publish-pipeline 为新建 capability。本 change 仅 ADDED Requirements。 -->

## Impact

- **aidcp-cloud（唯一受影响仓，分支 `master`）**：
  - `src/publish-agent/types.ts`：新增 `imagePlan` / `cleanedContent` / `aiFlavorScore` / `qualityReport` /
    `contentType` / `coverSelection` 类型与 `PipelineFields` 键；`assembledContent`（`AssembledContent`）保持同形。
  - `src/publish-agent/roles/`：新增 `image-planner.ts` / `image-generator.ts` / `content-cleaner.ts` /
    `ai-flavor-scorer.ts` / `quality-scorer.ts` / `content-type-selector.ts` / `cover-selector.ts`；
    瘦身 `content-assembler.ts`；删除 / 拆解 `image-director.ts`；更新 `roles/index.ts` 导出。
  - `src/server.ts`：替换生产段角色注册（6 → 11），下游 `ApprovalGatekeeper` / `PublishExecutor` 注册不动。
  - `test/publish-agent/`：新角色单测 + `publish-orchestrator.test.ts` 角色集 / 端到端不回归（仍产出同形 `assembledContent`）。
- **不影响**：协议（edge / cloud 两份 `protocol.ts`、`command-bridge.ts`、`docs/protocol.md`）、aidcp-edge、
  下游消费方（`ApprovalGatekeeper` / `PublishExecutor` / 审批信号文件契约 / `publish-log` 写入）、风控、浏览闭环。
