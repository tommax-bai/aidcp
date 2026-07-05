# Tasks: Billing-Only Token Cost Estimates

## 1. OpenSpec

- [x] 1.1 Replace the previous public-price fallback spec with a billing-only rule.
- [x] 1.2 Validate with `openspec validate estimate-token-cost-column --strict`. <!-- 2026-07-05: passed locally. -->

## 2. aidcp-console

- [x] 2.1 Remove the hard-coded model price estimator and its unit test.
- [x] 2.2 Remove the estimated-cost column from `TokenUsagePage`.
- [x] 2.3 Run console tests and build. <!-- 2026-07-05: npm test passed 39 + 1 skipped; npm run build passed. -->

## 3. Closeout

- [x] 3.1 Commit, push, and deploy the console rollback. <!-- 2026-07-05: aidcp-console 57a5b7c pushed to master; deployed clean worktree dist to ECS at 20260705-104005; backup /opt/aidcp/console.bak.20260705-104005.tar.gz; 8088 root 200 and /api/health ok. -->
