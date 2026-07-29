## Why

The installed Native runtime now completes the fixed 12.5-second, five-sample bottom-confirmation window, but Facebook's localized end marker is absent or unstable across layouts. Requiring that marker in every sample leaves an otherwise stable near-bottom home Feed in an endless `feed_continuation_unconfirmed` loop and never authorizes the existing Reels fallback.

## What Changes

- Confirm a previously non-empty canonical home Feed as `feed_exhausted` after the existing five samples at `t=0 / 5 / 7.5 / 10 / 12.5s` remain structurally stable.
- Treat "near bottom" as sufficient entry and continuation evidence using the actual scrolling container's viewport; the scrollbar does not need to be exactly at the mathematical bottom.
- Require every sample to retain the same URL, document time origin, home surface, and document generation; keep document age monotonic between adjacent samples; remain non-loading and near-bottom; show no height growth above 100px; and retain the same ordered canonical post-identity vector.
- Keep the localized `explicit_end` observation for diagnostics and the separate initial-home-empty ladder, but remove it as a hard gate only when the commanded list context began on home and the non-empty witness belongs to that same home document.
- Preserve fail-closed handling when loading, growth, a new post, navigation, refresh, generation change, or surface change invalidates the window. Do not extend marker-free structural exhaustion to search or group surfaces.
- Reuse the existing `feed_exhausted` receipt and Cloud-owned `empty_feed_reels_fallback` authorization; add only a bounded internal `documentTimeOriginMs` probe fact, with no external protocol field, reason code, retry, timer, or Cloud transition path.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-feed-continuity`: Replace the localized end-marker requirement for a previously non-empty canonical home Feed with the fixed five-sample structural confirmation contract.
- `native-facebook-behavior-parity`: Align the Native adapter's home-Feed exhaustion outcome with that structural contract while preserving bounded continuation and existing list-surface boundaries.

## Impact

- `aidcp-edge/native/page-engine/src/facebook/feed.rs`, `facebook.rs`, and `facebook-router/20-feed.js`: bottom-confirmation classification plus an exact document-epoch probe fact.
- Native Rust tests covering the exact five-sample schedule, structural invalidation, prior-card evidence, near-bottom semantics, and marker-independent completion.
- Existing router `explicit_end` extraction remains available as bounded diagnostic/empty-state evidence.
- No Cloud, protocol, Console, database, deployment, or risk-accounting change.
