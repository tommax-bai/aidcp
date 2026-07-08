# Tasks — refine-curated-scrape-image-cap-18

> 抓取精选集参考图上限 30 → 18（= 小红书单帖图上界）。收窄 raise-curated-scrape-image-cap 的落点数值。发布侧 ≤9 不动。

## 1. aidcp-edge — 抽取上限

- [x] 1.1 `src/browse/note-extractor.ts`：`NOTE_IMAGE_HARD_MAX` 30 → 18，注解补「18 = 平台单帖图上界」 <!-- aidcp-edge a270caf -->

## 2. aidcp-cloud — 持久化上限

- [x] 2.1 `src/cache/curated-content-store.ts`：`CURATED_REFERENCE_IMAGE_DEFAULT_LIMIT` / `CURATED_REFERENCE_IMAGE_HARD_MAX` 30 → 18 <!-- aidcp-cloud 32c1f53 -->
- [x] 2.2 `test/cache/curated-content-store.test.ts`：上限单测 32→30 改 20→18；断言序列 [0..17] <!-- aidcp-cloud 32c1f53 -->

## 3. 验证与部署

- [x] 3.1 边端 typecheck + acceptance(15) + test(752) 全绿；云端 typecheck + acceptance(46) + test(1616) 全绿
- [x] 3.2 云端部署 dev + healthcheck（active / :8787 / CuratedContentStore 就绪 / 飞书长连 / 无错） <!-- 2026-07-09 deployed -->

## 4. 收口

- [x] 4.1 同步 revert 地雷：`curated-reference-images`（未归档）的 note-extraction-fidelity delta 与 design.md 由 30 收窄到 18
- [ ] 4.2 `openspec validate --strict` 通过 → archive（合并 live spec 到 18）
