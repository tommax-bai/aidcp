## 1. Feishu Card Rendering

- [x] 1.1 Extend command result card data to accept an optional presentation-only `accountName`.
  <!-- repo=aidcp-cloud commit=5474800 added CommandResult.accountName as display-only metadata -->
- [x] 1.2 Render alert and command result visible account text as nickname-first with honest `accountId` fallback.
  <!-- repo=aidcp-cloud commit=5474800 renders accountName first and falls back to accountId without fabricating names -->

## 2. Cloud Wiring

- [x] 2.1 Inject existing `AccountStore.getNickname` into blocking-alert card creation so P0/P1 alert titles show nicknames when available.
  <!-- repo=aidcp-cloud commit=5474800 injects accountDisplayName into CaptchaCoordinator; alert storage/risk still use accountId -->
- [x] 2.2 Pass nickname display names into curated reference creation async result cards while keeping scheduler and persistence keyed by `accountId`.
  <!-- repo=aidcp-cloud commit=5474800 passes display names into async result cards and keeps scheduler inputs keyed by accountId -->

## 3. Verification

- [x] 3.1 Add focused cloud unit coverage for nickname-first Feishu alert and command result cards.
  <!-- repo=aidcp-cloud commit=5474800 adds card rendering and captcha coordinator coverage -->
- [x] 3.2 Run focused cloud tests for touched Feishu/captcha paths.
  <!-- validation=cd ../aidcp-cloud.wt/feishu-account-nickname-cards && npx tsx --test test/feishu-cards.test.ts test/comm/captcha-coordinator.test.ts passed 24/24; npm test passed 1376/1376 -->
- [x] 3.3 Run `npm run typecheck` in `aidcp-cloud`.
  <!-- validation=cd ../aidcp-cloud.wt/feishu-account-nickname-cards && npm run typecheck passed -->
- [x] 3.4 Run `openspec validate feishu-account-nickname-cards --strict`.
  <!-- validation=openspec validate feishu-account-nickname-cards --strict passed -->
