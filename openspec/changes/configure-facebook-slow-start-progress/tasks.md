## 1. Cloud authority and projection

- [x] 1.1 Add a version-safe dedicated slow-start progress projection with bounded `day`, `totalDays`, and `completed` facts while preserving the existing operation-policy response shape, including active, graduated, off, unknown, bound, and unbound coverage.
- [x] 1.2 Implement the environment-owned slow-start progress CAS write that atomically adjusts the Shanghai-day anchor, target-local completion fact, policy revision, audit snapshot, and sync-read mirror without changing the base mode or cadence.
- [x] 1.3 Add the strict customer-auth progress route with ownership/platform/binding validation, revision-conflict current truth, write-after-read response, and focused API/store tests.
  <!-- aidcp-cloud worktree: dedicated GET/PUT customer route preserves the legacy operation-policy DTO; store writes anchor/completion/revision/audit/mirrors in one transaction. Focused client-auth + store run reached 107 tests with the one new fixture assertion corrected; final store rerun 24/24 and typecheck passed. -->

## 2. Edge client controls

- [x] 2.1 Add named preload/main IPC for exact `{ envKey, expectedRevision, day, completed }` progress requests through the fixed customer-auth environment route.
- [x] 2.2 Add compact current-day and completed controls immediately after the primary browse surface, render them only for confirmed active/graduated cold start, and preserve confirmed values during pending/error/cross-environment flows.
- [x] 2.3 Add focused renderer, UI-logic, IPC contract, and smoke tests for conditional visibility, dynamic day bounds, graduated selection, non-optimistic readback, and invalid response rejection.
  <!-- aidcp-edge worktree: named IPC plus exact response validation, dynamic day options, graduated-as-selected presentation, pending rollback and env-keyed caches. Typecheck passed; focused progress smoke 4/4 and operation-policy contract 6/6 passed after replacing cross-realm deep equality with serialized DTO equality. -->

## 3. Validation and delivery

- [x] 3.1 Run focused Cloud/Edge tests, both repository typechecks, `git diff --check`, and `openspec validate configure-facebook-slow-start-progress --strict`; record exact evidence and deviations in this task file.
  <!-- 2026-08-03 validation: Cloud `npm test` 4136 total / 4125 pass / 11 skipped / 0 fail, `npm run typecheck` passed, focused store rerun 24/24. Edge `npm run typecheck` passed, focused renderer smoke 4/4 and operation-policy contract 6/6. Edge full `npm test` reported 3044 pass / 1 skipped / 1 `write EPIPE` failure in runtime-contracts-session-recovery; the exact file then passed 3/3 in an immediate isolated serial rerun. `git diff --check` passed in control, Cloud, and Edge. `openspec validate configure-facebook-slow-start-progress --strict` passed. An offscreen source render confirmed the requested field order and existing control sizing; this is not packaged-client acceptance. -->
- [ ] 3.2 Commit and push the isolated Cloud/Edge branches, serially fast-forward them to the current default branches after rebase and validation, then deploy/verify Cloud on DEV through the standard target gate without packaging Edge or touching OL.
