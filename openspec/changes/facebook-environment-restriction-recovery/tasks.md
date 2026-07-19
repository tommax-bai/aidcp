## 1. Facebook blocking classification

- [x] 1.1 Update the Edge Facebook overlay classifier so positive captcha evidence stays immediate while generic checkpoint/security-check evidence becomes persistence-confirmed `unknown` and two-step verification remains an identity block.
- [x] 1.2 Add focused classifier and report-gate tests covering checkpoint without captcha, checkpoint with captcha, identity routes, and the AIDCP persona notice non-signal boundary.

## 2. Cloud environment risk API

- [x] 2.1 Add a serialized `RiskController` restricted-only recovery operation with non-empty reason validation, idempotent-normal behavior, and refusal for warned/frozen.
- [x] 2.2 Add customer-auth `GET /environments/:envKey/risk-state` and `POST /environments/:envKey/risk-state/recover` routes with ownership, binding, Facebook-platform, empty-body, response allowlist, and audit logging guards.
- [x] 2.3 Inject controller read/recovery and account-edge resume dependencies from the Cloud runtime without changing protocol or database schema.
- [x] 2.4 Add focused Cloud tests for authoritative offline reads, authorization/platform/body failures, restricted recovery, idempotency, refusal states, write-after receipts, and resumed-edge counts.

## 3. Electron compact recovery surface

- [x] 3.1 Add named preload/main IPC methods that accept only `envKey`, call the customer-auth risk routes, and preserve the existing response environment scope guard.
- [x] 3.2 Add the static compact `解除受限 / ?` row under “今日进展”, including accessible help content and narrow-window-safe styling; keep the explicit `账号受限` label in the existing status projections instead of duplicating it in the row.
- [x] 3.3 Add selected-environment risk fetch/cache and recovery rendering logic with Facebook-only visibility, confirmation, pending/error truthfulness, write-after convergence, and environment isolation.
- [x] 3.4 Replace restricted-state euphemisms with explicit `账号受限` wording in health, detail, and rail projections, and add focused UI logic/renderer/IPC contract tests.
  <!-- Edge focused UI/IPC validation: 122/122 passed; overlay classifier/report-gate validation: 22/22 passed; `npm run typecheck` passed. -->

## 4. Validation, integration, and rollout

- [x] 4.1 Run focused Edge and Cloud tests, acceptance suites, full tests, and typechecks; record exact results and any non-destructive validation boundary.
  <!-- Edge: focused overlay/report-gate 22/22; focused UI/IPC 122/122; acceptance 25/25 with real-machine E2E gated; full 1896/1896; typecheck passed. Cloud: focused risk/customer-auth 49/49; acceptance 59/59 with deployment E2E gated; full 2600 passed, 8 gated/skipped, 0 failed; typecheck passed. No real Facebook account was mutated and no actual restricted-account recovery was triggered. -->
- [ ] 4.2 Run `openspec validate facebook-environment-restriction-recovery --strict`, commit and push the isolated control/Edge/Cloud branches, then serially fast-forward them to current default branches without force.
- [ ] 4.3 Read the deployment runbook, pass `scripts/deploy-target dev --check`, deploy the integrated Cloud default branch to `dev`, and verify service/listener/health/customer-auth route behavior without mutating a real Facebook account.
- [ ] 4.4 Update this checklist with repository commit SHAs, validation/deployment evidence, deviations, and the explicit boundary that no Edge installer was built or published.
