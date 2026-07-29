## Why

`PgRiskCounterOutboxStore.applyClaimed()` currently uses `ON CONFLICT (outbox_id) DO NOTHING`, but PostgreSQL cannot infer the deployed partial unique index `WHERE outbox_id IS NOT NULL` from that conflict target. Every apply therefore fails before the outbox row can be marked applied, moving confirmed account activity toward dead letter while leaving the authoritative risk ledger under-counted.

## What Changes

- Make the risk-counter insert conflict target explicitly match the partial unique index predicate while preserving database-enforced exactly-once accounting.
- Add a PostgreSQL-gated integration test that creates the production index shape and proves first apply, duplicate apply, and outbox status behavior against a real PostgreSQL parser/planner.
- Retain bounded failure/dead-letter semantics and record an operational recovery sequence: target-scoped DEV audit, exact outbox-id before-images, deployment/canary, then explicit replay and reconciliation of only that immutable id set.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `interaction-risk-gating`: Clarify that exactly-once outbox apply must remain executable against the deployed partial unique index and must be verified by a real PostgreSQL contract test.

## Impact

- Cloud owner: `aidcp-cloud/src/risk/risk-counter-outbox-store.ts` and its PostgreSQL integration tests.
- Control owner: the `interaction-risk-gating` contract and this change's rollout/recovery tasks.
- No protocol, Edge, Console, schema shape, or public API change.
- DEV deployment and dead-letter replay are explicitly deferred until integration; no production data is mutated by this change implementation, and recovery MUST NOT restore shared DEV/OL tables wholesale.
