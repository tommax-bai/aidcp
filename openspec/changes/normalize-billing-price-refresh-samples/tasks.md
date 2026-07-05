## 1. Cloud Billing Sample Matching

- [x] 1.1 Create/use the `normalize-billing-price-refresh-samples` worktree for `aidcp-cloud` and confirm it is based on the latest `master`. <!-- worktree: ../aidcp-cloud.wt/normalize-billing-price-refresh-samples on codex/normalize-billing-price-refresh-samples from origin/master 24b27a3 -->
- [x] 1.2 Add deterministic provider-specific billing model matching for Volcengine runtime ids versus billing labels, while preserving exact matching and honest `no_billing_sample` behavior. <!-- aidcp-cloud worktree: provider-specific Volcengine alias matching added; exact matching preserved; Count/Unit token quantity and same-row Price/PriceUnit handling added for rounded Volcengine rows -->
- [x] 1.3 Add focused cloud tests covering Volcengine `doubao-seed-2-0-pro-260215` / `doubao-seed-character-260628` billing rows and absent DashScope samples. <!-- aidcp-cloud worktree: npx tsx --test test/billing-price-refresh.test.ts passed (7 tests) -->
- [x] 1.4 Include Aliyun discounted zero-payable billing rows and derive DashScope price from positive same-row gross amount fields. <!-- aidcp-cloud c6f336f: IsHideZeroCharge=false; positive net amount, then positive gross amount, then same-row unit price; zero-only rows stay no_billing_sample -->
- [x] 1.5 Add focused cloud tests covering Aliyun `PretaxAmount=0` plus positive `PretaxGrossAmount` rows and zero-only rows that remain skipped. <!-- aidcp-cloud: npx tsx --test test/billing-price-refresh.test.ts passed (9 tests) -->

## 2. Console Refresh Result Reporting

- [x] 2.1 Create/use the `normalize-billing-price-refresh-samples` worktree for `aidcp-console` and confirm it is based on the latest `master`. <!-- worktree: ../aidcp-console.wt/normalize-billing-price-refresh-samples on codex/normalize-billing-price-refresh-samples from origin/master 2b5d43a -->
- [x] 2.2 Add operator-facing skipped-reason labels and aggregate refresh result formatting for `/usage`. <!-- aidcp-console worktree: formatBillingPriceRefreshMessage aggregates skip reason counts and credential labels -->
- [x] 2.3 Update the refresh action to show a non-green outcome when zero rows are written and targets were skipped, and add focused console test coverage. <!-- aidcp-console worktree: npx vitest run src/pages/tokenUsagePriceRefresh.test.ts passed (2 tests) -->

## 3. Validation

- [x] 3.1 Run relevant `aidcp-cloud` tests/build for billing refresh changes. <!-- aidcp-cloud worktree: npx tsx --test test/billing-price-refresh.test.ts passed (7); npm test passed (1352); npm run build passed; deploy snapshot 695c973 focused test/build passed -->
- [x] 3.2 Run relevant `aidcp-console` tests/build for usage page changes. <!-- aidcp-console worktree: npx vitest run src/pages/tokenUsagePriceRefresh.test.ts passed (2); npm test passed (45 passed, 1 skipped); npm run build passed; existing jsdom getComputedStyle and Vite chunk-size warnings only -->
- [x] 3.3 Run `openspec validate normalize-billing-price-refresh-samples --strict`. <!-- passed -->
- [x] 3.4 Run follow-up `aidcp-cloud` tests/build and `openspec validate normalize-billing-price-refresh-samples --strict`. <!-- aidcp-cloud worktree: npx tsx --test test/billing-price-refresh.test.ts passed (9); npm test passed (1354); npm run build passed; deploy snapshot c6f336f focused test/build passed; openspec validate normalize-billing-price-refresh-samples --strict passed -->

## 4. Closeout

- [x] 4.1 Commit and push `aidcp-cloud` changes to the default branch after fast-forward integration. <!-- aidcp-cloud a6c0695 and 695c973 pushed to master; validation: npx tsx --test test/billing-price-refresh.test.ts, npm test, npm run build -->
- [x] 4.2 Commit and push `aidcp-console` changes to the default branch after fast-forward integration. <!-- aidcp-console 79bf971 pushed to master; validation: npx vitest run src/pages/tokenUsagePriceRefresh.test.ts, npm test, npm run build -->
- [x] 4.3 Commit and push control-repo OpenSpec artifacts. <!-- aidcp ad1260f pushed initial OpenSpec; 07ccfde records design/spec/tasks closeout; openspec validate normalize-billing-price-refresh-samples --strict passed -->
- [x] 4.4 Deploy cloud and publish console, then verify the production refresh outcome no longer hides skipped reasons and Volcengine samples can write when billing rows are present. <!-- deployed: aidcp-console 79bf971 to /opt/aidcp/console; aidcp-cloud 695c973 to ECS after backups 20260705-164126 and 20260705-164842; health active with ports 8787/8090/8088, Feishu WS ready, PG select 1, console 200; production refresh written=3 targetCount=10 skipped no_billing_sample=7 missingCredentials=0; DB confirmed 3 Volcengine snapshots -->
- [x] 4.5 Commit, push, deploy, and verify the Aliyun discounted-row follow-up. <!-- aidcp-cloud c6f336f pushed to master and deployed to ECS after backup 20260705-170333; health active with ports 8787/8090/8088, Feishu WS ready, PG select 1, console 200; production refresh written=6 targetCount=10 skipped no_billing_sample=4 missingCredentials=0; DB confirmed 3 DashScope snapshots -->
