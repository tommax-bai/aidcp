## Why

Facebook group and comment tasks temporarily take the page away from the configured browsing surface. Releasing the Edge write lease currently only unblocks browsing; Cloud does not immediately issue a continuation command, so the next movement can wait for the four-minute idle watchdog. For Reels sessions, the long-lived `reelsFallbackState='confirmed'` can also describe an earlier page rather than the page that is currently open, preventing an immediate return to Reels.

## What Changes

- Reuse one existing `page.scroll` command with `reason='resume_redrive'` for every active browse continuation, and include the configured target surface in that command instead of selecting different redrive reasons in Cloud.
- Make Edge reconcile the currently observed Facebook page with the requested target: continue directly when already on target, otherwise restore Feed or enter Reels before continuing.
- Trigger one immediate redrive only after a group/comment action chain has reached a terminal receipt (including `submitted_unknown`) and its final page-write lease release has been acknowledged. Intermediate lease releases used by a multi-step task continue to preserve the task page.
- Replace the sticky Reels `confirmed` fallback state with current page observations plus a bounded in-flight entry attempt. A past Reels confirmation no longer stands in for the current page.
- Keep pause, quota, risk, ownership, and session-validity gates authoritative; resume redrive is not permission to bypass them.

## Capabilities

### Modified Capabilities

- `session-auto-resume`: define the unified `resume_redrive` payload and terminal evidence while retaining the existing `page.scroll` protocol message.
- `facebook-primary-browse-surface`: use the pinned primary surface as the target of every unified redrive.
- `facebook-reels-browse`: replace sticky historical confirmation with current-surface observation and bounded entry-in-flight state.
- `edge-task-execution-coordination`: distinguish intermediate task lease release from final workflow release and immediately redrive only after the final release acknowledgement.

## Impact

- Control: OpenSpec deltas and protocol documentation.
- Cloud: Facebook consumption action-chain settlement, RoleDispatcher redrive dispatch, primary-surface/state tracking, and focused tests.
- Edge: protocol decoding, Native page-engine command mapping/execution, and focused Rust/TypeScript tests.
- No new protocol message type is introduced. The existing `page.scroll` payload gains a backward-compatible optional target surface used by `resume_redrive`.
- No packaging or deployment is included in this change.
