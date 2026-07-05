# Tasks: Manual Billing-Derived Price Refresh

## 1. OpenSpec

- [x] 1.1 Specify manual provider/model price refresh semantics.
  <!-- control: openspec/changes/manual-billing-price-refresh proposal + llm-token-usage-stats delta -->
- [x] 1.2 Validate with `openspec validate manual-billing-price-refresh --strict`.
  <!-- local validation passed after implementation. -->

## 2. aidcp-cloud

- [x] 2.1 Update usage cost lookup to use the latest available billing-derived price for the same provider/model.
  <!-- aidcp-cloud e117071: /api/llm-usage now joins latest llm_billing_price_snapshot by provider/model. -->
- [x] 2.2 Add a manual panel endpoint that refreshes provider/model prices from T-1/T-2 billing samples.
  <!-- aidcp-cloud e117071: POST /api/llm-usage/prices/refresh; no cron or background worker. -->
- [x] 2.3 Infer billing provider for legacy unknown-provider usage rows when model names are recognizable.
  <!-- aidcp-cloud e117071: qwen/deepseek => dashscope; doubao/ep-* => volcengine. -->
- [x] 2.4 Return refresh diagnostics without exposing secrets.
  <!-- aidcp-cloud e117071: returns written/prices/skipped/missingCredentials only. -->
- [x] 2.5 Cover latest-price fallback and refresh target selection with tests.
  <!-- validated: npx tsx --test test/token-usage-store.test.ts test/billing-price-refresh.test.ts; npx tsx --test "test/**/*.test.ts"; npm run build. -->

## 3. aidcp-console

- [x] 3.1 Add a "update provider model pricing" action on the token usage page.
  <!-- aidcp-console 12cd65a: button text is 更新厂商模型定价. -->
- [x] 3.2 Show refresh result feedback and invalidate token usage queries after success.
  <!-- aidcp-console 12cd65a: mutation invalidates ['llm-usage'] and reports refresh diagnostics. -->
- [x] 3.3 Keep pending display only when no historical billing-derived price exists.
  <!-- aidcp-console 12cd65a + aidcp-cloud e117071: UI keeps column; cloud supplies latest historical price when available. -->

## 4. Closeout

- [x] 4.1 Run validation, commit, push, deploy cloud and console, and record notes.
  <!-- commits: aidcp-cloud e117071 pushed to master; aidcp-console 12cd65a pushed to master and included in deployed console head ec24083. -->
  <!-- validation: cloud relevant tests + full npx tsx --test "test/**/*.test.ts" + npm run build; console npm test + npm run build; openspec validate manual-billing-price-refresh --strict. -->
  <!-- deployment: ECS 121.89.85.150 updated 20260705-130923; backups cloud.bak.20260705-130923.tar.gz, cloud.env.bak.20260705-130923, console.bak.20260705-130923.tar.gz. Health: aidcp-cloud active, /api/health ok, /api/llm-usage/prices/refresh returns 401 without token, console bundle contains refresh action. -->
