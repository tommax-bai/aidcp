## Why

The installed Native runtime now completes the fixed 12.5-second, five-sample bottom-confirmation window, but Facebook's localized end marker is absent or unstable across layouts. Requiring that marker in every sample leaves an otherwise stable near-bottom home Feed in an endless `feed_continuation_unconfirmed` loop and never authorizes the existing Reels fallback.

The 2026-07-30 Daniel Golden live run exposed a second identity-path defect after that structural rule shipped: the page contained two valid cards declared as `content_ref` and no permalink cards, while Rust's Feed identity projection accepted only values parseable as Facebook permalinks. It therefore dropped both cards from new-card reporting, session seen-state, the five-sample identity vector, and the prior-card witness. Merely relaxing the witness would be unsafe because an unseen, reportable `content_ref` card must reach Cloud before the same viewport can be classified as exhausted.

## What Changes

- Confirm a previously non-empty canonical home Feed as `feed_exhausted` after the existing five samples at `t=0 / 5 / 7.5 / 10 / 12.5s` remain structurally stable.
- Define a Feed card identity through its declared identity kind rather than through permalink parsing alone: a permalink uses the canonical Facebook post identity extracted from its validated content URL, while a `content_ref` must be explicitly typed and satisfy the existing strict `aidcp:facebook-group-feed-post:v1:<64 lowercase hex>` format.
- Use the same typed validated-identity projection for card reporting, session seen deduplication, the ordered five-sample identity vector, and the non-empty-feed witness. A fresh `content_ref` card MUST be reported before bottom confirmation may return exhaustion.
- Treat "near bottom" as sufficient entry and continuation evidence using the actual scrolling container's viewport; the scrollbar does not need to be exactly at the mathematical bottom.
- Require every sample to retain the same URL, document time origin, home surface, and document generation; keep document age monotonic between adjacent samples; remain non-loading and near-bottom; show no height growth above 100px; and retain the same ordered validated Feed identity vector.
- Keep the localized `explicit_end` observation for diagnostics and the separate initial-home-empty ladder, but remove it as a hard gate only when the commanded list context began on home and the non-empty witness belongs to that same command, home URL, and document time origin. A `content_ref` witness MUST NOT be carried into another command or document.
- Preserve fail-closed handling when loading, growth, a new post, navigation, refresh, generation change, or surface change invalidates the window. Do not extend marker-free structural exhaustion to search or group surfaces.
- Reuse the existing `feed_exhausted` receipt and Cloud-owned `empty_feed_reels_fallback` authorization; add only a bounded internal `documentTimeOriginMs` probe fact, with no external protocol field, reason code, retry, timer, or Cloud transition path.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-feed-continuity`: Replace the localized end-marker requirement for a previously non-empty canonical home Feed with the fixed five-sample structural confirmation contract, using both validated permalink and `content_ref` identities.
- `native-facebook-behavior-parity`: Align Native card reporting, session deduplication, and home-Feed exhaustion evidence on one typed identity projection while preserving bounded continuation and existing list-surface boundaries.

## Impact

- `aidcp-edge/native/page-engine/src/facebook/feed.rs`, `facebook.rs`, and `facebook-router/20-feed.js`: typed Feed identity projection, bottom-confirmation classification, and an exact document-epoch probe fact.
- Native Rust tests covering permalink and `content_ref` reporting/deduplication, the exact five-sample schedule, structural invalidation, prior-card evidence, near-bottom semantics, and marker-independent completion.
- Existing router `explicit_end` extraction remains available as bounded diagnostic/empty-state evidence.
- No Cloud, protocol, Console, database, deployment, or risk-accounting change.
