## Context

`RiskController.explain()` currently evaluates `minute`, `hour`, and `day` through the same sliding-window counter. The companion UI, panel usage, and operator language treat daily usage as the Asia/Shanghai calendar day. This mismatch caused a real case where the UI showed `view=76/150` for today while the cloud blocked new views because the last 24 hours had reached `150/150`.

The change belongs in `aidcp-cloud`: edge should continue executing commands honestly and should not reinterpret quota windows locally.

## Goals / Non-Goals

**Goals:**
- Keep short burst protection as sliding `minute` and `hour` windows.
- Make the `day` quota window an Asia/Shanghai local calendar day for gating, retry timing, UI usage, and docs.
- Preserve existing persisted `risk_counters` events and quota numbers.

**Non-Goals:**
- No protocol payload shape changes.
- No database schema changes.
- No change to risk-state transitions or quota-level scaling semantics.
- No manual clearing or rewriting of existing counters.

## Decisions

1. Add calendar-day semantics inside the risk counter layer instead of special-casing only UI.
   - Rationale: `RiskController.explain()`, `quotaReleaseAfterMs()`, and UI `releaseAt` should use the same source of truth.
   - Alternative rejected: changing the UI to show 24-hour totals would keep operator-facing "daily" quotas unintuitive.

2. Use Asia/Shanghai as the day boundary.
   - Rationale: the service runtime and operator workflows are China-local, and explicit Asia/Shanghai arithmetic avoids host or DB session timezone drift.
   - Alternative rejected: UTC calendar days would still disagree with the operator's local day.

3. Keep `risk_counters` as append-only event storage.
   - Rationale: the storage already has enough timestamp data to compute both burst windows and calendar-day windows. A schema migration would add risk without value.

4. Make persisted "today" aggregations use the same explicit day boundary.
   - Rationale: companion `dailyUsage`, panel summaries, and content/publish daily caps must not disagree with `RiskController` when the DB session timezone differs from Asia/Shanghai.

## Risks / Trade-offs

- [Risk] Local tests running outside Asia/Shanghai could produce boundary drift if the implementation depends on the host timezone. → Mitigation: compute day boundaries explicitly for `Asia/Shanghai`.
- [Risk] Existing docs still mention "day sliding window". → Mitigation: update protocol/risk-control docs and OpenSpec requirement wording in the same change.
- [Risk] Switching day semantics can immediately unblock accounts that hit the old 24-hour window but not today's quota. → Mitigation: this is intended behavior; minute/hour burst windows remain in place.
