## Context

`deriveWindowQuotasFromDaily()` is the single source that converts an action's daily quota into built-in minute and hour window values. It is used in two paths:

1. `deriveWindowQuotas(level)` supplies built-in fallback windows when `quota_config` has no valid override.
2. `RiskController.applyColdStartClamp()` converts the selected slow-start day's fixed daily caps into all three windows before taking an element-wise minimum with the risk-scaled account quota.

The minute formula currently divides by `20`; for Facebook slow-start day 1, `view=20/day` therefore becomes `1/minute`.

## Goals / Non-Goals

**Goals:**

- Change the shared minute derivation to `ceil(daily / 10)`.
- Preserve zero handling, the non-zero minimum of one, and `MINUTE_BURST_CAP`.
- Preserve explicit `quota_config.per_minute` overrides and the element-wise minimum between risk-scaled and slow-start quotas.
- Lock the resulting Facebook day-1 `view=2/minute` behavior with focused tests.

**Non-Goals:**

- Changing daily quotas, hour derivation, slow-start day curves, action cooldowns, pacing configuration, or risk-state transitions.
- Adding a new Console control, environment variable, database migration, compatibility branch, or rollout knob.
- Changing Edge/Cloud protocol payload shapes.

## Decisions

### Keep one shared derivation formula

Change only the minute divisor inside `deriveWindowQuotasFromDaily()`. This makes fallback default windows and slow-start windows obey the same arithmetic and avoids a slow-start-only duplicate formula.

Alternative considered: add a second slow-start-specific minute formula. Rejected because it would make two callers derive different minute windows from the same daily quota and create a future drift point.

### Preserve all existing clamps and precedence

The expression remains:

`daily <= 0 ? 0 : max(1, min(MINUTE_BURST_CAP[action], ceil(daily / 10)))`

`QuotaConfigStore` continues to prefer a valid persisted `per_minute` value over the derived fallback. Slow-start continues to take `min(riskScaled, derivedSlowStartCap)` per window and action, so the change cannot raise an account above its explicit/base risk quota.

### Test both the generic formula and the slow-start outcome

Focused tests will assert:

- `20/day` derives to `2/minute`.
- Zero remains zero and large values remain capped.
- Facebook slow-start day 1 exposes an effective `view` limit of `2/minute` when the base quota is looser.
- Day and hour values remain unchanged.

## Risks / Trade-offs

- [Uncovered `quota_config` cells receive higher built-in minute defaults] → Keep persisted valid overrides authoritative and test the fallback boundary explicitly.
- [Slow-start permits denser short bursts while retaining the same daily budget] → Preserve the existing minute burst cap, hourly cap, daily cap, cooldown backstop, and saturation observability.
- [Generic helper change accidentally alters hour/day behavior] → Add exact assertions for unchanged day/hour outputs and keep the patch confined to the minute divisor.

## Migration Plan

No schema or data migration is required. Deploying the Cloud code changes the in-memory derived values immediately; rollback restores the divisor to `20`. Existing `quota_config.per_minute` rows remain unchanged in both directions.

## Open Questions

None.
