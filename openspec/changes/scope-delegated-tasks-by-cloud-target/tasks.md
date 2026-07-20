## 1. Runtime target boundary

- [x] 1.1 Add the `dev | ol` delegated execution-target type and strict `AIDCP_DEPLOY_ENV` parser with focused tests.
- [x] 1.2 Make Cloud delegation service/worker assembly fail closed when the deployment target is missing or invalid, without changing unrelated Cloud startup boundaries.

## 2. Persistence and migration

- [x] 2.1 Add `delegated_tasks.execution_target`, map it into `DelegatedTask`, and make store-created tasks receive the store's trusted target rather than caller input.
- [x] 2.2 Add idempotent startup schema and `0052` migration SQL that backfills every legacy task to `dev`, enforces `NOT NULL`/`dev|ol`, and preserves task/attempt/event data.
- [x] 2.3 Partition active dedupe and queue/ownership indexes by execution target so identical dev/ol requests do not conflict.

## 3. Target-scoped lifecycle

- [x] 3.1 Scope task create dedupe, get/list, curated creation-state projections, confirmation, pause/resume/cancel and terminal writes to the current execution target.
- [x] 3.2 Scope worker claim, interrupted-claim recovery, ownership checks and expiry inputs to the current execution target.
- [x] 3.3 Add focused PostgreSQL/store/worker/service tests proving ol cannot observe, recover, claim or control dev tasks and dev/ol dedupe remains independent.

## 4. Validation and delivery

- [x] 4.1 Run focused delegated-task tests, required acceptance/full Cloud tests, and `npm run typecheck`; record any bounded reruns or flakes honestly.
  <!-- aidcp-cloud: delegated 88/88; delegated + curated-store focused 123/123; acceptance 64/64; full 2730 passed + 8 gated skips; typecheck passed. The only rerun was a test-regex whitespace mismatch after adding migration consistency coverage; production SQL was unchanged and the corrected assertion passed. -->
- [x] 4.2 Run `openspec validate scope-delegated-tasks-by-cloud-target --strict` and record Cloud/control commits plus validation evidence in this checklist.
  <!-- OpenSpec strict validation passed. aidcp-cloud implementation commit: 17f1bf7. aidcp control artifact commit: 211ab75. -->
- [x] 4.3 Rebase onto current defaults, fast-forward integrate and push Cloud `master` plus control `main` without disturbing unrelated work.
  <!-- 2026-07-21: both feature branches were based on the current fetched origin defaults (0 behind), fast-forwarded into aidcp-cloud master / aidcp main, and pushed. Canonical control output/ and tmp/ remained untouched. -->

## 5. Coordinated migration and runtime proof

- [ ] 5.1 Obtain explicit ol deployment authorization; before that, do not run the shared-database migration or a dev-only deployment.
- [ ] 5.2 Run dev/ol target preflights; record pre-migration task/status/attempt/event counts, active claims and each target's `AIDCP_DEPLOY_ENV` without exposing secrets.
- [ ] 5.3 Back up both Cloud/env targets and delegated-task data, then coordinate stopping both old Cloud workers before applying the shared schema migration.
- [ ] 5.4 Deploy ol and dev from clean eligible branches, restarting only the documented `aidcp-cloud.service` on each target.
- [ ] 5.5 Verify service/listeners/health/PostgreSQL/Feishu on both targets, assert every legacy task is `dev` with unchanged business counts, and prove new tasks plus worker queries remain target-scoped.
