## Why

上一改动（`raise-curated-scrape-image-cap`，同日归档）把抓取精选集的参考图上限从 9 抬到 30，留了冗余。运营复核后定为 **18** —— 18 正是小红书单帖图片数上界，等于「一篇笔记的图全存下来」，既不再被旧的 9 截半，也不留无意义的余量。属对上一改动落点数值的收窄修正。

前提不变：**抓取参照池上限**（本次 18）与**发布侧配图张数**（小红书 ≤9 平台硬约束）仍是两套独立的数，发布侧不动。

## What Changes

- 边端 `NOTE_IMAGE_HARD_MAX` 30 → 18。
- 云端 `CURATED_REFERENCE_IMAGE_DEFAULT_LIMIT` / `CURATED_REFERENCE_IMAGE_HARD_MAX` 30 → 18。
- 更新耦合的云端上限单测（32→30 改 20→18）。
- **不改**：发布侧任何配图张数上限（≤9 平台硬约束）；边端翻图浏览张数（`VIEW_ALL_IMAGE_CAP=18`，现与抽取/存储上限完全对齐）。

## Capabilities

### New Capabilities
<!-- 无新增 capability。 -->

### Modified Capabilities
- `curated-inspiration-corpus`：「精选参考图默认保留平台上限」要求——默认与硬上限由 30 收窄到 18（= 平台单帖图上界）。
- `note-extraction-fidelity`：「翻图后回传完整图片快照」要求——抽取数量上限由 30 收窄到 18。

## Impact

- **aidcp-edge**：`src/browse/note-extractor.ts`。运营机边端生效，无 ECS 部署。
- **aidcp-cloud**：`src/cache/curated-content-store.ts` + `test/cache/curated-content-store.test.ts`。ECS 纯代码落 dev。
- **不改**：协议 / 风控 / 发布链 / 发布侧配图张数；无 DB 迁移；无 env 强制项。既存 `reference_images` 里 >18 张的历史行（若有）在下次观测刷新时按 18 归一，不主动回填。
