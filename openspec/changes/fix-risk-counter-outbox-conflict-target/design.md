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

Add a PG-gated integration test using `resolveIntegrationDatabase`, a dedicated `aidcp_test*` database, the canonical `0002` + `0061` migration DDL in an isolated schema, and `PgRiskCounterOutboxStore`. It SHALL prove:

1. PostgreSQL reports the deployed partial-index predicate as `outbox_id IS NOT NULL`;
2. the first claimed row inserts one counter and becomes `applied`;
3. a duplicate apply attempt does not insert a second counter;
4. the test would fail under the old predicate-less query because PostgreSQL itself resolves the conflict target.

Unit/fake tests remain useful for orchestration semantics but are not accepted as proof of index inference.

The full PG channel SHALL run on a migration-complete temporary database. Its integration files share destructive fixtures, so the channel SHALL serialize test files and reset both legacy and topic-scoped event-outbox cursors. A focused contract pass cannot replace a red aggregate.

## Risks / Trade-offs

- [The PG test is skipped outside the explicit integration channel] → Keep the standard repository skip guard, run unit/typecheck in all environments, and require a green full `npm run test:pg` on a migration-complete dedicated database before deployment.
- [Existing DEV dead letters may include unrelated failures] → Audit by target, failure signature, action, and time window; never bulk-reset all dead rows.
- [Replay after deployment could double-count rows already represented in `risk_counters`] → Freeze an immutable exact-id manifest with before-images first and exclude any dead row whose id already exists as a non-null `risk_counters.outbox_id`.
- [DEV and OL share PostgreSQL] → Every audit, reset, verification, and inverse operation MUST join the exact manifest back to `risk_counter_outbox.execution_target='dev'`. `risk_counters` has no target column, so it MUST be scoped only through those manifest outbox ids. Whole-table restore is forbidden.

## Migration Plan

1. Validate source with focused unit tests, risk acceptance tests, typecheck, strict OpenSpec validation, and a green full PostgreSQL aggregate on a migration-complete `aidcp_test*` database.
2. Integrate both clean worktree commits through the normal default-branch boundary.
3. Before any DEV mutation, audit `risk_counter_outbox` read-only by `execution_target='dev'`, the exact partial-index inference error, and the bounded incident window. Exclude every row already represented by `risk_counters.outbox_id`; freeze the resulting outbox ids as an immutable replay manifest.
4. Capture before-images for only the manifest outbox rows, any `risk_counters` rows whose `outbox_id` is in that manifest, and the affected account/day aggregates. Back up the DEV Cloud application/env state separately. Do not take or plan a whole-table restore of shared risk tables.
5. Deploy the eligible integrated Cloud revision to DEV, then verify the actual automation owner process, worker health, and one newly enqueued canary fact. Roll back code and stop before replay if the canary does not become exactly one applied counter.
6. If the DEV risk-counter worker is independently supervised, pause only that worker. If DEV is still running the monolith, do not stop the whole DEV service and do not take a shared-table lock that would stall OL: instead perform the complete manifest revalidation and exact-id reset in one transaction. Dead rows are not claimable, so the worker cannot race the validation before commit; they become claimable only after the guarded update commits. In either topology, revalidate that every manifest id still belongs to `execution_target='dev'`, is still the audited dead row, and has no counter; abort on any drift. Reset only those ids to retryable state and never stop or mutate OL.
7. Verify every manifest id becomes `applied`, appears exactly once in `risk_counters`, and reconciles with the frozen account/day before-images plus the manifest action counts.
8. Code rollback does not broadly restore database tables or erase already verified facts. If replay validation diverges, pause only the DEV worker and apply an inverse operation only to manifest ids using their before-images. If that exact inverse cannot be proved safe, leave the worker paused and stop for operator review; whole-table restore is forbidden.

## Open Questions

None for source implementation. The exact DEV replay set remains an operational audit result and MUST NOT be guessed in source tasks.
