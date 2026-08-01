## Why

Native Facebook Feed wheel RPCs can return successfully while a background AdsPower page makes no physical scroll movement. The current Feed path can still confirm the command from already-readable cards, leaving the account visually stalled until the later watchdog foregrounds the browser.

## What Changes

- Keep the first ordinary Facebook Feed wheel gesture background-safe.
- When bounded same-document readback proves that the completed gesture made no movement on a ready, scrollable, non-terminal list, activate the exact bound target once and retry one fresh wheel gesture.
- Treat an already-foregrounded watchdog command as having consumed that one activation; it must never activate twice.
- Suppress adaptive activation after measured movement, at a confirmed bottom, while loading or blocked, after document/surface drift, or before input was actually dispatched.
- Require movement readback after the foreground recovery; if it still does not move, return an honest ambiguous scroll outcome instead of confirming from stale cards.
- Do not add a JavaScript scrolling fallback, a Cloud field, configuration, an unbounded retry, or a new browser-control channel.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-humanized-scroll`: replace the no-movement fallback contract with one exact-target foreground recovery and one freshly located Native wheel retry.
- `native-facebook-behavior-parity`: narrow the watchdog-only foreground rule so an ordinary Feed scroll may activate only after bounded same-document no-movement proof, while retaining the one-activation ceiling.

## Impact

- `aidcp-edge/native/page-engine/src/facebook/feed.rs`
- `aidcp-edge/native/page-engine/src/facebook/reels.rs`
- Focused Native Facebook scroll tests and fake-CDP ordering assertions
- No Cloud, Console, wire-shape, dependency, packaging, or deployment change
