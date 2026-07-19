## 1. Contract and Cloud authority

- [x] 1.1 Extend provisioning completion with a strictly validated optional Facebook-only slow-start intent while preserving old request compatibility.
  <!-- repo: aidcp-cloud; commit: f5605d6; validation: focused client-auth/store tests PASS; deviations: none -->
- [x] 1.2 Persist the Shanghai-day slow-start anchor atomically with first registration/ownership and keep completed-intent retries read-only.
  <!-- repo: aidcp-cloud; commit: f5605d6; validation: store SQL/unit coverage PASS; PostgreSQL-gated assertion added but local DB gate was not enabled; deviations: none -->
- [x] 1.3 Add Cloud store/server tests for Facebook enablement, non-Facebook rejection, omitted-field compatibility, rollback, and idempotency.
  <!-- repo: aidcp-cloud; commit: f5605d6; validation: focused PASS 57 with 4 PostgreSQL-gated skips; full direct tsx PASS 2531 with 8 gated skips; deviations: npm test on Windows discovered 0 tests due existing single-quote glob, so full validation used direct PowerShell npx tsx glob -->

## 2. Edge creation behavior

- [x] 2.1 Make every Facebook single and batch creation completion request enable slow start while XHS and WeChat Channels omit the concept.
  <!-- repo: aidcp-edge; commit: db11ac0; validation: main-contract + renderer focused suite PASS 65/65; deviations: none -->
- [x] 2.2 Carry a verified non-sensitive slow-start result in creation receipts and add honest Facebook creation guidance without changing credential handling.
  <!-- repo: aidcp-edge; commit: db11ac0; validation: renderer secret-safety and success/partial-state coverage PASS; deviations: none -->
- [x] 2.3 Add focused Edge main-contract and renderer coverage for single, batch, cross-platform, and partial-assignment results.
  <!-- repo: aidcp-edge; commit: db11ac0; validation: focused PASS 65/65; deviations: none -->

## 3. Validation and delivery

- [x] 3.1 Run focused Cloud and Edge tests plus typecheck/build checks proportionate to the touched runtime paths.
  <!-- repos: aidcp-edge db11ac0, aidcp-cloud f5605d6; validation: focused Edge 65/65, focused Cloud 57 pass + 4 gated skips, both typecheck PASS, both build PASS; deviations: none -->
- [x] 3.2 Run full required suites and `openspec validate facebook-default-slow-start --strict`.
  <!-- repos: aidcp-edge db11ac0, aidcp-cloud f5605d6; validation: Edge post-rebase acceptance 25/25 and full 1834/1834; Cloud full direct tsx 2531 pass + 8 gated skips; strict OpenSpec rerun before and after integration; deviations: no live account/profile creation -->
- [x] 3.3 Commit, integrate, push, deploy Cloud to dev, and record validation/deployment evidence; do not package an Edge installer without an explicit request.
  <!-- delivery: edge db11ac0 pushed to origin/master; cloud f5605d6 pushed to origin/master and deployed as part of clean master b1eccf7 to dev; backup cloud.bak.20260719-120652.tar.gz plus matching env backup; health: service active, NRestarts=0, 8787 and 8090 listening, PostgreSQL select 1, Feishu WSClient onReady, deployed source SHA-256 matched local; Edge installer intentionally not packaged -->
