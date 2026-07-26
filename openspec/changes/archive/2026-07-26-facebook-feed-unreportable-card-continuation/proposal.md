## Why

Facebook lightweight feeds can show a real, readable video or media card while exposing no post-shaped permalink accepted by Edge. The current initial-feed path rescans that same viewport, reports “0 cards,” and returns without scrolling, so a common unreportable first card can stall the browse loop until a much later Cloud watchdog nudge.

## What Changes

- Treat a structurally present but unreportable feed card as a skip signal, not as an empty feed or a terminal initial-feed result.
- Continue downward with bounded, humanized feed scrolling until a reportable card is found or the existing honest exhaustion/loading limits are reached.
- Support the observed lightweight Facebook video-card structure when it exposes a trustworthy post/video permalink within the exact card boundary.
- Preserve fail-closed identity: photo/video resource IDs, obfuscated timestamps, neighboring-card links, and content text alone never become a post identity.
- Make diagnostics distinguish visible/unreportable cards from a genuinely empty homepage.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-feed-continuity`: Initial feed bootstrap and scroll recovery continue past visible cards that cannot be reported, instead of waiting idle on the same viewport.
- `facebook-feed-browse`: Lightweight video cards use exact-card trustworthy identity when available; otherwise they are skipped and browsing continues without fabricating a target.

## Impact

- `aidcp-edge`: Facebook feed reader/session, shared lightweight-card helpers, focused fixtures, acceptance coverage, and diagnostic logging.
- No protocol, Cloud orchestration, risk-state, quota, write-authorization, or packaging change.
