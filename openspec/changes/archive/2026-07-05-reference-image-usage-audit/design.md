## Context

`curated-reference-images` 已经让精选行保存原文图片，并在参照洗稿触发时把图片快照传入 `referenceNote.images`。但当前图片 provider 路径仍可能是文生图：`SeedreamClient` 和 `WanxiangClient` 在收到 `referenceImages` 时会返回 `referenceStatus: 'unsupported'`，表示没有实际使用参考图。`ImageGenerator` 已能汇总这个状态到 `imageDirective.referenceImageStatus`，但该字段没有落库，也没有在内容面板展示。

## Goals / Non-Goals

**Goals:**
- 将 `imageDirective.referenceImageStatus` 与参照图片数量持久化到发布记录的 `publish_metadata`。
- 面板 API 和 console 展示该审计信号，使运营能判断“带图参考”是否真的被 provider 使用。
- 历史记录、普通发布、无参考图发布保持兼容。

**Non-Goals:**
- 不接入或验证新的图生图 / 图像编辑 provider。
- 不直接复用原文图片作为发布图。
- 不改变配图张数、生成 prompt、审批、人审或下发逻辑。
- 不修改 `publish_log` 表结构；审计走现有 `publish_metadata` JSONB。

## Decisions

### D1. 审计写入 `publish_metadata.referenceImageAudit`

`publish_metadata` 已是发布候审段的 JSONB 审计与下发重建载体，适合加性扩展。新增结构：

```ts
referenceImageAudit?: {
  requestedCount: number;
  usableCount: number;
  status: 'none' | 'used' | 'unsupported' | 'unavailable' | 'skipped';
  providerClaimedUsed: boolean;
  generatedCount: number;
}
```

`requestedCount` 来自触发输入中的 `referenceNote.images.length`，`usableCount` 来自实际有 `ossUrl/sourceUrl` 的图片数，`status` 来自 `imageDirective.referenceImageStatus`。历史记录缺字段时读侧返回 `null`。

### D2. 在 `PublishExecutor` 汇总而非 `MetadataAggregator`

`MetadataAggregator` 与配图链并行，不能稳定读取 `imageDirective`。`PublishExecutor` 激活时标题、审批门、元数据已就绪，且通过 `assembledContent` 间接保证配图链完成；此时从 context 读取 `imageDirective` 和 `trigger.generateInput.referenceNote` 汇总审计，时序稳定。

### D3. 面板投影加字段，前端只读展示

`GET /api/content/published` 的每条 `PanelPublish` 增加 `imageReferenceAudit: null | ...`。console 在详情浮层的配图说明下方展示：
- `used`: 参考图已被图片模型使用；
- `unsupported`: 当前图片厂商不支持参考图，已按文本重新生成；
- `unavailable`: 参考图不可用；
- `skipped`: 本次未传参考图；
- `none` / `null`: 不展示或显示无参考图。

## Risks / Trade-offs

- [Risk] 审计字段只覆盖新生成记录，历史记录仍缺失。
  - Mitigation: 读侧返回 `null`，前端不编造状态；必要时后续按发布日志回填。
- [Risk] provider 将来支持参考图但未正确返回 `used`。
  - Mitigation: 继续以 provider 返回值为真相；新 provider 接入时必须单测断言 `referenceStatus='used'`。
- [Risk] 运营可能把 `unsupported` 当成失败。
  - Mitigation: 文案明确“已按文本重新生成”，不影响草稿可审，但说明视觉不保真原因。
