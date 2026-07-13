## Context

The Facebook feed reader currently sends one fixed 900px `mouseWheel` event and then unconditionally executes `window.scrollBy(0, 900)`. The first event has no acceleration or deceleration; the second can double the visible movement. The Facebook comment executor has the same fixed-wheel plus unconditional-JS-fallback pattern.

XHS already uses `generateScrollSequence` from `src/humanize/scroll-physics.ts`: it jitters a target distance, divides it into 8-15 wheel frames with an acceleration-to-deceleration envelope, and spaces frames by 16-60ms. Facebook can reuse that platform-neutral primitive, but must retain its own selector and page-readiness behavior.

## Goals / Non-Goals

**Goals:**

- Give Facebook feed and comment-editor scrolling a bounded, visible inertial wheel gesture.
- Preserve one-feed-screen overlap by using a 650px baseline with +/-20% per-gesture distance jitter.
- Prevent a successful wheel gesture from being followed by an unconditional second scroll.
- Keep the fallback honest and bounded when CDP wheel input does not move the Facebook document.
- Preserve existing cloud-provided dwell, command timeout, overlay handling, quota, and `AIDCP_FB_BROWSE_AUTO` behavior.

**Non-Goals:**

- No change to cloud orchestration, protocol messages, real-like enablement, or account risk accounting.
- No attempt to implement missing Facebook capabilities such as image browsing, author-follow, or comment deep-reading.
- No mouse-path simulation for post open or changes to the React-required atomic like click in this change.

## Decisions

### One Facebook-owned viewport gesture helper

Create a small helper under `src/facebook/` that accepts CDP, a target baseline, injected random/sleep dependencies, and an optional logger. It owns viewport-centre cursor placement, jitter, inertial frame dispatch, movement observation, and fallback. Both `FacebookFeedReader` and `FacebookCommentExecutor` call it.

This avoids two copies of a security-sensitive fallback boundary. Reusing XHS `CdpFeedScroller` directly was rejected because its card scanning and interface are XHS-specific, while the physics generator is already the correct shared boundary.

### Wheel first, fallback after measured non-movement

The helper samples document scroll position before and after its wheel sequence. It calls `window.scrollBy` at most once only when the observed position did not change. A dispatch exception is treated the same way: it is logged, then position is checked before deciding whether a fallback is needed. The helper does not throw a transient CDP input failure into the browse loop.

This replaces the former unconditional double action. Always using JavaScript scrolling was rejected because it drops the hardware-like wheel event and fails to activate some lazy-load paths. Never falling back was rejected because a temporary CDP Input failure would make a feed appear frozen.

### Gesture profile and pacing boundary

The default Facebook feed baseline is 650 CSS pixels, jittered by +/-20%, then passed to `generateScrollSequence`. It produces 8-15 exact-sum frames and 16-60ms intra-gesture delays. The helper does not add the inter-command dwell: `FacebookBrowseSession.ensureFeedDwell` remains the sole owner of cloud-directed feed dwell. The comment executor retains its existing bounded editor-probe loop; only one probe scroll gesture changes shape.

Keeping gesture time separate from cloud dwell prevents accidental changes to session pacing or quota semantics.

## Risks / Trade-offs

- [A browser surface consumes wheel input without changing `window.scrollY`] -> Facebook's known feed and comment surfaces use document scrolling. The helper only falls back after measured document non-movement, and real-machine validation will record whether the fallback is used unexpectedly.
- [A partial CDP sequence moves the document before failing] -> observe movement before fallback; never add a second scroll after any measured movement.
- [More wheel frames add a few hundred milliseconds] -> these are intra-gesture timings, far below the existing multi-second cloud dwell and command timeout.
- [A smaller scroll misses cards] -> 650px preserves overlap between snapshots; the reader still reports an honest `no_target` when the subsequent scan has no usable cards.

## Migration Plan

1. Add the helper and deterministic unit tests.
2. Switch Facebook feed and comment-editor scroll callers to it.
3. Run edge focused tests, acceptance tests, full tests, and typecheck.
4. Merge to edge `master`, deploy the current edge runtime, then run Facebook import 1 in its existing gated mode to inspect actual scroll movement, dwell, fallback logs, and safety receipts.

Rollback is a single edge revert. It neither changes persisted data nor enables any interaction capability.

## Open Questions

- Real-machine observation will confirm whether 650px is the best Facebook baseline across the imported desktop profile; it can be tuned without touching cloud pacing if card overlap is too high or too low.
