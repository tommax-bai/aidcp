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

- [x] 4.1 After integration and deployment preflight, perform a read-only DEV audit by target, exact failure signature, and bounded incident window; exclude represented counters and freeze the exact outbox-id replay manifest
  <!-- DEV audit: 697 exact dead rows from 2026-07-23 14:17:30.802+08 through 2026-07-26 10:41:23.735+08; view=681, search=6, like=10; represented counters=0. Immutable manifest SHA-256 2a7bca125b95a48acd683f0d2cde57fe13475b8ce8c295b4228c4eae82b59b01. -->
- [x] 4.2 Capture the manifest rows, manifest-linked counter rows, and affected account/day aggregates as exact before-images; back up DEV application/env state separately and record that shared risk tables MUST NOT be restored wholesale
  <!-- Exact before-images live under /opt/aidcp/recovery/risk-counter-outbox-dev-20260726-105209 (mode 0600); Cloud backup /opt/aidcp/cloud.bak.20260726-105451.tar.gz plus .env backup. criteria.txt records whole_table_restore=forbidden. -->
- [x] 4.3 Deploy the eligible integrated Cloud revision, verify the actual automation owner/worker health, and require one new canary outbox id to become exactly one applied counter before replay
  <!-- DEV source is deployed at default SHA ae8eb06 (includes risk fix ec77cc1); local/remote source hashes match. Three-process switch failed closed because api cannot construct panel without automation-owned composition dependencies, then automatically restored healthy monolith. Actual owner is aidcp-cloud.service with writer lock, outbox worker, reconciler, schema gates, Feishu, :8787/:8090/:8091 all healthy. Manifest id=1 served as a real-fact canary and reached applied with exactly one counter. -->
- [x] 4.4 Revalidate every manifest id and absence of counters, reset only that immutable id set without stopping OL, and verify each id becomes applied with exactly one counter
  <!-- DEV remained monolith, so stopping only the risk worker was impossible. A single transaction revalidated 697 ids, the one applied canary, the remaining 696 exact dead rows, target=dev, incident bounds, and zero represented counters, then reset only those 696 ids. Dead rows were unclaimable before commit; no broad lock or OL mutation occurred. Final: applied=697, pending=0, dead=0, exactly-one counters=697, duplicates=0. -->
- [x] 4.5 Reconcile affected account/day totals and record an exact-id inverse procedure; code rollback or replay divergence MUST NOT restore shared DEV/OL tables wholesale
  <!-- Reconciliation: 16 account/day/action groups, mismatches=0. Secure exact-id inverse SQL SHA-256 b25f63e1d4ef904225700c0ff8131d85658841021559a4709ee9da19d5ee215f; it is guarded to the 697 DEV ids and never restores whole tables. Post-replay service active, NRestarts=0, PostgreSQL/panel/ports/Feishu healthy, matching dead=0, recent risk errors=0. -->
