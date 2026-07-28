## 1. Cloud customer-auth contract

- [x] 1.1 Add a narrow customer-facing Facebook rule-mode projection and a `ClientAuthDeps` port that reuses the existing account-level store without exposing account identifiers or internal actors.
- [x] 1.2 Add environment-scoped GET and PUT routes that validate ownership, unique binding, Facebook platform and an exact `{ enabled: boolean }` body before authoritative read/write.
- [x] 1.3 Wire the existing `FacebookRuleModeStore` into the customer-auth composition root with client-scoped actor attribution and no Edge-online dependency.
- [x] 1.4 Add focused server tests for auth, ownership, stopped environments, binding unknown/conflict/unavailable, non-Facebook rejection, strict body validation, write failure and successful write-after-readback.
<!-- 1.1-1.4: aidcp-cloud worktree implementation. Focused client-auth suite 71/71 PASS; typecheck PASS. Commit/integration/deploy evidence will be recorded in section 3/4. -->

## 2. Edge customer client

- [x] 2.1 Add named main/preload IPC methods that accept only `envKey` or `envKey + enabled` and call the fixed customer-auth rule-mode routes.
- [x] 2.2 Add a static Facebook-only rule-mode row adjacent to the slow-start row with copy that distinguishes enabled configuration from effective execution and states slow-start precedence.
- [x] 2.3 Implement per-environment authoritative reads, pending writes, complete-receipt convergence, errors, unknown state and stale-response isolation without local persistence or local rule execution.
- [x] 2.4 Add focused Electron contract and renderer tests for adjacency, platform visibility, stopped-environment reads, non-optimistic write success/failure, incomplete responses and environment switching.
<!-- 2.1-2.4: aidcp-edge worktree implementation. IPC contract 3/3 PASS, renderer smoke 92/92 PASS, typecheck PASS. No WebSocket protocol or local execution authority changed. -->

## 3. Validation and integration

- [x] 3.1 Run focused Cloud client-auth/rule-mode tests, then Cloud acceptance, full tests and typecheck with bounded output.
- [x] 3.2 Run focused Edge IPC/renderer tests, relevant customer-auth safety tests, full tests and typecheck with bounded output.
<!-- 3.1: aidcp-cloud 0622af9. Focused client-auth 71/71 PASS; acceptance 27 files PASS; full 449 files PASS; typecheck PASS. -->
<!-- 3.2: aidcp-edge 8d377a6. IPC contract 3/3 PASS; renderer smoke 92/92 PASS; acceptance 3 files PASS; full 197 files PASS; typecheck PASS. -->
- [x] 3.3 Record owning repositories, commit SHAs, exact validation and delivery boundaries in this checklist, then run `openspec validate client-facebook-rule-mode-toggle --strict`.
<!-- 3.3: Cloud owner commit 0622af95228efda94fcb25540678037cdaad3942; Edge owner commit 8d377a6bebd7af03e2a2f0cfc5b6c3578428f29f. Validation is recorded in 3.1/3.2. Boundary at this checkpoint: source commits only; no DEV deploy, Edge package, OL deploy, or real-account action yet. OpenSpec strict validation PASS. -->
- [x] 3.4 Rebase each implementation worktree onto the latest default, rerun required validation, fast-forward integrate and push Cloud/Edge plus the control change without disturbing unrelated files.
<!-- 3.4: Cloud/Edge worktrees were current with origin/master, post-rebase focused suites + typechecks PASS, and fast-forward pushes integrated Cloud master 0622af9 and Edge master 8d377a6. Canonical sibling checkouts were fast-forwarded; unrelated Edge dist-electron backup and repro scratch files, plus control PDF artifacts, were preserved. Control main 9fcda37 was pushed with the validated artifacts; later delivery evidence is appended in follow-up control commits. -->

## 4. DEV delivery boundary

- [x] 4.1 Read the deployment runbook, run DEV target preflight, back up the affected Cloud/runtime state, deploy only from the clean Cloud default checkout and verify service, listeners, health, customer-auth and database evidence with rollback on failure.
- [x] 4.2 Keep OL deployment, Edge packaging/signing/installer publication and real-account Facebook writes out of scope; report Cloud DEV runtime, Edge source and installed-client availability as separate facts.
<!-- 4.1: DEV target 121.89.85.150 preflight PASS. Clean Cloud master 0622af9 deployed only src/client-auth/client-auth-server.ts and src/server.ts after backups /opt/aidcp/backups/cloud.bak.20260728-124651.tar.gz and /opt/aidcp/cloud/.env.bak.20260728-124651. Local/remote SHA-256 matched 5ab7eb3 and 8f1c4af. Migration status remained content 20/20, automation 51/51 and api 59/59 with zero pending. Stop→start touched only aidcp-cloud.service; active, NRestarts=0, listeners 8787/8090/8091/8088/5432, panel/client/public health, three owner DB SELECT 1 probes, all enforce schema gates, target=dev writer lock and Feishu WSClient onReady passed. New route source was present; unauthenticated GET/PUT probes returned 401 and performed no write. Startup critical error count was zero; all four isales services remained active. No rollback was required. -->
<!-- 4.2: OL was untouched. Edge master contains source commit 8d377a6, but no dist, package, signature, notarization, installer or installed-client update was produced. No customer credential was used and no real Facebook read/write was triggered; the visible switch requires a future explicitly authorized Edge package/release before installed clients receive it. -->
