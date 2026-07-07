## Context

`GET /api/content/queue` returns `PublishOrchestrator.getStatus()`: a `status` string and the current `PipelineContext.snapshot()` while a generation run is active. The snapshot shape is intentionally the publish blackboard and contains many internal keys such as `trigger`, `referenceAnalysis`, `faithfulDraft`, `createdContent`, `imagePlan`, `publishMetadata`, and `publishResult`.

The console currently renders every top-level snapshot key in a bordered `Descriptions` list. That is useful for debugging but poor for operations: the most important question is "where is the active draft in the generation lane?"

## Decisions

### Stage Model

The console will derive display stages from known snapshot keys without changing the API:

1. `来源/触发`: `trigger`.
2. `洗稿/正文`: reference rewrite keys (`referenceAnalysis`, `faithfulRewritePlan`, `faithfulDraft`, `fidelityAuditReport`) or normal creation keys (`scoutDecision`, `createdContent`).
3. `质检/清洗`: `cleanedContent`, `aiFlavorScore`, `qualityReport`, `assembledContent`, `titleSelection`.
4. `配图/元数据`: `postCategory`, `imageSetPlan`, `imagePlan`, `imageDirective`, `coverSelection`, metadata decision keys, `publishMetadata`.
5. `人审/下发`: `gateDecision`, `publishResult`.

Each stage is `done` when any mapped key is present, `active` when it is the first not-yet-done stage after prior progress, and `pending` otherwise. For idle/no snapshot, the page shows only the status and an empty-state hint instead of a fake pipeline.

### Information Density

The overview shows one row of compact stage cells plus short facts derived from the snapshot:

- account id / source title / source author / source image count from `trigger.generateInput.referenceNote`;
- generated title/content length from `createdContent`, `faithfulDraft`, or `titleSelection`;
- image count from `imageDirective.imageUrls`, `imagePlan.imageCount`, or `imageSetPlan.imageCount`;
- final publish result status and record id when present.

Text is truncated with CSS and tooltips/ellipsis where AntD already supports it. Raw values remain in a collapsed "原始字段" panel so future keys remain observable.

### Scope

This is a console-only presentation change. It MUST NOT add queues, parallelize the publish orchestrator, modify the global serial publish lane, or change `/api/content/queue`.

## Risks

- Unknown future snapshot fields may not be represented in the stage summary. Mitigation: raw fields remain visible in the secondary disclosure.
- Snapshot values may be partial while a role is running. Mitigation: stages are progress indicators, not success claims; only present keys are marked complete.
- Very long source/title/content text can crowd the card. Mitigation: use compact metadata chips and CSS truncation.
