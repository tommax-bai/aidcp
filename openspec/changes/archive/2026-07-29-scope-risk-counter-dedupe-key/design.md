## Context

Edge envelopes use a process-local sequential ID. Cloud currently forms several Edge-origin risk-fact dedupe keys from that ID plus the action or a fact discriminator. Because the database uniqueness boundary is `execution_target + dedupe_key`, a sequence restart in another Edge process can collide with an older fact on the same deployment target even when the account, environment, or original send time differs.

The existing persistent outbox, transactional apply path, and database uniqueness constraint are correct. Only the identity supplied to that mechanism is incomplete.

## Goals / Non-Goals

**Goals:**

- Give every Edge-origin risk fact an identity scoped by account and environment.
- Distinguish reused sequential envelope IDs by their original envelope timestamp.
- Keep a true retransmission of the same original envelope idempotent.
- Apply one construction rule to every Edge-origin risk-fact enqueue site.

**Non-Goals:**

- Changing Edge envelope IDs or protocol v2.
- Changing the outbox schema or unique index.
- Backfilling historical outbox or counter data.
- Adding retries, compatibility modes, configuration, or a second dedupe mechanism.

## Decisions

### Centralize the key at the Cloud enqueue boundary

The Cloud communication handler will construct the dedupe key inside its shared Edge-origin risk-fact enqueue method. Call sites will provide the original envelope, action, and any existing discriminator rather than assembling partial keys themselves.

This prevents one receipt type from retaining the old incomplete identity. Keeping per-call-site strings was rejected because it makes future drift likely.

### Bind the original fact identity

The key will contain:

1. account ID from the authenticated Edge session;
2. Edge environment ID from that session;
3. the original envelope timestamp;
4. the original envelope ID;
5. the risk action;
6. the existing optional fact discriminator.

Each text field will be encoded before joining so field separators cannot create ambiguous identities. The original timestamp and ID are used unchanged; Cloud does not replace them with receipt time or a new UUID.

Account plus environment prevents unrelated sessions from sharing an identity. Timestamp plus ID preserves idempotency for a true replay while distinguishing a restarted process that reuses the same sequential ID later.

Generating a new Cloud UUID was rejected because it would make every retransmission distinct and break exactly-once behavior.

### Reuse the current persistence contract

The existing `execution_target + dedupe_key` uniqueness constraint remains the final exactly-once boundary. The target is still server-injected and is not duplicated as a substitute for account or environment identity.

No migration is required: newly received facts enter the new key namespace, while existing rows remain untouched.

## Risks / Trade-offs

- **Risk: A malformed session lacks an environment ID.** → Treat it as an enqueue failure through the existing fail-closed risk-accounting path instead of emitting an incompletely scoped key.
- **Risk: Old and new key formats can both exist for the same historical fact.** → Do not replay or backfill historical envelopes as part of this change; rollout applies only to newly received facts.
- **Trade-off: Keys become longer.** → The field is text and the added identity is bounded by existing session and envelope fields; correctness is more important than compactness.

## Migration Plan

1. Deploy the Cloud-only handler change and tests with no schema migration.
2. Restart the DEV Cloud service so new receipts use the scoped key.
3. Verify service health and inspect newly created outbox keys without initiating a real platform write solely for verification.
4. Roll back the Cloud commit if receipt handling or service health regresses; no data rollback is required.

## Open Questions

None.
