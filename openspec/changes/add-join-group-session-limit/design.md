## Context

`join_group` is already a first-class risk action with daily/minute/hour quota control and an admin "安全限额" action column. The separate "单场会话上限" config is a global singleton used by cloud runtime session budgets, but it currently contains only six interaction counters: likes, collects, follows, searches, comments, and comment_likes.

Facebook group join is scheduled by cloud and executed by edge as one atomic action. The cloud scheduler already gates on the `join_group` risk quota before dispatch and records risk success only after judgment-confirmed join. The missing piece is a per-session budget field that can stop additional join dispatches inside the same cloud-managed session.

## Goals / Non-Goals

**Goals:**

- Add `join_groups` to the global single-session budget with admin edit support.
- Keep older database rows safe by defaulting missing `join_groups` to `1`.
- Gate real group-join dispatch on the current runtime's remaining session join budget.
- Consume the session join budget only after a verified `joined` verdict.
- Keep the daily `join_group` risk quota and the single-writer risk-state model unchanged.

**Non-Goals:**

- No edge executor or `group.join` protocol change.
- No account-specific session-limit override.
- No change to comment coverage scheduling or group membership assignment semantics.
- No attempt to treat `already_member`, `pending`, `gated`, shadow, or failed attempts as session join consumption.

## Decisions

1. **Field name: `join_groups`.**

   The session budget fields use plural resource names (`likes`, `collects`, `follows`, `searches`, `comments`, `comment_likes`). `join_groups` keeps that shape while mapping clearly to the risk action `join_group`. The previous Facebook group-join design mentioned optional `joins`; this implementation chooses the more explicit field name for admin/API clarity.

2. **Default value: `1`.**

   The existing Facebook group-join design treated one join per scheduled slot as the conservative default. `1` preserves that behavior when the column is absent or an old row has no value, and it gives operators an explicit knob to raise or set to `0`.

3. **Runtime ownership: `RoleDispatcher` owns the budget, scheduler consumes through the runtime registry.**

   The existing per-session budget lives in `RoleDispatcher`. The join scheduler is not a dispatcher role, so it should not duplicate budget state. `ConnectionRuntimeRegistry` will expose a small session-budget adapter for `join_group`, allowing the scheduler to check and consume the active runtime budget without learning dispatcher internals.

4. **Consume only after verified success.**

   Session budget should represent successful joins, not navigation attempts. The scheduler will check remaining budget before dispatch, then call the runtime budget consumer only when the post-click verdict is `joined` and the edge result is successful. This matches existing risk-counter semantics and avoids punishing gated/failed probes.

5. **No WebSocket protocol change.**

   The admin page and cloud runtime need the new field, but edge does not. Keeping the change cloud+console-only avoids protocol drift and desktop package rollout.

## Risks / Trade-offs

- **[Race between budget check and consume]** → The content scheduler already enforces per-account single-flight for join/comment actions. The budget check and consume are still implemented defensively, but no additional distributed lock is introduced.
- **[No active runtime for an account]** → If no cloud runtime is registered for the account, the scheduler fails closed for the session-budget gate and skips dispatch. This avoids bypassing the new operator cap.
- **[Existing rows lack the column]** → Add both a migration and runtime self-heal `ALTER TABLE ... ADD COLUMN IF NOT EXISTS`, with code fallback to default `1` if a read returns a non-finite value.
- **[Operator sets join_groups to 0]** → This is valid and intentionally blocks real joins for the session while leaving daily quota config untouched.

## Migration Plan

- Add `budget_join_groups INTEGER NOT NULL DEFAULT 1` to the singleton session config table through a new migration and store self-heal DDL.
- Update cloud tests and console tests before deployment.
- Deploy cloud first so the API accepts and persists the new field, then deploy console so the new column can be edited.
- Rollback is safe: old console ignores the extra API field; old cloud would not read the new column but the database column is additive.

## Open Questions

- None for this change. The operator decision is to add the single-session join cap now.
