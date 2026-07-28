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
- [ ] 3.4 Rebase each implementation worktree onto the latest default, rerun required validation, fast-forward integrate and push Cloud/Edge plus the control change without disturbing unrelated files.

## 4. DEV delivery boundary

- [ ] 4.1 Read the deployment runbook, run DEV target preflight, back up the affected Cloud/runtime state, deploy only from the clean Cloud default checkout and verify service, listeners, health, customer-auth and database evidence with rollback on failure.
- [ ] 4.2 Keep OL deployment, Edge packaging/signing/installer publication and real-account Facebook writes out of scope; report Cloud DEV runtime, Edge source and installed-client availability as separate facts.
