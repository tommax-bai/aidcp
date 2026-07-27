## Why

Nancy's DEV Facebook session can report `feed_exhausted` before the Native runtime has observed a complete height-stability window or an explicit terminal marker. After Cloud confirms the resulting Feed-to-Reels fallback, later non-empty Feed cards do not reopen fallback authorization, so another truthful exhaustion can be silently ignored until the idle watchdog fires.

## What Changes

- Make Native Facebook Feed settling observe document height throughout the existing bounded wait instead of returning as soon as card identities appear stable.
- Treat a stable explicit end-of-feed marker as positive terminal evidence, while retaining no-growth, near-bottom, consecutive confirmation as the structural path.
- Remove the round-limit shortcut that reports `feed_exhausted` merely because any card was seen; insufficient evidence returns an observable non-terminal continuation receipt that Cloud maps to another gated ordinary scroll.
- Reset Cloud's confirmed Reels-fallback epoch only after a later non-empty Facebook Feed batch proves the session has returned to a Feed list, while preserving pending-handshake and same-epoch deduplication.
- Add focused Edge and Cloud regressions for delayed height growth, explicit terminal evidence, unconfirmed round exhaustion, duplicate fallback reports, and Feed re-entry.

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
