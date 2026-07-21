## Context

Electron already receives four authoritative window payloads under `dailyUsage.windows`: a session that starts with the active automation round, rolling minute and hour windows, and the Shanghai calendar day. The renderer currently maps those keys to “本轮计划 / 当前节奏 / 阶段节奏 / 今日计划”, renders each action as a slash fraction, derives one generic state vocabulary for all windows, and places four detailed groups in one row above 620 px.

The session is not a rolling “last N minutes” window. Its actual duration is configurable, and the existing payload already provides `startedAt`, `expiresAt`, and `windowMs`; therefore the client can explain the round without inventing or hard-coding a duration. Counts, caps, saturation, and release timing remain cloud-owned.

## Goals / Non-Goals

**Goals:**

- Make every expanded group reveal its real time scope in user language.
- Keep the short title “本轮计划” while using the existing status and metadata lines for remaining time and the actual range.
- Make a supplied cap read as “最多 N”, not as a target the user is expected to fill.
- Make browsing completion the visual milestone for a completed card, while letting other completed actions contribute only to a concise completion count.
- Give six action rows enough horizontal room through a 2×2 normal-width layout and a one-column narrow layout.
- Preserve stale-window, inactive-session, completion, and release fallbacks honestly.

**Non-Goals:**

- Changing cloud aggregation, quota configuration, risk gating, session duration, protocol fields, or supported-action projection.
- Turning the session into a rolling 30-minute window or hard-coding 30 minutes in the client.
- Changing the collapsed “今日进展” totals or lifecycle controls.

## Decisions

### 1. Use explicit time-scope labels, but keep the session identified as a round

The fixed labels become `本轮计划`, `近 1 分钟`, `近 1 小时`, and `今日计划`. Minute and hour are true rolling windows; session is deliberately not called `近 N 分钟`, because its count begins at `startedAt` and resets with the next round.

Alternative considered: `近 30 分钟` for session. Rejected because it is only numerically aligned at the end of a 30-minute round and becomes false after reset or while the round has run for less than 30 minutes.

### 2. Derive session timing only from supplied timestamps

When `session.active !== false`, `startedAt` and a future `expiresAt` are finite, the state line shows a remaining-time label and the metadata line shows `HH:MM 开始 · 预计 HH:MM 结束`. Remaining time uses minute precision normally and seconds near the end. Missing, inactive, or elapsed timing keeps existing safe states instead of synthesizing a countdown.

Alternative considered: show the configured duration in the title. Rejected because it makes the title too long and tells the user less than a live remaining-time status.

### 3. Separate confirmed count from the protective maximum

Each capped row renders the confirmed count as the primary value and `最多 N` as secondary text. An uncapped row renders only the count and no empty slash, maximum, or progress percentage. Existing completion/near styling remains derived from the same supplied cap and saturation fields.

Alternative considered: retain `N/N` and explain it in a tooltip. Rejected because the misleading target metaphor remains in the always-visible content.

### 4. Use 2×2 at the normal companion width

The expanded detail grid uses two equal columns at the normal companion width, ordered left-to-right and top-to-bottom as session, minute, hour, day. At the existing narrow breakpoint it becomes one column. The collapsed daily metric grid is unchanged.

Alternative considered: keep four columns. Rejected because status text, `最多 N`, and six progress rows become cramped in the companion's maximum-width shell.

### 5. Treat browsing completion as the card-level milestone

Every completed action contributes to the state text `完成 N 项`, and that text uses the completion color. The whole card and a completed row use the green completion surface only when the completed action is `浏览`. A completed like, favorite, comment, follow, or publish row stays in the normal visual style, so a supporting action cannot make the whole time window look finished.

The near-limit card tone is derived only from incomplete capped actions. This prevents a completed non-browsing action at 100% from turning the otherwise neutral card into a near-limit state.

Alternative considered: keep every completed action row green while limiting only the card background. Rejected because the user's primary signal is browsing progress; multiple green rows would still overstate completion and compete with the single `完成 N 项` summary.

## Risks / Trade-offs

- [Client clock differs from cloud] → Use client time only to format cloud-supplied timestamps and stop showing a countdown once `expiresAt <= now`; never infer a new end time locally.
- [Old snapshots omit timing] → Preserve the current state and metric fallback instead of fabricating a session range.
- [Long translated or large-number text wraps] → Allocate two columns, use secondary compact cap text, and retain the existing ellipsis/min-width protections.
- [A supporting action completion overstates the window result] → Keep the card and non-browsing rows neutral, and reserve the completion surface for browsing completion.
- [Copy-only change accidentally alters enforcement] → Keep protocol, cloud, counters, quotas, and saturation calculations untouched; cover the renderer transformation with focused DOM tests.
