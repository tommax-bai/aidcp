## 1. Cloud persistence and create-only persona write

- [x] 1.1 Add persistent auto-fill run/target schema and store operations for customer-scoped Facebook environment snapshots, idempotency, binding reconciliation, state transitions, and restart recovery.
- [x] 1.2 Add atomic persona create-if-missing support through PersonaStore/facade, preserving validation and firing bound/changed callbacks only after a real insert.
- [x] 1.3 Cover the new store and create-if-missing semantics with focused unit tests, including ownership loss, existing persona, duplicate request, and manual-write race cases.
  <!-- aidcp-cloud commit df50563: persistent run/target store, atomic create-if-missing, and focused regressions. -->

## 2. Cloud orchestration and customer API

- [x] 2.1 Implement the versioned `facebook_auto_v1` strategy and bounded orchestrator with stable account-based direction selection, selected writing language, account in-flight dedupe, and truthful terminal states.
- [x] 2.2 Add the authenticated `POST /persona-auto-fill/runs` route with strict body/header allowlists and no account/env selector acceptance.
- [x] 2.3 Wire immediate reconcile, startup recovery, and post-handshake environment-binding reconcile into server assembly without blocking Edge registration.
- [x] 2.4 Add focused orchestrator, customer-auth API, binding-trigger, restart, failure, and no-overwrite tests.
  <!-- aidcp-cloud commit df50563: orchestrator, strict customer-auth route, startup/binding wiring, and tests. -->

## 3. Edge batch-creation surface and bridge

- [x] 3.1 Add the Facebook-batch-only default-on auto-fill control and one batch writing-language selector; hide and omit both for single/non-Facebook creation.
- [x] 3.2 Forward only the auto-fill intent/language through renderer IPC and, after at least one authoritative created environment, call customer-auth once with a bounded idempotent retry and no account IDs or credentials.
- [x] 3.3 Keep environment creation receipts separate from auto-fill acceptance/failure and add renderer/main-process regressions for enabled, disabled, partial, failure, and secret/ID non-disclosure paths.
  <!-- aidcp-edge commit 4f8d92b: batch-only UI/bridge, separate receipts, and dedicated regressions. No installer built. -->

## 4. Validation, integration, and delivery

- [x] 4.1 Run focused Cloud/Edge tests, protocol and unauthorized-write acceptance where relevant, full tests, and typecheck in the owning worktrees.
  <!-- Cloud: focused customer-auth/persona/auto-fill tests + typecheck pass; full 2588 (2580 pass, 8 gated skips); acceptance 59/59. Edge: focused renderer/main auto-fill batch regressions + typecheck pass; acceptance 25/25; full suite exit 0 on rerun. One unrelated companion-ui timing assertion failed under the first concurrent full run, then passed focused and in the clean full rerun; no production change was made for the flaky test. -->
- [ ] 4.2 Run `openspec validate facebook-cloud-auto-persona-fill --strict`, record repository commits/validation/deviations in this checklist, and commit/push feature branches.
- [ ] 4.3 Rebase or fast-forward integrate clean default branches serially, rerun proportionate validation, and push `aidcp-cloud/master`, `aidcp-edge/master`, and `aidcp/main` without building an Edge installer.
- [ ] 4.4 Run the dev deployment preflight, back up and deploy the committed Cloud source, restart only `aidcp-cloud.service`, verify service/listeners/health/PostgreSQL/customer-auth, and record the deployed SHA and honest runtime boundary.
