## Why

The expanded “今日进展” card currently exposes cloud window keys as vague product labels such as “当前节奏” and “阶段节奏”, while slash values and “进行中” make protective pacing ceilings look like targets the user should complete. Users need to understand the real time range, what has happened, and when the current round will end without learning the system's quota model.

## What Changes

- Rename the expanded window groups to “本轮计划”, “近 1 分钟”, “近 1 小时”, and “今日计划”.
- For an active session with trustworthy timing metadata, show the current round's remaining time and exact start/end range; retain honest inactive or missing-time fallbacks.
- Present capped action rows as “已完成数量 + 最多 N” instead of a bare `N/N` fraction, while uncapped actions show only the confirmed count.
- Keep the expanded groups in a readable 2×2 layout at the normal companion width and fall back to one column at narrow widths.
- Preserve all cloud counts, caps, saturation decisions, action projection, collapsed daily totals, and risk behavior unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-companion-ui`: Make expanded plan-window labels, timing, cap wording, and layout describe the user-visible time scopes and consequences directly.

## Impact

- `aidcp-edge`: Electron renderer copy, formatting helpers, expanded-window layout, and focused UI tests.
- `aidcp`: OpenSpec delta and validation record.
- No protocol, cloud, database, configuration, or deployment-contract changes.
