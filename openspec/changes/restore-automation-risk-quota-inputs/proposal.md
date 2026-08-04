## Why

On 2026-08-04 dev moved the edge WebSocket and all risk judgement from the monolith into the derived `aidcp-automation` process. That process builds its risk controller registry without two of the registry's current-read inputs: the safety-limit configuration provider and the account-nurture provider. Both parameters are optional and documented as "absent means a stated fallback", so the process starts, serves traffic, and reports nothing.

The result is that two configured behaviours silently stopped applying to every account driven from dev:

- **Slow start does not clamp anything.** A Facebook account whose environment carries today's slow-start anchor runs on the full tier ceiling. Measured on the client panel: browse 150 / like 50 / comment 8 / follow 15 / publish 1 / search 10 / join 3, against a day-1 curve of 20 / 2 / 0 / 1 / 0 / 1 / 0.
- **The console's safety-limit table is not read.** The same panel showed the compiled defaults, not the live `quota_config` rows an operator had edited (join_group daily 20 configured vs 3 enforced; browse per-hour 150 configured vs 38 enforced).

Because the same absent provider also feeds the slow-start projection, the browse loop's mode selection can never resolve to slow start either, so the slow-start cadence rules do not run. And the client shows two contradicting readings of one account: the operation-policy block (served by the interface process, which reads the environment anchor directly) says "slow start, day 1", while the quota block (served by the automation process) shows full-tier numbers — exactly the "displayed ≠ enforced" split the risk controller's own contract exists to prevent.

The two emergency levers for this feature (`AIDCP_SLOW_START_DISABLED`, `AIDCP_COLDSTART_RAMP`) are likewise never read by the judging process, so neither can be used to stop or restore the behaviour there.

## What Changes

- Build an account-nurture provider in the automation process from the sync-read mirrors it already maintains (account platform and creation time, environment slow-start anchor and graduation time, Facebook slow-start curve), and inject it into the risk controller registry.
- Inject the automation process's own safety-limit configuration store as the quota provider, constructing and initialising it before the risk foundation so no window exists in which judgement runs on compiled defaults while the store is available.
- Read both slow-start environment levers in the automation process and pass them through, so the global disable switch and the account-age ramp opt-in work where judgement happens.
- Make absence loud: when either current-read input is not injected, the risk foundation states at startup which capability is inert in this process and what the consequence is, instead of relying on a fallback documented only in source.
- Keep every existing judgement semantic unchanged: the clamp is still `min(curve, risk-scaled tier)`, an unknown platform still does not clamp, a stale slow-start mirror still resolves to the most conservative anchor, and the stop-work gate remains the mechanism that halts action on stale configuration.

## Capabilities

### Modified Capabilities

- `interaction-risk-gating`: any process that judges quotas must have both current-read inputs wired, must read the feature's own environment levers, and must say so loudly when an input is absent rather than falling back silently to compiled defaults.

## Impact

- Owning repo: `aidcp-automation` — process composition root, a new nurture-provider adapter over the existing sync-read mirrors, and the risk foundation's startup reporting.
- Control repo: OpenSpec delta and delivery evidence.
- No protocol, database, Console, or Edge change. No monolith change: `aidcp-cloud` already wires both inputs, and this change makes the derived process match it.
- Field caveat recorded, not fixed here: on dev the account-projection sync-read stream is currently rejecting every refresh (`same_cursor_payload_drift`), so account platform reads as unknown and the clamp still will not engage until that stream recovers. That staleness already halts platform actions through the existing stop-work gate, so it does not widen the quota hole; it does mean this change cannot be acceptance-tested on dev until that stream is healthy.
