# Tasks — raise-curated-scrape-image-cap

> 抓取精选集参考图上限 9 → 30；边端抽取 + 云端持久化两处同抬。发布侧 ≤9 平台硬约束不动。

## 1. aidcp-edge — 抽取上限

- [x] 1.1 `src/browse/note-extractor.ts`：`NOTE_IMAGE_HARD_MAX` 9 → 30，加注解澄清与发布侧 9 无关 <!-- aidcp-edge 2db61b9 -->

## 2. aidcp-cloud — 持久化上限

- [x] 2.1 `src/cache/curated-content-store.ts`：`CURATED_REFERENCE_IMAGE_DEFAULT_LIMIT` / `CURATED_REFERENCE_IMAGE_HARD_MAX` 9 → 30，加注解澄清解耦 <!-- aidcp-cloud 8e69ed5 -->
- [x] 2.2 `test/cache/curated-content-store.test.ts`：上限单测 10→9 改 32→30；断言序列改为 [0..29] <!-- aidcp-cloud 8e69ed5 -->

## 3. 验证

- [x] 3.1 边端：`npm run typecheck` + `npm run test:acceptance`(14) + `npm test`(746) 全绿 <!-- aidcp-edge -->
- [x] 3.2 云端：`npm run typecheck` + `npm run test:acceptance`(45) + `npm test`(1588) 全绿 <!-- aidcp-cloud -->
- [x] 3.3 对抗性核验（4-agent workflow）：抓取路径无残留 9；发布 ≤9 平台约束不受影响（已证）
- [x] 3.4 云端部署 dev + healthcheck（service active / :8787 / CuratedContentStore 就绪 / 飞书长连 / 无错） <!-- 2026-07-08 deployed -->

## 4. 收口

- [x] 4.1 拆除 revert 地雷：把已完成未归档 change `curated-reference-images` 里 note-extraction-fidelity delta 与 design.md 的「上限 9」改 30，防其归档时把 live spec 上限退回 9
- [x] 4.2 `openspec validate raise-curated-scrape-image-cap --strict` 通过 → archive
