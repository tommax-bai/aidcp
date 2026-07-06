## Why

参照洗稿来源行已经可以保存并展示最多 9 张参考图，但发布生成链路仍把参考图截断为 3 张，导致内容页审计显示“参考图 3 张”，且图片模型只能看到前三张。这个差异会降低洗稿配图对原文图集的保真度，也会让运营误以为精选池图片没有抓全。

## What Changes

- 将参照洗稿发布链路的可用参考图上限从 3 张提升到 9 张，与精选内容池当前参考图保存/展示上限一致。
- 统一冻结到 `referenceNote.images`、图片 prompt guidance、图片 provider 输入和发布审计的参考图数量口径。
- 保持“仅文本参考”模式不传参考图，普通发布不生成参考图审计。
- 不直接复用或发布原图；参考图仍只作为生成阶段的视觉指导输入。

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `publish-multi-image`: 参照洗稿图片生成链路应最多携带 9 张来源参考图，并按实际携带数量记录审计。

## Impact

- Affected repo: `../aidcp-cloud`.
- Affected modules: publish scheduler reference-image freeze, image prompt guidance, image generator provider input, related unit tests.
- No database migration or API shape change: existing `referenceImageAudit` fields continue to be used, with counts reflecting the expanded limit.
- Production behavior changes after cloud deployment to `dev`.
