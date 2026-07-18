## 1. Contract

- [x] 1.1 Define creation-status classification, pagination, compatibility, and hidden-scrollbar behavior.
- [x] 1.2 Validate `split-curated-creation-status-filters` with strict OpenSpec validation before implementation. <!-- 2026-07-18 strict valid -->

## 2. Cloud

- [x] 2.1 Replace the client curated-list boolean filter with `uncreated | created | all` and apply account-scoped persisted rewrite-trigger existence predicates in SQL. <!-- aidcp-cloud 1a6d51f -->
- [x] 2.2 Keep main-page and offset-overrun COUNT queries on the identical filter and preserve honest unavailable behavior. <!-- main/COUNT share conds; two partial JSONB expression indexes added -->
- [x] 2.3 Update customer-auth route validation and focused store/server coverage for all three modes, exact legacy compatibility, account isolation, trigger-state independence, and pagination totals. <!-- focused 66/66 passed -->

## 3. Edge

- [x] 3.1 Replace the library tabs and per-environment default state with “未创作 / 已创作 / 全部”. <!-- aidcp-edge 0096411 -->
- [x] 3.2 Update main-process IPC mode validation, list empty states, state restoration, and focused renderer/security coverage. <!-- accepted trigger forces server reclassification reload; focused 23/23 passed -->
- [x] 3.3 Hide only the curated-list scrollbar while retaining overflow scrolling and add a style regression assertion. <!-- scrollbar-width:none + WebKit scrollbar hidden; overflow-y:auto retained -->

## 4. Verification and Integration

- [x] 4.1 Run focused tests, acceptance tests where defined, full tests, and typecheck in Cloud and Edge. <!-- Cloud acceptance 57/57; full direct Windows-safe glob 2519 total, 2511 pass, 8 gated skip; typecheck pass. Edge acceptance 25/25; full 1801/1801; typecheck pass. -->
- [x] 4.2 Commit, land, and push both implementations; deploy the runtime behavior to `dev` without building an Edge installer. <!-- Cloud master 1a6d51f; Edge master 0096411. dev backup cloud.bak.20260718-213254.tar.gz; active, 8787/8090/8091, both health endpoints, PG, two indexes, Feishu onReady, no startup errors, isales four services active. Live aggregate partition 344 = 7 created + 337 uncreated. No Edge installer built. -->
- [ ] 4.3 Record commit/deploy evidence, strictly validate, commit and push control changes, then archive the completed OpenSpec change.
