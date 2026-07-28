## Context

The Native Facebook router currently makes `activeReel()` return `ok:false/no_active_identity` when a unique visible video exists on `/reel/` or `/reels/` but no canonical `/reel/<id>` is exposed. Rust then requires both `noteId` and `videoKey` before any input. This couples three different facts:

1. the page is a Reels surface;
2. exactly one active video is safe to target;
3. the active video has a canonical platform identity and may be reported or written to.

Facebook also serves at least two navigation layouts. The existing actuator and target locator encode only the vertical layout: `ArrowDown`, positive `deltaY`, and a lower control in a far-right vertical rail. A horizontally paged layout instead advances with `ArrowRight` or the right-side control.

The change remains inside the Edge Native page-understanding and atomic-action boundary. Cloud continues to receive only canonical cards and honest action receipts, and remains the owner of orchestration, pacing, view accounting, and risk.

## Goals / Non-Goals

**Goals:**

- Resolve one unique active video on a Reels landing route even when its canonical `noteId` is absent.
- Use that anonymous observation only to bind one bounded forward-navigation attempt.
- Infer a vertical or horizontal navigation axis from fresh structural evidence before dispatching input.
- Preserve one-write-at-a-time behavior and suppress every later fallback after any observed video transition.
- Report a card only after the post-state has both a canonical Reel identity and a stable active-video key.
- Make effect phases truthful: pre-dispatch failures stay `not_started`; an unverified post-dispatch result is `ambiguous`; a canonical post-state is `confirmed`.

**Non-Goals:**

- Generating a replacement `noteId` from description text, media URLs, hashes, or DOM order.
- Allowing likes, follows, comments, detail reads, or view accounting against an anonymous Reel.
- Adding a Cloud retry loop, compatibility flag, account-level layout configuration, or protocol-v2 field.
- Guessing horizontal wheel semantics or dispatching both vertical and horizontal keys as a blind probe.
- Packaging, signing, notarizing, or releasing an Edge installer in this change.

## Decisions

### 1. Separate targetability from reportable identity

`activeReel()` will return `ok:true`, `videoKey`, and `videoRect` whenever exactly one visible active video is structurally resolved on a Reels surface. `noteId` remains optional. `feedCards()` and every write-target resolver continue to require a canonical Reel identity, so the anonymous observation cannot leak into Cloud data or interaction commands.

An alternative was to hash the description or media source. That would create a locally stable-looking identifier from mutable, empty, duplicated, localized, or lazily hydrated content and could be mistaken for platform identity. It is rejected.

### 2. Treat anonymous entry as a one-transition bootstrap

Rust may dispatch navigation from an anonymous pre-state only when it has a unique `videoKey`, a current `videoRect`, and one unambiguous navigation axis. Bootstrap success requires a different active `videoKey` and a canonical post-state `noteId`; merely hydrating an id onto the unchanged first video does not prove that the requested forward navigation occurred.

If the video changes before route identity hydrates, the driver stops the fallback ladder and waits within the existing bounded card-read window. It never sends another key, wheel, or click after observing that transition. If no canonical card appears, the result is an ambiguous `reels_identity_unresolved` receipt.

### 3. Infer axis structurally and dispatch one matching key

The router will inspect bounded navigation-control candidates relative to the active video:

- a vertical rail is a previous/next pair whose centers are predominantly separated on the Y axis, including disabled previous controls used as layout evidence;
- a horizontal rail is a previous/next pair on opposite sides of the active video whose centers are predominantly separated on the X axis;
- localized semantic labels may identify previous/next roles, while geometry determines the axis;
- unlabeled controls are admitted only as a unique structural pair, with the lower member as vertical next or the right member as horizontal next.

The probe returns `axis: vertical|horizontal` plus the optional unique forward-control coordinates. Rust sends only `ArrowDown` (`keyCode=40`) for vertical or `ArrowRight` (`keyCode=39`) for horizontal. It does not try the other axis after an unchanged result because a late first transition followed by a second key could skip a Reel.

### 4. Keep fallbacks axis-specific and freshly bound

The vertical ladder remains key, one small trusted wheel over the freshly resolved active video, then the vertical next control. The horizontal ladder is key, then the horizontal next control; no horizontal wheel behavior is assumed.

Before each fallback write, both active-video identity and axis are re-probed. A changed video suppresses the write and enters canonical-card verification. Missing, ambiguous, moved, or axis-drifting button targets are not clicked.

### 5. Preserve canonical cards as the only success witness

Input dispatch, route hydration on an unchanged anonymous video, coordinate movement, and document scrolling are insufficient. `page.cards{listKind:'reels'}` with exactly one canonical card remains the external success result. This keeps existing Cloud deduplication and one-view-per-presented-Reel accounting unchanged for reportable cards while ensuring the anonymous landing video is not counted.

## Risks / Trade-offs

- **[Facebook serves a layout without a structurally provable control pair]** → Fail before dispatch with `no_target`; capture the real DOM/accessibility evidence before broadening the locator.
- **[A transition changes the video but delays the canonical route beyond the bounded window]** → Stop all further writes and return `ambiguous/reels_identity_unresolved`; do not risk skipping again.
- **[Disabled controls disappear entirely on the first item]** → Directional labels or other unique pair evidence may still resolve the axis; a generic single “Next” control remains intentionally insufficient.
- **[Existing tests assume missing identity means `ok:false`]** → Update fixtures to assert targetable-but-unreportable behavior and separately assert that card/read/write paths still reject it.
- **[Concurrent Reels humanization work changes the same Rust actuator]** → Rebase and integrate serially because `facebook/reels.rs` is overlapping code.

## Migration Plan

1. Add delta specifications and focused router/Rust tests.
2. Implement the targetability split and typed axis decode.
3. Implement the axis-aware, freshly re-probed actuator and truthful post-dispatch outcomes.
4. Run focused router and Rust tests, acceptance tests, full Edge tests, Native build/verification, and typecheck.
5. Rebase and fast-forward the Edge default branch serially. Rollback is the single Edge commit; no database or protocol migration is required.
6. A packaged-client or real-account acceptance remains a separate release boundary unless explicitly requested.

## Open Questions

- Real-account acceptance should record the exact accessibility labels and control rectangles for both layouts. The implementation intentionally does not broaden past structural evidence until those samples exist.
