## 1. Cloud account schedule persistence and API

- [x] 1.1 Extend `account_content_schedule` with nullable `active_week_mask`, update the documented migration, cache/DTO types, reload and atomic UPSERT paths without backfilling existing accounts.
- [x] 1.2 Add the single account effective active/content resolver with independent inheritance, source/effective catalog fields, dirty-active fallback to global, and unchanged automation switch defaults.
- [x] 1.3 Extend the Panel account schedule request parsing and response contract for `activeWeekMask` plus `contentActiveMask`, including atomic validation, clear-to-inherit and honest readback.
- [x] 1.4 Add focused store and Panel tests for account priority, independent inheritance, clear-to-global, invalid atomic rejection, unknown/retired accounts and unchanged action fields.
  <!-- aidcp-cloud commit 02e052d; focused store/runtime/Panel validation 71/71 passed. -->

## 2. Cloud runtime account-aware activity gates

- [x] 2.1 Add an account active-mask provider to `RoleDispatcher` and route restart, resume verdict, wake calculation, running-session monitoring and standby snapshots through one helper with global fallback compatibility.
- [x] 2.2 Make `ContentScheduler.browseActiveAt` account-aware and wire production to the same account effective resolver so automatic content remains inside that account's active window.
- [x] 2.3 Add focused runtime tests proving two accounts can receive different start/resume/wake/content decisions and that clearing an override immediately returns to global behavior.

## 3. Console account schedule management

- [x] 3.1 Extend Console DTOs and catalog query handling with raw account masks, effective masks and independent source flags.
- [x] 3.2 Add the schedule column and account three-state calendar modal with “add schedule”, “edit”, atomic save and confirmed “restore global” actions while preserving the global editor.
- [x] 3.3 Add interaction tests for global initialization, account-only edits, restore-to-global, server-error truthfulness and unchanged automation switches.
  <!-- aidcp-console commit 02c3b54; focused page validation 12/12 passed. -->

## 4. Validation, integration and dev delivery

- [x] 4.1 Run Cloud focused tests, acceptance, full tests and typecheck; run Console focused tests, full tests and build.
  <!-- Validation: Cloud focused 71/71, acceptance 65/65, post-rebase full 2796 passed + 8 skipped, typecheck passed. Console focused 12/12, full 230 passed + 1 skipped, typecheck/build passed. -->
- [x] 4.2 Run `openspec validate account-activity-content-schedule --strict` and record validation evidence and implementation commit SHAs in this task file.
  <!-- OpenSpec strict validation passed before and after implementation; control deb51f0; Cloud 02e052d; Console 02c3b54. -->
- [ ] 4.3 Rebase and fast-forward land the control, Cloud and Console branches onto their default branches, then push without force.
- [ ] 4.4 Deploy the clean default Cloud and Console revisions to `dev` only after target preflight/backups, then verify schema/hash, service/listener/health and bounded logs; record truthful deployment evidence.
