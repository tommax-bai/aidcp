## Context

Electron already receives account usage windows through `dailyUsage.windows` and renders session/minute/hour/day quota details. The presence strip is separate: once the latest activity event is older than five minutes, it currently falls back to "有一会儿没有新动态了" even if the latest quota snapshot shows a current saturated minute or hour window.

## Goals / Non-Goals

**Goals:**

- Prefer a quota-specific presence message when a running session has stale activity but current quota-window evidence explains the wait.
- Include the action label, window label, and estimated remaining wait when available.
- Keep stale-window honesty: expired rolling windows MUST NOT keep driving a quota-rest message.

**Non-Goals:**

- No new cloud event, database field, or protocol field.
- No change to quota enforcement, risk state, or session scheduling.
- No attempt to infer limits from local counters when cloud did not supply caps.

## Decisions

- Reuse normalized `dailyUsage.windows` in renderer logic. This keeps the change local to Electron and avoids adding another status channel for information the companion already has.
- Gate the message to running sessions after presence staleness. Fresh action text remains higher priority so the UI does not hide actual current work.
- Treat `releaseAt` as the preferred source for remaining wait because it represents quota release time. `expiresAt` remains only the stale-snapshot guard; if a rolling window is expired, the quota-rest message is suppressed and the existing stale-activity copy remains available.
- Select one explanatory window/action: the first current saturated action by window priority `session`, `minute`, `hour`, then `day`. Minute/hour are expected to produce the useful "预计 X 后继续" copy; day/session without expiry can still explain the reached limit without fabricating a resume time.

## Risks / Trade-offs

- [Risk] A stale cloud snapshot without timing metadata could over-explain a pause. → Mitigation: only include a remaining-time estimate when `releaseAt` is current; otherwise use a plain reached-limit message and keep existing stale fallback for missing caps.
- [Risk] Multiple windows can be saturated at once. → Mitigation: use deterministic window/action priority so tests and operator copy are stable.
