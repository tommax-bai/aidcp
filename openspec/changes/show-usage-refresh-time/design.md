## Context

`ui.snapshot.dailyUsage.windows` already carries totals, quotas, saturation,
and timing metadata for session/minute/hour/day windows. Electron marks minute
and hour windows as `待刷新` when the local clock passes `expiresAt` without a
newer cloud snapshot. That is honest, but not actionable: operators cannot see
whether the next update is scheduled soon or whether a saturated window is
waiting for sliding-window quota release.

Cloud already has the pieces:

- `RiskController` owns per-account sliding-window counters and can compute
  retry timing for rejected quota checks.
- `UiSnapshotService` already pushes account-scoped daily usage via
  `ui.snapshot` to a specific online edge during hello.
- Edge already forwards unknown-compatible snapshot data through a structured
  `[ui-event] dailyUsage` path before Electron renders it.

## Goals / Non-Goals

**Goals:**

- Expose cloud-derived timing on each supplied daily usage window without
  changing the existing daily aliases.
- Show useful operator text in Electron: quota release time when a window is
  saturated, otherwise next cloud refresh time when known.
- Refresh online edge daily usage snapshots periodically enough that minute and
  hour windows do not sit indefinitely in `待刷新`.
- Preserve the existing red line: if cloud cannot compute timing, omit the
  fields and let the client fall back to the current honest stale state.

**Non-Goals:**

- No change to quota numbers, risk-state transitions, or interaction gating.
- No new edge-to-cloud request type for polling usage.
- No protocol breaking change; all new fields are optional.
- No attempt to predict platform-side risk overlays or captcha recovery.

## Decisions

1. Add optional `refreshAt` and `releaseAt` epoch-ms fields to
   `UiDailyUsageWindowStatus`.

   `refreshAt` means cloud plans or recommends refreshing this window snapshot
   at that time. `releaseAt` means at least one saturated quota in that window
   is expected to free a slot then, based on cloud's sliding-window counter.
   These stay separate so the UI does not present a snapshot refresh as quota
   availability.

   Alternative considered: overload `expiresAt`. Rejected because `expiresAt`
   currently means snapshot freshness, not runtime recovery or next push.

2. Compute `releaseAt` from `RiskController` rather than from aggregate totals.

   Aggregate totals cannot identify the oldest event that will leave a sliding
   window. `RiskController` already owns ordered counter events, so a small
   read-only helper can expose per-action/per-window retry timing without
   mutating risk state.

   Alternative considered: add timestamp queries to `PgRiskStore`. Rejected for
   this change because it duplicates counter logic and broadens the storage API.

3. Let `UiSnapshotService` schedule daily-usage-only refresh pushes for online
   edges after a hello snapshot.

   This keeps the flow cloud-initiated like existing UI snapshot behavior and
   avoids adding a new polling endpoint or WebSocket request. The scheduler is
   best-effort and stops naturally when a targeted push reaches no edge.

   Alternative considered: have Electron locally count down and refresh nothing.
   Rejected because it would answer "when" without ensuring the snapshot
   actually arrives.

4. Edge core and Electron main process sanitize and persist the new fields only
   when they are finite epoch numbers.

   This preserves the existing compatibility stance: absent or malformed timing
   is ignored, and the renderer never fabricates refresh/release values.

## Risks / Trade-offs

- [Risk] Periodic daily usage refresh adds database reads per online edge.
  → Mitigation: schedule only for targeted online edges, use the existing
  account-scoped snapshot builder, and stop when no edge receives the push.
- [Risk] Local clocks can drift from cloud time.
  → Mitigation: display epoch timestamps from cloud as hints, keep stale-state
  wording honest when a scheduled time passes without a fresh snapshot.
- [Risk] `releaseAt` may be absent for state-level blocks or non-quota reasons.
  → Mitigation: omit the field; Electron falls back to quota counts and refresh
  timing without claiming availability.
