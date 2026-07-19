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
- [x] 3.4 Replace restricted-state euphemisms with explicit `账号受限` wording in health, detail, rail, and presence projections; ensure restricted overrides the generic completed-round/auto-resume fallback; and add focused UI logic/renderer/IPC contract tests.
  <!-- Edge focused UI/IPC validation: 122/122 passed; overlay classifier/report-gate validation: 22/22 passed; `npm run typecheck` passed. -->

## 4. Validation, integration, and rollout

- [x] 4.1 Run focused Edge and Cloud tests, acceptance suites, full tests, and typechecks; record exact results and any non-destructive validation boundary.
  <!-- Edge: focused overlay/report-gate 22/22; final combined UI/logic/IPC 172/172; acceptance 25/25 with real-machine E2E gated; final full 1897/1897; typecheck passed. Cloud: focused risk/customer-auth 49/49; acceptance 59/59 with deployment E2E gated; full 2600 passed, 8 gated/skipped, 0 failed; typecheck passed. No real Facebook account was mutated and no actual restricted-account recovery was triggered. -->
- [x] 4.2 Run `openspec validate facebook-environment-restriction-recovery --strict`, commit and push the isolated control/Edge/Cloud branches, then serially fast-forward them to current default branches without force.
  <!-- Strict validation passed before and after rebasing the control change onto current `origin/main`. Edge `47c03cfd4d339a4bc35145b84cfa78012e1849d3`, Cloud `69dfe1d8aee89f666a59bfeba03a46cc78c5564c`, and control artifact `55b82e1c73cc2fe8ff7f50dad9ea1cee658c022d` were pushed on the isolated branch. Edge/Cloud defaults were advanced by `--ff-only` and pushed without force; control main is advanced serially by the checklist closeout commit. -->
- [x] 4.3 Read the deployment runbook, pass `scripts/deploy-target dev --check`, deploy the integrated Cloud default branch to `dev`, and verify service/listener/health/customer-auth route behavior without mutating a real Facebook account.
  <!-- Deployed Cloud `69dfe1d8aee89f666a59bfeba03a46cc78c5564c` to dev from the clean canonical `master`. Backup: `/opt/aidcp/cloud.bak.20260719-210314.tar.gz`; env backup: `/opt/aidcp/cloud/.env.bak.20260719-210314`. Local/remote SHA-256 matched for the three changed source files. Post-restart: service active, NRestarts=0, listeners 8787/8090/8091 present, panel/client health returned `{ok:true}`, public `/capi/health` passed, both risk routes rejected missing auth with 401, PostgreSQL returned ok=1, Feishu WS reached onReady, and all four pre-existing isales services remained running. -->
- [x] 4.4 Update this checklist with repository commit SHAs, validation/deployment evidence, deviations, and the explicit boundary that no Edge installer was built or published.
  <!-- No behavior or validation deviations. No real Facebook account was mutated, no restricted-state recovery was triggered against a live account, and no Edge installer was built or published; the Edge change is source-only until a separately authorized desktop release. -->
