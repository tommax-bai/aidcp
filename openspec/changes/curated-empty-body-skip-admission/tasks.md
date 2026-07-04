# Tasks: 空正文自有收藏不补建精选行

## 1. OpenSpec

- [x] 1.1 增加 spec delta，明确源帖精选以非空正文为前提；自有收藏空正文只补标记既有行、不新建壳行；模型准入空正文零 LLM。 <!-- aidcp this commit proposal/tasks + curated-inspiration-corpus/panel-curated-content deltas -->
- [x] 1.2 `openspec validate curated-empty-body-skip-admission --strict` 通过。 <!-- 2026-07-04 strict valid -->

## 2. aidcp-cloud

- [x] 2.1 修改 `CuratedContentStore.markBotAction('collect')`：无非空正文时只 `UPDATE` 既有源帖行 `bot_collected=true`，不 `INSERT`；`upsertObservation` 空正文 no-op。 <!-- aidcp-cloud 5d9b11a src/cache/curated-content-store.ts -->
- [x] 2.2 更新 store / evaluator 单测：有正文仍补建；视频媒体类型保持；无正文不补建壳行且只发 UPDATE；模型准入空正文不调 LLM；历史清理方法保留。 <!-- aidcp-cloud 5d9b11a test/cache/curated-content-store.test.ts + test/agents/curated-note-evaluator.test.ts -->
- [x] 2.3 运行 cloud 相关测试与 typecheck。 <!-- passed: npx tsx --test test/cache/curated-content-store.test.ts test/agents/curated-note-evaluator.test.ts test/panel-server.test.ts test/panel-curated-actions.test.ts (59 pass); npm run typecheck. Note: npm test single-quoted glob discovers 0 tests on Windows; double-quoted full glob timed out at 184s, not counted. -->

## 3. aidcp-console

- [x] 3.1 将精选页清理文案调整为“历史遗留空正文壳行清理”，避免暗示新数据仍会常规产生壳行。 <!-- aidcp-console 00f8901 src/pages/CuratedContentPage.tsx + test comment wording -->
- [x] 3.2 运行 console typecheck 或相关验证。 <!-- passed: npx vitest run src/pages/CuratedContentPage.test.tsx; npm run typecheck. Vitest emitted existing jsdom getComputedStyle warnings but tests passed. -->
