# Tasks: Billing-Backed Token Cost Estimates

## 1. OpenSpec

- [x] 1.1 Correct the product rule: keep the estimated-cost column, but require billing-derived data only.
- [x] 1.2 Validate with `openspec validate estimate-token-cost-column --strict`. <!-- 2026-07-05: passed locally. -->

## 2. aidcp-cloud

- [x] 2.1 Persist token usage with provider metadata so billing rows can distinguish Alibaba/DashScope from Volcengine/Ark.
- [x] 2.2 Add a billing-derived price snapshot table keyed by provider, model, and usage day.
- [x] 2.3 Extend `/api/llm-usage` rows with optional cost estimates derived from billing snapshots, never from hard-coded model prices.
- [x] 2.4 Cover provider persistence and billing-backed estimates with tests.
- [x] 2.5 Run cloud tests and build. <!-- 2026-07-05: npx tsx --test "test/**/*.test.ts" passed 1323; npm run build passed. -->

## 3. aidcp-console

- [x] 3.1 Restore the estimated-cost column immediately after total tokens.
- [x] 3.2 Render billing-backed cost values with source/date hints and pending states when billing data is unavailable.
- [x] 3.3 Run console tests and build. <!-- 2026-07-05: npm test passed 39 + 1 skipped; npm run build passed in main worktree; final deploy build will use a clean worktree. -->

## 4. Closeout

- [ ] 4.1 Commit, push, deploy cloud and console, and record validation/deployment notes.
