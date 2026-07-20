## Context

Facebook's current lightweight Vietnamese feed layout exposes an author heading, a `story_message`, media, and post actions inside an ordinary `div`, but the timestamp anchor can resolve to `/` and the only media href can be `/photo/?fbid=...`. A live read-only probe of the active Mi Xu profile reproduced one visible lightweight card with `hydratedArticles=1` and `scanCards=[]`: the structural card existed, but there was no trustworthy post identity. A second live probe captured the lightweight video card `Mời các bác ăn sáng #Buffet`; its exact-card `/watch/?v=1547652190157533` anchor was already recognized as `fb:1547652190157533`, and the current reader returned one reportable `isVideo=true` card. The video path therefore needs a regression fixture, not a broader identity rule.

`reportInitialFeed` currently waits for `settleCards`. When the result is `no_feed`, `confirmHomeEmpty` correctly returns `cards_ready` for such a visible card, but the session then logs and returns. The Edge emits no `page.cards`, so Cloud cannot drive the normal content-selection chain; only the idle watchdog can eventually nudge a scroll.

The existing canonical identity boundary already accepts exact-card `/watch?v=`, `/videos/<id>`, and `/reel/<id>` links. It deliberately rejects media resource IDs, `/` timestamp anchors, and obfuscated/non-post links. This change must preserve that boundary.

## Goals / Non-Goals

**Goals:**

- Continue the initial browse loop immediately when the current viewport contains visible but unreportable lightweight cards.
- Reuse the existing bounded, humanized, lazy-load-aware scroll loop so recovery has one pacing and exhaustion policy.
- Cover lightweight video cards explicitly: report them when the exact card exposes an accepted video-post link; otherwise skip them and continue.
- Keep empty-feed/Reels authorization separate from visible-unreportable-card continuation.
- Emit diagnostics that say “unreportable cards” instead of claiming the homepage has zero cards.

**Non-Goals:**

- Deriving a post id from text, author, DOM order, `/photo/?fbid`, CDN video URLs, or opaque timestamp text.
- Clicking a video, timestamp, media, or menu to discover identity.
- Changing Cloud, protocol messages, risk state, quotas, interaction authorization, or Edge packaging.

## Decisions

### Reuse the existing scroll command implementation for bootstrap recovery

When initial settle returns no reportable cards and `confirmHomeEmpty` returns `cards_ready`, `reportInitialFeed` will invoke the same internal feed-scroll routine used by `page.scroll`. That routine already performs bounded humanized scrolling, loading-aware settling, unseen-card filtering, lazy-load growth checks, and honest `no_target`/`feed_exhausted` outcomes.

The bootstrap path will emit only a resulting `page.cards` observation. It will not emit an unsolicited `action.completed`, because no Cloud command exists to receive that action receipt. A bounded failure remains a diagnostic and leaves the later watchdog as a final recovery layer.

Alternative: add a second bootstrap-only scrolling loop. Rejected because it would duplicate pacing, exhaustion, cursor, and empty-feed behavior and drift from command-driven scrolling.

### Use `cards_ready` as the structural skip signal

`confirmHomeEmpty` reads card presence independently of reportable identity. Its `cards_ready` state therefore means the homepage is not empty and the current viewport contains a structural card that may be unreportable. That is the exact condition that should trigger continuation. `feed_unknown`, login, captcha, loading, and confirmed empty states retain their existing fail-closed behavior.

Alternative: scroll on every `no_feed`. Rejected because an unknown or blocked page is not evidence that a safe feed card is present.

### Keep video identity source strict and exact-card scoped

The scanner and action resolvers continue to share the same top-level card boundary. A lightweight card containing `<video>` is reportable only when an anchor inside that exact card yields an existing canonical video-post identity (`watch?v`, `videos/<id>`, or `reel/<id>`). A video element, CDN source, media resource id, `/` timestamp anchor, or neighboring card link is not identity.

The target Vietnamese sentence is captured in a fixture representing the observed unreportable first-card shape. A paired fixture proves a lightweight video card with an exact-card `watch?v` permalink remains reportable.

Alternative: promote the video resource id or text hash. Rejected because later reads/actions could not prove they still target the same Facebook post.

## Risks / Trade-offs

- [Several consecutive media-only cards consume scroll budget] → Reuse the existing bounded multi-round loop; return honest `no_target` when the budget is exhausted and retain the Cloud watchdog as a later retry.
- [Bootstrap continuation races a page/navigation change] → Every round retains `ensureFeed`, blocking checks, loading-aware settle, and current document/surface checks.
- [A reportable card appears after an unreportable video card] → The continuation emits only the newly discovered canonical card and seeds the session cursor through the existing path.
- [Facebook later exposes a new trustworthy video permalink shape] → Capture a live fixture and extend the canonical parser separately; do not infer it from media bytes or visible text.

## Migration Plan

1. Add Edge fixtures and session tests, then implement the minimal session continuation.
2. Run Facebook focused tests, acceptance, full Edge tests, and typecheck.
3. Land Edge on `master`; no Cloud deployment or desktop package is required.
4. Validate read-only against an active AdsPower Facebook profile: a visible unreportable first card must be skipped and a later reportable card observed without any interaction.
5. Roll back the Edge commit if initial sessions over-scroll or emit unsolicited action receipts.

## Open Questions

None. The original media-only sentence was virtualized out before CDP attachment, but the active profile reproduced the same decisive unreportable identity shape (`/` timestamp plus media-only href). The user-positioned `Mời các bác ăn sáng #Buffet` video card was captured separately and proved that exact-card `watch?v` video identity already works. The contract intentionally depends on structural/identity evidence rather than an account or sentence.
