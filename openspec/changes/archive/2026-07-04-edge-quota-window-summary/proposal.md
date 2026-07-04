## Why

The Electron companion now shows authoritative account-scoped daily usage, but the quota model has more than a daily cap. Operators also need to see whether the current account is blocked by the current session budget, the minute burst cap, or the hour burst cap.

Without these windows, the UI can say the daily quota is fine while a minute/hour/session limiter is already saturated, which makes the companion look inconsistent with cloud decisions.

## What Changes

- Extend `ui.snapshot.dailyUsage` with optional per-window quota status for `session`, `minute`, `hour`, and `day`.
- Keep the existing `totals`, `quotas`, and `saturated` fields as daily aliases for older edge clients.
- Build minute/hour/day usage in cloud from account-scoped risk counters and publish history, and build session usage from the active dispatcher session budget when available.
- Render a compact quota-window strip in Electron: single-session, minute, hour, and today as peer status chips with visual saturation/near-limit states.
- Aggregate all supplied windows into the top quota-status chip so operators can see "quota normal" or "limit reached" without reading every metric.

## Impact

- Protocol: backward-compatible optional fields under `ui.snapshot.dailyUsage`.
- Cloud: additional read-only aggregation for risk windows, publish windows, and active session budget snapshots.
- Edge: structured UI event forwarding and Electron status normalization for windowed quota data.
- Electron UI: layout refinement in the existing daily summary card, preserving the current polished light-tech design language.
