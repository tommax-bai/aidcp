## Why

A DEV real-account run on 2026-07-28 (environment `ads-k1f44fo4`) joined a Facebook group successfully and then failed to comment on the group's first post, ending with the session stalled on an empty home feed for 60 seconds until cold standby restarted it. A control account on the same machine, same build, same minute completed the identical flow.

Four independent defects compose that outcome. Each of them is real on its own; none is the "reels vs feed surface" difference that the first reading suggested (a 45-sample cross-tab refutes that: reels-origin succeeded 3 times, feed-origin failed 5 times).

1. **The first-post scroll budget is spent in one round instead of four.** Change `facebook-first-post-comment-confirmation` (task 2.7) corrected the scroll displacement measurement to read the element that actually scrolls, because some group layouts never scroll the document itself. That correction landed in the list-probe path only. The first-post probe scrolls through a different branch that still moves and measures window coordinates, so on those layouts displacement is always zero and "already at bottom" is always true — the bounded scroll loop exits after the first round.

2. **The first-post identity and editor budgets are the tightest in the chain and are the observed failure boundary.** Across the last two days every first-post failure took 9.8–15.8 s and every success took ≤7 s, over five environments, three days and four distinct reasons. The discriminator is page hydration speed, not account, surface, or group. The identity readback window (8 s) is half of what the ordinary detail read path allows (15 s) for the same work, and the editor binding window (4 s) starts from "document interactive", which on these pages precedes content hydration.

3. **A command dropped by the task lease produces no receipt.** When a task release and a browse command race within the same millisecond, the edge logs a warning and returns; Cloud waits out its own step timeout with no signal. This is the "silently dropped" failure mode the project forbids, and it is already recorded as `facebook-first-post-comment-confirmation` task 5.6 (explicitly deferred there).

4. **An account whose ordinary home feed is empty can never return to the Reels surface once anything sends it home.** Authorizing the Reels fallback requires the fallback state to be idle; the only transition back to idle requires a non-empty ordinary feed to arrive. For an account whose home feed is empty — which is precisely why it was on Reels — that condition can never be met. The batch-tail browse scroll carries no task id, so the page session is rebuilt under the browse owner and the browse position resets to the default home feed, which trips exactly this trap. **This defect is independent of whether the comment succeeded**, and the dispatcher additionally has no handling branch for the resulting scroll/no-target receipt, so the session emits no further command and no terminal state.

## What Changes

- Measure and actuate the first-post probe scroll on the element that actually scrolls, so the bounded scroll budget is spent as specified rather than collapsing to one round on non-document-scrolling group layouts.
- Raise the first-post identity readback window to 20 s and the first-post comment editor binding window to 12 s, and raise the enclosing Native command ceiling and the Cloud first-post open step ceiling so the inner windows can actually be reached instead of being pre-empted by an outer deadline that reports less information.
- Keep the keyword-search open step at its current ceiling; only the empty-keyword first-post step is widened.
- Give a lease-suppressed command an honest receipt instead of dropping it silently.
- Break the Reels re-entry deadlock: an account that cannot produce a non-empty ordinary feed MUST still be able to be re-authorized onto the Reels surface.
- Give the dispatcher a handling branch for a scroll receipt that reports no target, so the session reaches a terminal state instead of emitting no further command.
- Recognize the observed Vietnamese `Đi đến Bảng feed` recovery control on an otherwise unusable Feed surface, locate it in JavaScript without DOM actuation, and let Native perform one trusted CDP pointer click. Browsing continues only after the same control disappears and the home surface is confirmed.
- Do not raise any group-join budget; the join path was measured with roughly half its readiness window unused and is explicitly out of scope.

## Capabilities

### New Capabilities

_None._

### Modified Capabilities

- `facebook-scheduled-comment`: bounded first-post scroll continuation is measured on the real scrolling element; first-post identity/editor budgets and their enclosing ceilings are stated as one coherent chain.
- `facebook-reels-browse`: Reels re-entry no longer requires a non-empty ordinary feed as its only unlock.
- `edge-task-execution-coordination`: a command suppressed by a task lease is reported, not dropped.
- `browse-loop-resilience`: a no-target scroll receipt reaches a terminal state instead of leaving the session with no pending command; the observed Vietnamese Feed-recovery control has a bounded trusted-click path.

## Impact

- Edge: Facebook page-router scroll branch and scroll metrics helper, Vietnamese Feed-recovery target probe, Native trusted CDP recovery click, Native first-post budgets, Native command ceiling selection, lease-suppression receipt path, and focused tests.
- Cloud: first-post open step ceiling, Reels fallback state transitions, dispatcher scroll-receipt handling, and focused tests.
- Control: OpenSpec deltas for the four capabilities above.
- Protocol: no new message type; no change to the action-name mapping tables.
- No database migration, no installer build, no OL deployment. Edge changes only reach the operator machine after a desktop package build, which is a separately triggered action.

## Constraint To Resolve Explicitly

`restore-facebook-join-handoff-resilience` states that established Edge/Native/Cloud timeout ceilings must not be raised. That requirement was written about the **group-join** legs, whose budgets this change leaves untouched. This change records that the constraint's scope is the join path, and widens only the first-post comment path. The join budgets stay exactly as they are.
