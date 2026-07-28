## Why

Cloud currently derives Edge-origin risk-counter outbox dedupe keys primarily from the sequential envelope ID and action. Independent Edge processes restart that sequence, so different accounts or environments can emit the same envelope ID and cause a confirmed platform action to be mistaken for an existing outbox row. The platform action is then visible in activity history but absent from the account risk counter.

## What Changes

- Bind every Cloud dedupe key for an Edge-origin risk fact to the account ID, Edge environment ID, original envelope timestamp, original envelope ID, action, and any existing fact discriminator.
- Preserve exactly-once behavior for an actual replay of the same original envelope.
- Add focused Cloud coverage for replay, cross-account/environment isolation, and restarted envelope sequences.
- Keep the existing outbox schema, worker, protocol, and Edge envelope ID generation unchanged.
- Do not backfill or reinterpret historical risk-counter rows.

## Capabilities

### Modified Capabilities

- `interaction-risk-gating`: Define an unambiguous identity for Edge-origin outbox facts so unrelated accounts, environments, or envelope generations cannot collide.

## Impact

- Cloud communication handler and its risk-accounting tests.
- No database migration, public API change, protocol-v2 change, Edge change, Console change, or historical data rewrite.
