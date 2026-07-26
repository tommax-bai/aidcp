## Why

The Native Facebook startup Feed probe returns `documentAgeMs` as a fractional JavaScript number while Rust requires an unsigned integer, so a real Chrome session fails its first bounded-result decode and never starts browsing. This must be corrected at the internal Native boundary and covered across the JavaScript-to-Rust decode path.

## What Changes

- Normalize the Facebook Feed probe document age to a finite, non-negative integer before it crosses the Native router boundary.
- Add a cross-boundary regression test that decodes a realistic fractional browser time origin through the Rust Feed probe model.
- Preserve the current initial Feed navigation, bounded settling, failure honesty, Cloud orchestration, and Native-only routing.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-feed-continuity`: Require Native Feed probes to remain decodable for real browser timing values so startup and resumed browse generations can enter the existing bounded Feed flow.

## Impact

- Affected repository: `aidcp-edge`.
- Affected code: the embedded Facebook command router and Rust Native probe contract/tests.
- No Edge-Cloud protocol, Cloud policy, database, configuration, installer, or OL deployment changes.
