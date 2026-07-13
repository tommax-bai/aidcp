## Why

Facebook feed browsing currently emits one fixed 900px wheel event and then always applies another 900px JavaScript scroll. The visible result is rigid, can move twice as far as intended, and does not match the inertial interaction model already used for XHS.

## What Changes

- Replace Facebook feed's fixed single-wheel scroll with a jittered, multi-frame inertial wheel sequence.
- Remove the unconditional JavaScript `scrollBy` after a successful wheel gesture; retain a bounded fallback only when the gesture did not move the page.
- Use the same gesture helper for Facebook comment-editor lazy-load scrolling so the two Facebook surfaces do not diverge.
- Add deterministic regression coverage for the gesture shape, total movement, fallback boundary, and failure behavior.

## Capabilities

### New Capabilities

- `facebook-humanized-scroll`: Defines Facebook feed and comment-editor scrolling as bounded, inertial, observable wheel gestures with a verified fallback.

### Modified Capabilities

- None.

## Impact

- Affected repo: `aidcp-edge` only, primarily `src/facebook/feed-reader.ts` and `src/facebook/comment-executor.ts`.
- Reuses the existing `src/humanize/scroll-physics.ts` sequence generator; no new protocol messages, cloud policy changes, or rollout-switch changes.
- Existing cloud `dwellMs`, quotas, overlay monitoring, and `AIDCP_FB_BROWSE_AUTO` safety behavior remain authoritative and unchanged.
