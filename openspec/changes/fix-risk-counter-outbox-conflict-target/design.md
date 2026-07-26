## Context

`risk_counters.outbox_id` is nullable because historical/direct counter rows do not originate from the durable outbox. Migration `0061` therefore enforces outbox idempotency with the partial unique index `UNIQUE (outbox_id) WHERE outbox_id IS NOT NULL`.

The apply statement names `(outbox_id)` as its conflict target without the index predicate. PostgreSQL requires a partial-index inference predicate in this form, so the statement raises `there is no unique or exclusion constraint matching the ON CONFLICT specification`. The transaction rolls back and repeated attempts eventually dead-letter confirmed activity.

Fake database tests cannot detect this parser/planner contract mismatch. The repository already has an explicit, production-refusing PostgreSQL integration channel (`npm run test:pg`) which is the correct place for the regression test.

## Goals / Non-Goals

**Goals:**

- Make the insert compatible with the existing partial unique index.
- Preserve transactionality, lease ownership checks, and database-enforced exactly-once counting.
- Prove the exact production schema/query pairing against real PostgreSQL.
- Define a safe, target-scoped recovery sequence for already dead-lettered DEV facts.

**Non-Goals:**

- Changing the `risk_counters` schema or making historical rows require `outbox_id`.
- Adding retries, alternate conflict strategies, or compatibility branches.
- Deploying Cloud, mutating DEV, or replaying dead letters in the implementation worktree.
- Repairing unrelated Edge activity projection or Native interaction execution.

## Decisions

### Match the existing partial index in the conflict target

Use:

```sql
ON CONFLICT (outbox_id) WHERE outbox_id IS NOT NULL DO NOTHING
```

PostgreSQL can then infer `uq_risk_counters_outbox`. This is preferred over removing the conflict target because an unconstrained `DO NOTHING` would suppress unrelated unique violations, and preferred over converting the index to a full unique constraint because nullable historical/direct rows are intentional and no schema change is needed.

### Keep the transaction and lease guard unchanged

The counter insert and outbox status update remain in one transaction. If the row is no longer owned by the claim token, the whole transaction rolls back. Duplicate apply is still harmless because the partial unique index suppresses only the duplicate non-null `outbox_id`.

### Test the production index shape with real PostgreSQL

Add a PG-gated integration test using `resolveIntegrationDatabase`, a dedicated `aidcp_test*` database, isolated test tables/schema shape, and `PgRiskCounterOutboxStore`. It SHALL prove:

1. the first claimed row inserts one counter and becomes `applied`;
2. a duplicate apply attempt does not insert a second counter;
3. the test would fail under the old predicate-less query because PostgreSQL itself resolves the conflict target.

Unit/fake tests remain useful for orchestration semantics but are not accepted as proof of index inference.

## Risks / Trade-offs

- [The PG test is skipped outside the explicit integration channel] → Keep the standard repository skip guard, run unit/typecheck in all environments, and require `npm run test:pg` with a dedicated test database before deployment.
- [Existing DEV dead letters may include unrelated failures] → Audit by target, failure signature, action, and time window; never bulk-reset all dead rows.
- [Replay after deployment could double-count rows already represented in `risk_counters`] → Back up first and exclude any dead row whose id already exists as a non-null `risk_counters.outbox_id`.

## Migration Plan

1. Validate source with focused unit tests, risk acceptance tests, typecheck, strict OpenSpec validation, and the real PostgreSQL contract test.
2. Integrate both clean worktree commits through the normal default-branch boundary.
3. Before DEV deployment, back up the Cloud application/env state and PostgreSQL tables involved in the scoped recovery.
4. Audit DEV `risk_counter_outbox` dead rows by `execution_target='dev'`, the partial-index inference error, and incident window; cross-check `risk_counters.outbox_id` to establish the exact replay set.
5. Deploy the eligible integrated Cloud revision to DEV and verify service/worker health plus a newly enqueued canary fact.
6. Reset only the audited replay set from `dead` to retryable state, preserving identifiers and dedupe keys; let the normal worker apply it.
7. Verify each replayed outbox id is `applied`, appears exactly once in `risk_counters`, and reconciles with account/day totals.
8. Roll back the code if new applies fail. Do not replay under the old code; if replay validation diverges, stop the worker and restore from the pre-replay backup.

## Open Questions

None for source implementation. The exact DEV replay set remains an operational audit result and MUST NOT be guessed in source tasks.
