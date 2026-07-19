## 1. Cloud persistence and create-only persona write

- [x] 1.1 Add persistent auto-fill run/target schema and store operations for customer-scoped Facebook environment snapshots, idempotency, binding reconciliation, state transitions, and restart recovery.
- [x] 1.2 Add atomic persona create-if-missing support through PersonaStore/facade, preserving validation and firing bound/changed callbacks only after a real insert.
- [x] 1.3 Cover the new store and create-if-missing semantics with focused unit tests, including ownership loss, existing persona, duplicate request, and manual-write race cases.
  <!-- aidcp-cloud commit 1286f8b: persistent run/target store, atomic create-if-missing, and focused regressions. -->

## 2. Cloud orchestration and customer API

- [x] 2.1 Implement the versioned `facebook_auto_v1` strategy and bounded orchestrator with stable account-based direction selection, selected writing language, account in-flight dedupe, and truthful terminal states.
- [x] 2.2 Add the authenticated `POST /persona-auto-fill/runs` route with strict body/header allowlists and no account/env selector acceptance.
- [x] 2.3 Wire immediate reconcile, startup recovery, and post-handshake environment-binding reconcile into server assembly without blocking Edge registration.
- [x] 2.4 Add focused orchestrator, customer-auth API, binding-trigger, restart, failure, and no-overwrite tests.
  <!-- aidcp-cloud commit 1286f8b: orchestrator, strict customer-auth route, startup/binding wiring, and tests. -->

## 3. Edge batch-creation surface and bridge

- [x] 3.1 Add the Facebook-batch-only default-on auto-fill control and one batch writing-language selector; hide and omit both for single/non-Facebook creation.
- [x] 3.2 Forward only the auto-fill intent/language through renderer IPC and, after at least one authoritative created environment, call customer-auth once with a bounded idempotent retry and no account IDs or credentials.
- [x] 3.3 Keep environment creation receipts separate from auto-fill acceptance/failure and add renderer/main-process regressions for enabled, disabled, partial, failure, and secret/ID non-disclosure paths.
  <!-- aidcp-edge commit 78cf2df: batch-only UI/bridge, separate receipts, and dedicated regressions. No installer built. -->

## 4. Validation, integration, and delivery

- [x] 4.1 Run focused Cloud/Edge tests, protocol and unauthorized-write acceptance where relevant, full tests, and typecheck in the owning worktrees.
  <!-- Cloud: focused customer-auth/persona/auto-fill tests + typecheck pass; full 2588 (2580 pass, 8 gated skips); acceptance 59/59. Edge: focused renderer/main auto-fill batch regressions + typecheck pass; acceptance 25/25; full suite exit 0 on rerun. One unrelated companion-ui timing assertion failed under the first concurrent full run, then passed focused and in the clean full rerun; no production change was made for the flaky test. -->
- [x] 4.2 Run `openspec validate facebook-cloud-auto-persona-fill --strict`, record repository commits/validation/deviations in this checklist, and commit/push feature branches.
  <!-- Feature commits after rebase: aidcp-cloud 1286f8b; aidcp-edge 78cf2df; aidcp OpenSpec artifact 57d1978. Strict OpenSpec validation passes. Feature branches pushed before default-branch integration. -->
- [x] 4.3 Rebase or fast-forward integrate clean default branches serially, rerun proportionate validation, and push `aidcp-cloud/master`, `aidcp-edge/master`, and `aidcp/main` without building an Edge installer.
  <!-- Defaults: aidcp-cloud/master 1286f8b; aidcp-edge/master 78cf2df; aidcp/main OpenSpec artifact b3b0a45 + validation record f24a34f, rebased onto concurrent origin/main 16534de before push. Canonical checkouts were clean; focused default-branch validation passed; no Edge installer was built. -->
- [x] 4.4 Run the dev deployment preflight, back up and deploy the committed Cloud source, restart only `aidcp-cloud.service`, verify service/listeners/health/PostgreSQL/customer-auth, and record the deployed SHA and honest runtime boundary.
  <!-- dev deployed aidcp-cloud/master 1286f8b on 2026-07-19. Preflight resolved 121.89.85.150 and aidcp-cloud.service. Backup stamp 20260719-184722 under /opt/aidcp/backups (cloud tar + env copy). Rsync dry-run and actual sync contained only the 12 intended Cloud source/test files; package manifests were unchanged, so npm ci was not run. Restarted only aidcp-cloud.service. Verified active service; listeners 8787/8090/8091; panel version; customer-auth /health locally and through :8088/capi; PostgreSQL select 1; persona_auto_fill_runs/targets present; startup log reports store ready; Feishu WS onReady and bot Dev.A; four isales services still active; four critical deployed file SHA-256 values match local master. No real Facebook account auto-fill was triggered during deployment because that would create paid/model-driven account state; the first operator batch remains the real-account acceptance boundary. -->

## 5. Edge manual Facebook-filter entry

- [x] 5.1 Add a compact writing-language selector and “补齐未设置人设” button visible only when the expanded environment rail is filtered to Facebook, with inline in-flight/success/failure feedback and no popup, navigation, counts, or local target selection.
- [x] 5.2 Add a dedicated renderer-to-main IPC that validates the language and customer session, generates a per-click idempotency key, and reuses the no-account-ID customer-auth request path without depending on batch-created items.
- [x] 5.3 Add focused helper, IPC, and renderer regressions for exact request body, Facebook-only visibility, empty local category submission, double-click prevention, honest inline receipts, and secret/ID non-disclosure.
  <!-- aidcp-edge feature commit aeb1020, rebased and integrated as master 3334fb5: Facebook-filter toolbar, customer-auth-only IPC, shared no-selector request helper, and 57 focused tests pass. -->
- [x] 5.4 Run focused Edge tests, acceptance/full tests and typecheck proportionately; run strict OpenSpec validation, commit/push and serially integrate `aidcp-edge/master` plus `aidcp/main` without building an Edge installer or redeploying unchanged Cloud code.
  <!-- Validation: focused 57/57, acceptance 25/25, full 1881/1881, typecheck pass, strict OpenSpec validation pass. aidcp-edge/master fast-forwarded to 3334fb5 after rebasing onto concurrent origin/master 65927e8, then focused 57/57 + typecheck passed on the default checkout and master was pushed. aidcp/main was rebased onto concurrent origin/main 169fbb1, fast-forward integrated, strictly validated, and pushed with this completion record. No real-account run, Edge installer, or Cloud deployment performed. -->
