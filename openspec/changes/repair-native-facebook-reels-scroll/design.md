## Context

The Cloud already distinguishes Facebook `listKind='reels'` and sends `page.scroll` with a pacing `dwellMs`. After the Native-only cutover, the selector-free TypeScript facade forwards that command, but the embedded Facebook router ignores `dwellMs` and executes the same `window.scrollBy` branch for Feed and Reels. Reels keeps neighbouring videos mounted in a snap surface, so document `scrollY` is not a valid forward-navigation witness.

The retired TypeScript `FacebookReelsReader` contains the proven mechanism: resolve one active Reel by viewport intersection, bind it to `noteId + videoKey`, try trusted ArrowDown, then a small wheel over the active video, then one constrained next-button click, and verify identity after each attempt.

## Goals / Non-Goals

**Goals:**

- Keep Cloud as the pacing and orchestration authority while making the Native-only Edge path consume the existing `dwellMs`.
- Move a Reels page only through trusted CDP input and report new cards only after the active Reel identity changes.
- Stop honestly with one failed scroll receipt when all bounded Reels navigation methods make no proven movement.
- Preserve ordinary Feed scrolling and the existing protocol.

**Non-Goals:**

- Changing Facebook selection, interaction probability, quotas, or Cloud risk state.
- Adding a JavaScript/legacy runtime fallback.
- Adding a new protocol message or exposing Native-only diagnostic fields to Cloud.
- Packaging, signing, or publishing an installer.

## Decisions

### Keep the dwell anchor in the selector-free Native session facade

`NativeBrowseSession` observes when `page_cards` is handed to the Edge client, which is the existing contract anchor for feed dwell. It will retain a monotonic `lastCardsAt`, jitter the Cloud-provided center once, subtract elapsed Cloud evaluation time, and wait only the positive remainder before dispatching `page_scroll`.

This is timing orchestration, not page intelligence, so it does not weaken the Native-only boundary. Storing the anchor in Rust was rejected because Rust does not know when the TypeScript client actually handed the cards to Cloud and would either double-count transport time or require a new protocol.

### Execute Reels navigation in Rust with embedded typed probes

Rust will probe the active Reel through the embedded Facebook router, then issue trusted CDP input in this order:

1. ArrowDown key down/up.
2. One small wheel event centred on the freshly re-probed active video.
3. One click on a freshly resolved, geometrically constrained next button.

Before every fallback write, the engine re-probes identity. Late movement wins and suppresses the next write. This preserves the single-writer boundary and prevents double navigation.

Direct `window.scrollBy` was rejected for Reels because document movement is not the surface's post-condition. Calling the retired TypeScript `FacebookReelsReader` was rejected because it would recreate a production JavaScript fallback after the Native-only cutover.

### Treat `noteId + videoKey` as the movement witness

The active Reel probe selects the single visible video with the largest viewport intersection and derives:

- a canonical Reel permalink from the active container or current route;
- a per-element video key based on media source plus a bounded page-local element identity.

Navigation succeeds only when either component changes from the pre-action identity and the active target remains unambiguous. A successful move returns a fresh `page_cards{listKind:'reels'}`. Exhausting all methods returns `action_receipt{action:'scroll', ok:false, reason:'no_target'}` and does not emit `page_cards`.

### Keep Feed behavior separate

Non-Reels `page_scroll` continues through the existing Feed router. The Reels probe's `not_reel` result is the only condition that selects that path; missing or ambiguous active video on a Reels route fails honestly instead of falling back to document scroll.

## Risks / Trade-offs

- [Facebook changes Reels markup or controls] → Active-video and button probes are geometry-bound, localized, and fail closed with `no_target`; tests cover ambiguity and missing targets.
- [A delayed transition happens between fallback probes] → Re-probe immediately before each write and accept the late movement without issuing another input.
- [Dwell wait delays shutdown or task takeover] → Make the wait abortable and part of the session's existing active-command boundary.
- [A video element is reused without a URL change] → Include a page-local video element identity in `videoKey`; require the pair rather than route alone.
- [Normal Feed regresses] → Keep its router branch unchanged and add a contract regression proving it still uses the existing document scroll path.

## Migration Plan

1. Land the OpenSpec contract and Edge implementation on their named branches.
2. Run focused TypeScript and Rust tests, Native build/verification, acceptance tests, full Edge tests, and typecheck.
3. Fast-forward the validated branches into their default branches and push.
4. Do not claim installed-client behavior until a desktop artifact containing the rebuilt Native binary is packaged and installed.

Rollback is a normal revert of the Edge commit; there is no data migration or Cloud protocol dependency.

## Open Questions

None. The prior Reels actuator establishes the input order and identity contract, and the current `page.scroll`/`page.cards`/`action.completed` protocol is sufficient.
