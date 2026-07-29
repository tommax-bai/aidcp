## Why

Facebook rule-mode join-comment notifications currently collapse `verification_ambiguous` into “已加群，但未评论 / 群内评论未发出”. That contradicts the underlying receipt: submit was dispatched and counted, but Facebook did not provide bounded confirmation that the comment became visible.

## What Changes

- Render a distinct warning receipt for `verification_ambiguous`: the group was joined, the comment was submitted, and the publication result remains unconfirmed.
- Keep confirmed comments as success and keep pre-submit, rejected, approval-pending, and other known-not-live outcomes on their existing non-submitted paths.
- Preserve the current risk accounting, de-duplication, no-retry, activity-feed, and platform-confirmed-success boundaries.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-comment-verification`: Require user-visible combined result cards to distinguish an unconfirmable dispatched submission from a comment that was never submitted.

## Impact

- `aidcp-cloud/src/comment-agent/comment-scheduler.ts`
- Focused Cloud comment-scheduler tests
- No protocol, database, Edge runtime, Console, quota, retry, or installer changes
