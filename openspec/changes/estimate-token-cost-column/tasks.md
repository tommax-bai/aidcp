# Tasks: Token Usage Estimated Cost Column

## 1. OpenSpec

- [x] 1.1 Add spec delta for the console usage estimated-cost column.
- [x] 1.2 Validate with `openspec validate estimate-token-cost-column --strict`. <!-- 2026-07-05: passed locally. -->

## 2. aidcp-console

- [x] 2.1 Add a small model-name based token cost estimator with known DashScope and Volcengine text model prices. <!-- aidcp-console 87554d0 -->
- [x] 2.2 Insert the estimated-cost column immediately after total token in `TokenUsagePage`. <!-- aidcp-console 87554d0 -->
- [x] 2.3 Add focused tests for known and unknown model estimates. <!-- aidcp-console 87554d0 -->
- [x] 2.4 Run console typecheck and tests. <!-- 2026-07-05 after rebase: npm test passed 42 + 1 skipped; npm run build passed; openspec validate estimate-token-cost-column --strict passed. -->

## 3. Closeout

- [x] 3.1 Commit and push OpenSpec + console changes; deploy console if validation passes. <!-- aidcp-console 87554d0 pushed to master; console deployed from dist at 20260705-084101; backup /opt/aidcp/console.bak.20260705-084101.tar.gz; 8088 root 200, /api/health ok, index serves /assets/index-FG8Hdw3u.js. -->
