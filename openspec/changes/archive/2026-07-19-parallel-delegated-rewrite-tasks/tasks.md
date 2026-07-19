# Tasks — parallel-delegated-rewrite-tasks

## 1. Contract and ownership model

- [x] 1.1 Add spec deltas for delegated rewrite lanes, waiting-approval ownership release, bounded worker concurrency, and admission atomicity.
- [x] 1.2 Add a pure task-ownership classifier/conflict function covering rewrite, autonomous publish, comment, and candidate-control lanes.
- [x] 1.3 Update PostgreSQL and memory stores to evaluate task-aware ownership without changing unrelated list/read behavior.
  <!-- aidcp-cloud 8aad267; task-aware query is additive and preserves hasActiveOwnership/list callers. -->

## 2. Bounded concurrent worker

- [x] 2.1 Replace whole-execution single-flight with a serialized admission gate plus bounded active executions.
- [x] 2.2 Release normal execution admission only after attempt dispatch and `executing` transition; release before long reconciliation awaits while keeping claims token-safe.
- [x] 2.3 Wire `AIDCP_DELEGATED_TASK_MAX_CONCURRENT` in `server.ts` with default 3 and startup-visible configuration.

## 3. Regression coverage

- [x] 3.1 Worker test: three different rewrite `sourceId` tasks can be executing concurrently and settle independently.
- [x] 3.2 Worker/store tests: same-source rewrite remains single-flight; waiting approval no longer blocks a rewash; autonomous publish/comment behavior remains single-flight.
- [x] 3.3 Run focused delegated-task and publish scheduler tests.
- [x] 3.4 Run `npm run test:acceptance`, full `npm test`, and `npm run typecheck`.
  <!-- Focused 35/35; acceptance 57/57; typecheck/build pass. After rebase, all 283 test files passed in 9 explicit Windows batches; npm test's quoted glob discovers 0 files on this host. -->

## 4. Integration and dev verification

- [x] 4.1 Rebase after any overlapping `show-queued-publish-tasks` store change, then integrate with `scripts/land-change aidcp-cloud parallel-delegated-rewrite-tasks --yes`.
  <!-- Rebasing included show-queued-publish-tasks cleanly; ff-only integration pushed aidcp-cloud master at 8aad267. -->
- [x] 4.2 Deploy dev from clean `aidcp-cloud/master`; verify service, 8787/8090/8088, health, PostgreSQL, and Feishu WS.
  <!-- Deployed dev 8aad267 after backup cloud-predeploy-20260719-110648-8aad267.tar.gz. Service active; ports and both health paths pass; PostgreSQL SELECT 1; Feishu WS ready and bot identity Dev.A; worker reports concurrency=3. -->
- [x] 4.3 Record commits, validation, deployment SHA, and deviations; run `openspec validate parallel-delegated-rewrite-tasks --strict` and archive when complete.
  <!-- Runtime proof: Engineer Dabai has two currently eligible rewrites and both are executing on distinct sourceId lanes. Deviation: rsync was unavailable on Windows, so a committed git archive was copied and extracted after backup; worker.ts SHA-256 matched before restart. -->
