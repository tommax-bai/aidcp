## Why

抓取精选集（curated inspiration corpus）时，单条笔记的参考图上限被封在 9 张——边端抽取（`NOTE_IMAGE_HARD_MAX=9`）与云端精选库持久化（`CURATED_REFERENCE_IMAGE_DEFAULT_LIMIT/HARD_MAX=9`）两处都硬夹 9。小红书图文笔记实际最多 18 张图，9 的上限会把多图源稿截半，洗稿创作可用的视觉参照池随之变薄。运营希望精选参照池尽量存全源稿的图，把上限抬到 30（留足冗余，覆盖平台当前 18 张上界并留增长空间）。

关键前提：**抓取参照池上限**与**发布侧配图张数**是两套独立的「9」。发布侧的 `IMAGE_COUNT_HARD_MAX` / `REFERENCE_IMAGE_MAX_COUNT` = 9 是小红书图文帖每帖最多 9 张图的**平台硬约束**，本变更**不动**。参照池刻意存更多、发布生成仍只取其中 ≤9 张——存的多、发的少，二者解耦。

## What Changes

- 边端 `NOTE_IMAGE_HARD_MAX` 9 → 30：单条笔记轮播图抽取上限。
- 云端 `CURATED_REFERENCE_IMAGE_DEFAULT_LIMIT` / `CURATED_REFERENCE_IMAGE_HARD_MAX` 9 → 30：精选库每行参考图持久化上限（写入 normalize + 读取 re-clamp 两条路径共用）。
- 更新与之耦合的云端上限单测（10 张输入截 9 → 32 张输入截 30）。
- **不改**：发布侧任何配图张数上限（小红书 ≤9 平台硬约束）；边端翻图浏览张数（`VIEW_ALL_IMAGE_CAP=18`，已等于平台每帖图上界，「尽量看完」即已覆盖，无需抬）。

## Capabilities

### New Capabilities
<!-- 无新增 capability。 -->

### Modified Capabilities
- `curated-inspiration-corpus`：「精选参考图默认保留平台上限」要求——默认与硬上限由 9 提到 30；措辞澄清参照池与发布侧 ≤9 解耦。
- `note-extraction-fidelity`：「翻图后回传完整图片快照」要求——抽取数量上限由 9 提到 30。

## Impact

- **aidcp-edge**：`src/browse/note-extractor.ts`（`NOTE_IMAGE_HARD_MAX`）。运营机边端生效，无 ECS 部署。
- **aidcp-cloud**：`src/cache/curated-content-store.ts`（两个常量）+ `test/cache/curated-content-store.test.ts`。ECS 纯代码落 dev。
- **不改**：协议 / 风控 / 发布下发上传链 / 封面形态 / 发布侧配图张数；无 DB 迁移（`reference_images` 为 JSONB，无长度约束）；无 env 强制项。
- **代价**：多图源稿单行 `reference_images` JSON 略变大（≤30 条轻量元数据对象），可忽略。
