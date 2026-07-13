## Context

The Electron renderer receives authoritative action totals, caps, saturated actions, and release timing through the existing account-scoped daily usage snapshot. The current renderer exposes those internal control concepts directly as "用量", "上限", "已满", and "释放", then styles saturation with the same red family used by engine failures. The data is correct, but the product meaning is wrong for a normal pacing completion.

The client must remain operationally honest: reaching a cap means a planned round or daily plan is complete, not that content performance has succeeded. Missing or stale quota evidence must not produce a completion message.

## Goals / Non-Goals

**Goals:**

- Translate authoritative pacing state into progress, completion, and next-step language.
- Separate completion, calm waiting, user assistance, and genuine failure visually.
- Preserve exact totals, caps, window timing, and stale-data behavior.
- Keep the change small enough to integrate into the current desktop layout.

**Non-Goals:**

- Changing quota calculation, risk control, session scheduling, or protocol fields.
- Adding the pending mascot assets or new onboarding flow.
- Claiming that a pacing completion guarantees reach, recommendations, or content quality.

## Decisions

### Translate control data only at the renderer boundary

Protocol and internal fields such as `quotas` and `saturated` remain unchanged. Renderer copy and CSS classes translate them to user-facing plan semantics. This avoids protocol churn and keeps developer diagnostics precise.

### Match completion language to the window

- Session caps become "本轮计划已完成".
- Minute and hour caps become "完成一轮" or "阶段计划已完成".
- Day caps become "今日计划已完成".

The collapsed summary favors the daily completion when the same action is complete in both rolling and day windows. Expanded details keep all supplied windows and exact numbers.

### Use a four-level visual taxonomy

- Progress: blue.
- Plan completion: green with a check mark.
- Calm waiting: teal/blue.
- User assistance: amber.
- Genuine execution failure or frozen account: red.

Red is not used for a reached pacing cap. Existing alert behavior remains, but assistance and failure receive separate presentation classes.

### Keep waiting copy short and layered

The presence strip uses a primary completion statement and a secondary next-step statement. The secondary line explains that the client is allowing the platform to learn from the current activity and includes the estimated continuation time when available. It does not claim that the whole session stopped when only one action is complete.

### Reuse the current layout

The existing summary card, disclosure control, progress bars, presence strip, health pill, and environment rail remain in place. No new component framework, icon dependency, or mascot slot is introduced.

## Risks / Trade-offs

- [Users may read "目标完成" as a performance guarantee] -> Always qualify the completed object as an action plan, round, or stage; never claim traffic or recommendation results.
- [A single saturated action may coexist with other running actions] -> Name the action that completed and avoid saying the entire client is resting.
- [Stale snapshots may show an old completion] -> Preserve the existing expiry checks and generic stale fallback.
- [Reduced red may hide real failures] -> Add a dedicated red error class for engine failure and frozen-account states; keep amber for recoverable assistance.

## Migration Plan

Ship as a renderer-only desktop update. Rollback is a direct revert of the HTML, JavaScript, CSS, and tests because no stored data or protocol changes are involved.

## Open Questions

None for this iteration. Mascot motion and first-content onboarding remain separate work.
