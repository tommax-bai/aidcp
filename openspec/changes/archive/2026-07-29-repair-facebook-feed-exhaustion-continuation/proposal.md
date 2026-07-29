## Why

Nancy's DEV Facebook session can report `feed_exhausted` without an explicit terminal marker. Live DEV inspection showed both that a background AdsPower Facebook target can leave `Input.dispatchMouseEvent` unanswered and that the page can hold a constant-height near-bottom skeleton without exposing it through the Feed probe's loading selectors. The former prevents the wait logic from starting at all; the latter means structural stability cannot distinguish exhaustion from opaque lazy loading. After Cloud confirms the resulting Feed-to-Reels fallback, later non-empty Feed cards also need to reopen fallback authorization so another truthful exhaustion is not silently ignored until the idle watchdog fires.

## What Changes

- Make Native Facebook Feed settling observe document height throughout the existing bounded wait instead of returning as soon as card identities appear stable.
- Foreground the exact bound Facebook target before `page_scroll` input so an inactive AdsPower tab cannot leave the CDP gesture awaiting a response until the atomic deadline.
- Treat a stable explicit end-of-feed marker as the only positive terminal evidence; no-growth near the bottom remains a bounded observation window but never proves exhaustion by itself.
- Remove the round-limit shortcut that reports `feed_exhausted` merely because any card was seen; a complete stable bottom window without terminal evidence returns an observable non-terminal continuation receipt immediately, while other unresolved rounds retain their bound.
- Reset Cloud's confirmed Reels-fallback epoch only after a later non-empty Facebook Feed batch proves the session has returned to a Feed list, while preserving pending-handshake and same-epoch deduplication.
- Add focused Edge and Cloud regressions for target foregrounding, delayed height growth, constant-height opaque loading, explicit terminal evidence, unconfirmed continuation, duplicate fallback reports, and Feed re-entry.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `native-facebook-behavior-parity`: Tighten Native settling and exhaustion evidence so the bounded tail cannot bypass the established contract.
- `facebook-feed-continuity`: Replace the contradictory round-limit `feed_exhausted` shortcut with honest non-terminal completion and recognize stable explicit end-of-feed evidence.
- `facebook-feed-browse`: Scope Reels-fallback idempotency to a confirmed Feed/Reels epoch and reopen authorization after authoritative non-empty Feed re-entry.

## Impact

- `aidcp-edge`: Native Page Engine Facebook Feed probe/settle/scroll logic and focused Rust tests.
- `aidcp-cloud`: `RoleDispatcher` Reels-fallback state transitions and integration tests.
- `aidcp`: OpenSpec deltas and validation records.
- No protocol expansion, database migration, new pacing knob, installer build, OL deployment, or Facebook write action.
