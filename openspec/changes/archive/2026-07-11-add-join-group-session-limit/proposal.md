## Why

The admin "安全 / 安全限额" page already exposes `join_group` as a daily risk action, but the "单场会话上限" table still has no join budget. Operators cannot cap how many group joins may happen inside one cloud-managed session, so join automation is only protected by minute/hour/day quotas.

This change closes that gap now that Facebook group join is a real scheduled action and the operator explicitly wants a per-session join limit.

## What Changes

- Add `join_groups` as the seventh global single-session interaction budget field, displayed in the admin session-limit table as "加群".
- Default `join_groups` to `1` when config is missing or older rows do not yet have the column.
- Gate real Facebook group-join dispatch on remaining single-session `join_groups` budget.
- Consume the single-session join budget only after a judgment-confirmed successful join; skipped, gated, pending, already-member, shadow, or failed attempts do not consume it.
- Preserve existing daily/minute/hour `join_group` risk quotas and risk-state single-writer behavior.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `interaction-risk-gating`: The global single-session interaction budget gains `join_groups`, and Facebook group join must honor it in addition to existing `join_group` risk quotas.

## Impact

- Cloud: session-limit config schema, defaults, panel API parsing, runtime session-budget accounting, Facebook group join scheduler gating, tests, and database migration/self-heal DDL.
- Console: quota page session-limit table, API types, save payload, and tests.
- Control repo: OpenSpec delta and implementation task tracking.
- No WebSocket protocol v2 change; no edge command or executor change.
