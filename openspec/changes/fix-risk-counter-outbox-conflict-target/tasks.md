## 1. Cloud implementation

- [x] 1.1 Update `PgRiskCounterOutboxStore.applyClaimed()` so the `outbox_id` conflict target explicitly infers the deployed partial unique index without changing transaction or lease semantics
- [x] 1.2 Add a real PostgreSQL integration test using the repository test-database guard and canonical migration/index DDL

## 2. Validation

- [x] 2.1 Run focused risk outbox unit tests and the new PostgreSQL contract test against a dedicated `aidcp_test*` database
  <!-- aidcp-cloud: focused risk tests 21/21; PostgreSQL 16 contract test 1/1 against canonical migrations in ephemeral aidcp_test_cloud. -->
- [x] 2.2 Run risk-related acceptance tests, the Cloud full test suite, and `npm run typecheck`
  <!-- aidcp-cloud: risk/protocol acceptance 27/27; full test exit 0; typecheck exit 0. Full PostgreSQL 16 aggregate 11/11 after applying all 78 canonical migrations to ephemeral aidcp_test_cloud; harness serializes destructive files and resets the topic cursor. -->
- [x] 2.3 Run `openspec validate fix-risk-counter-outbox-conflict-target --strict`
  <!-- aidcp control: strict validation passed. -->

## 3. Integration handoff

- [x] 3.1 Commit the Cloud implementation and tests in the Cloud worktree
  <!-- aidcp-cloud commits 21c4bf3 (runtime fix) + ec77cc1 (canonical PG contract and aggregate harness); branch codex/fix-risk-counter-outbox-conflict-target; not pushed or deployed. -->
- [x] 3.2 Record Cloud commit, validation evidence, and deviations here, then commit the OpenSpec artifacts in the control worktree
  <!-- Final validation: full Cloud test exit 0; typecheck exit 0; focused risk 21/21; risk/protocol acceptance 27/27; PostgreSQL 16 aggregate 11/11 after all 78 canonical migrations on ephemeral aidcp_test_cloud; strict OpenSpec passed. No source-validation deviation remains; deployment/replay remain tasks 4.1-4.5. -->

## 4. DEV deployment and recovery

- [ ] 4.1 After integration and deployment preflight, perform a read-only DEV audit by target, exact failure signature, and bounded incident window; exclude represented counters and freeze the exact outbox-id replay manifest
- [ ] 4.2 Capture the manifest rows, manifest-linked counter rows, and affected account/day aggregates as exact before-images; back up DEV application/env state separately and record that shared risk tables MUST NOT be restored wholesale
- [ ] 4.3 Deploy the eligible integrated Cloud revision, verify the actual automation owner/worker health, and require one new canary outbox id to become exactly one applied counter before replay
- [ ] 4.4 Pause only the DEV risk worker, revalidate every manifest id and absence of counters, reset only that immutable id set, resume DEV, and verify each id becomes applied with exactly one counter
- [ ] 4.5 Reconcile affected account/day totals and record an exact-id inverse procedure; code rollback or replay divergence MUST NOT restore shared DEV/OL tables wholesale
