## 1. Cloud implementation

- [x] 1.1 Update `PgRiskCounterOutboxStore.applyClaimed()` so the `outbox_id` conflict target explicitly infers the deployed partial unique index without changing transaction or lease semantics
- [x] 1.2 Add a real PostgreSQL integration test using the repository test-database guard and the production partial-index shape

## 2. Validation

- [x] 2.1 Run focused risk outbox unit tests and the new PostgreSQL contract test against a dedicated `aidcp_test*` database
  <!-- aidcp-cloud: focused risk tests 21/21; PostgreSQL 16 contract test 1/1 against ephemeral aidcp_test_risk_outbox. -->
- [x] 2.2 Run risk-related acceptance tests, the Cloud full test suite, and `npm run typecheck`
  <!-- aidcp-cloud: risk/protocol acceptance 27/27; full test exit 0; typecheck exit 0. Full PG aggregate additionally exposed 8 unrelated missing-migration failures on a blank temporary DB; this change's three PG cases passed. -->
- [x] 2.3 Run `openspec validate fix-risk-counter-outbox-conflict-target --strict`
  <!-- aidcp control: strict validation passed. -->

## 3. Integration handoff

- [x] 3.1 Commit the Cloud implementation and tests in the Cloud worktree
  <!-- aidcp-cloud commit 21c4bf3 (rebased onto origin/master e739c43); branch codex/fix-risk-counter-outbox-conflict-target; not pushed or deployed. -->
- [x] 3.2 Record Cloud commit, validation evidence, and deviations here, then commit the OpenSpec artifacts in the control worktree
  <!-- Validation after rebase: full Cloud test exit 0; typecheck exit 0; PostgreSQL 16 contract 1/1. Focused risk 21/21 and risk/protocol acceptance 27/27 passed before rebase; strict OpenSpec passed. Deviation: full PG aggregate on an unmigrated blank DB had 8 unrelated schema-missing failures while this change's 3 PG tests passed; deployment/replay remain tasks 4.1-4.4. -->

## 4. DEV deployment and recovery

- [ ] 4.1 After integration, run deployment preflight, back up the DEV Cloud application/env state and the affected PostgreSQL tables, then deploy the eligible integrated Cloud revision
- [ ] 4.2 Audit only `execution_target='dev'` dead letters matching the partial-index inference failure and incident window; exclude rows already represented by `risk_counters.outbox_id`
- [ ] 4.3 Reset only the audited DEV rows for normal-worker replay, then verify every replayed outbox id is applied and represented exactly once in `risk_counters`
- [ ] 4.4 Verify service/worker health, a newly enqueued canary fact, account/day reconciliation, and rollback readiness
