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

- [x] 5.1 Obtain explicit ol deployment authorization; before that, do not run the shared-database migration or a dev-only deployment.
  <!-- 2026-07-21: user explicitly requested dev deployment first, then an ol release branch and ol Cloud deployment, with no OL client package. -->
- [x] 5.2 Run dev/ol target preflights; record pre-migration task/status/attempt/event counts, active claims and each target's `AIDCP_DEPLOY_ENV` without exposing secrets.
  <!-- Preflight passed for dev 121.89.85.150 and ol 123.56.253.183. Both connected to PostgreSQL 172.17.201.88:5432/aidcp. Baseline: 124 tasks (awaiting_confirmation 1, cancelled 2, completed 18, deferred 4, failed 93, waiting_approval 6), 179 attempts, 11010 events at first snapshot, 0 active claims, 10 executable/polled tasks. dev target=dev; ol target was unset and must be set to ol after env backup. -->
- [x] 5.3 Back up both Cloud/env targets and delegated-task data; after observing zero active claims but 10 repeatedly polled executable tasks, stop the old ol Cloud immediately before the user-directed dev-first migration and audit claim/event deltas.
  <!-- Backup stamp 20260721-094029. dev: /opt/aidcp/backups/dev-cloud.20260721-094029.tgz, dev-cloud.env.20260721-094029, delegated-tasks.20260721-094029.dump; ol: /opt/aidcp/backups/ol-cloud.20260721-094029.tgz, ol-cloud.env.20260721-094029. SHA-256 and non-zero sizes verified. Old ol Cloud was stopped before dev restart; final pre-migration snapshot was 124 tasks, 179 attempts, 11039 max event id, 0 active claims, 10 polled tasks. -->
- [x] 5.4 Deploy dev from clean `master`, then create/push a release branch from the same Cloud SHA and deploy ol Cloud only; restart only the documented `aidcp-cloud.service` and do not build an OL client package.
  <!-- aidcp-cloud 17f1bf7 deployed dev-first from clean master; dev active at 2026-07-21 09:41:52 CST. Then release/20260721-delegated-task-target was created/pushed at the same SHA and deployed to ol; ol AIDCP_DEPLOY_ENV was backed up then set to ol, and ol became active at 09:43:56 CST. Only aidcp-cloud.service was stopped/started; no Edge/OL installer build or artifact upload ran. -->
- [x] 5.5 Verify service/listeners/health/PostgreSQL/Feishu on both targets, assert every legacy task is `dev` with unchanged business counts, and prove new tasks plus worker queries remain target-scoped.
  <!-- Both targets: service active, 8787/8090/8091 listening, local panel/client health OK, public /capi/health OK, matching server/migration SHA-256, and no post-start error-level journal entries. Startup logs show executionTarget=dev / ol. Final DB: 124 tasks (all dev; 0 invalid/ol), unchanged status distribution, 179 attempts, 0 active claims; ol startup produced 0 interrupted recovery events for dev tasks. Real PgDelegatedTaskStore createDraft smoke returned dev on dev and ol on ol inside transactions that were rolled back (no persisted smoke rows). dev Feishu WS is disabled by config; ol token/bot lookup passed as Red.A. -->
