## Context

The current Native adapter enters bottom confirmation when a list is near-bottom and stable, then samples at `t=0 / 5 / 7.5 / 10 / 12.5s`. It nevertheless returns `feed_exhausted` only when a localized `explicit_end` marker is present in all five samples. Real runtime evidence shows the complete 12.5-second window repeating as `feed_continuation_unconfirmed` because that marker is absent or unstable, even though there is no loading signal, document growth, new canonical post, navigation, or refresh.

The retired TypeScript path used structural near-bottom, no-growth, and no-new-card evidence rather than a localized end marker. The newer five-sample schedule is a stronger bounded observation window and can restore that structural business meaning without restoring the retired executor.

The active `restore-native-facebook-residual-parity` change introduced the five-sample schedule together with the stricter five-of-five marker gate. This change is the later product decision and supersedes only that marker requirement for a previously non-empty canonical home Feed.

The 2026-07-30 Daniel Golden live run then proved that "canonical card" was implemented too narrowly. The router returned two legitimate cards with `note_id_kind=content_ref` and zero permalink cards, but Rust's permalink-only `facebook_feed_card_identities` and `facebook_page_cards` paths discarded both. The command therefore neither reported those cards nor retained them as a non-empty-feed witness, and every otherwise valid 12.5-second window ended as `feed_continuation_unconfirmed`. Relaxing only the witness would invert the defect: Native could skip an unseen reportable card and switch to Reels. Reporting, seen-state, structural identity, and the witness must therefore share one typed validation rule.

## Goals / Non-Goals

**Goals:**

- Let a canonical home Feed that has shown real validated Feed identities reach `feed_exhausted` after all five structural samples remain stable.
- Treat a strictly validated, explicitly typed `content_ref` as a real reportable Feed identity alongside a validated permalink, and report every unseen identity before considering exhaustion.
- Use one typed identity projection for new-card reporting, session seen deduplication, five-sample vector equality, and the command-local non-empty-feed witness.
- Treat near-bottom—remaining distance no greater than the actual scrolling container's viewport—as sufficient; do not require exact mathematical bottom or substitute the browser-window height for a smaller nested scroller.
- Keep the full 12.5-second schedule, no-early-success rule, cancellation, deadline, and structural invalidation behavior.
- Preserve Cloud ownership of the actual Reels transition.

**Non-Goals:**

- Do not make search or group near-bottom stability authorize the home-Feed Reels fallback.
- Do not change the separate confirmed-empty or present-unreportable ladders.
- Do not widen what counts as a `content_ref`, infer its kind from its string prefix, persist it, or make it navigable/cross-session-capable.
- Do not add a retry counter, fallback timer, protocol field, reason code, Cloud handler, or configurable threshold.
- Do not package or release an Edge installer as part of source implementation.

## Decisions

### 1. Five structural samples, not five localized marker samples, prove home-Feed exhaustion

The fixed sample offsets remain `0 / 5 / 7.5 / 10 / 12.5s`. A home confirmation is valid only while every sample:

- stays on the same URL and exact `document_time_origin_ms` document epoch and the same document generation, with `document_age_ms` never moving backward relative to the immediately preceding sample;
- stays on the canonical home list surface;
- is non-loading and near-bottom according to the actual feed scroll node's `scroll_viewport_height`;
- grows by no more than the existing 100px reflow noise floor relative to the initial sample (`>100px` invalidates); and
- exposes the same ordered validated Feed identity vector as the initial sample.

The fifth valid structural sample produces the confirmed exhaustion state. None of the first four samples may succeed.

Alternative rejected: require the scrollbar to reach exactly zero remaining distance. Facebook virtualized layouts can retain padding or a terminal card below the effective content boundary; exact bottom is less stable than the existing one-viewport near-bottom predicate.

### 2. `explicit_end` remains observable but is not a home exhaustion gate

The router continues to extract the bounded localized marker. It remains useful for diagnostics, settle-key changes, the existing initial-home-empty evidence, and unchanged non-home behavior. Home exhaustion classification no longer counts or resets on this field.

Alternative rejected: expand the marker vocabulary. Layout and localization variants make vocabulary maintenance an open-ended hard dependency; it cannot guarantee progress.

### 3. A command-local validated-identity witness is required before structural exhaustion

The commanded list context must have begun on home, and that command must have observed at least one validated Feed identity on the same home URL and document time origin before it may return marker-free `feed_exhausted`. A permalink witness is based on the canonical Facebook post identity extracted from a validated content URL. A `content_ref` witness is accepted only when the card explicitly declares the `content_ref` kind and the value satisfies the existing exact prefix plus 64-lowercase-hex digest format; the value's prefix alone never determines its kind.

The witness is command-local. It may survive Facebook virtualization removing the earlier visible card within that command, but it may not be inherited by a later command, another URL, or another document time origin. A search/group command that is redirected to home mid-command does not inherit this authorization. A structurally quiet zero-validated-identity home continues through the existing empty, loading, blocked, and present-unreportable evidence ladder.

Alternative rejected: classify any stable near-bottom zero-card page as exhausted. That would conflate a non-empty Feed reaching its end with first-screen empty, blocked, or unreportable states.

### 4. One typed validated-identity projection precedes reporting and exhaustion

Rust must project every router card into one of two typed validated identities:

- **Permalink:** `note_id_kind` is absent or `permalink`, the value passes the existing Facebook content-URL validation, and the identity key is the canonical Facebook post identity extracted by the existing permalink parser.
- **ContentRef:** `note_id_kind` is explicitly `content_ref`, the value passes the existing strict `aidcp:facebook-group-feed-post:v1:<64 lowercase hex>` validator, and the identity key retains the `content_ref` type so it cannot collide with a permalink value.

A kind/value mismatch or malformed value produces no validated identity and cannot report a card, alter seen-state, enter the five-sample vector, or establish the witness. This is fail-closed validation, not permissive string inference.

The same projection feeds four consumers: `facebook_page_cards`, the session seen set, the ordered settle/bottom-confirmation vector, and the command-local witness. Card delivery comes first: if the current probe contains an unseen validated identity, Native reports that card to Cloud and does not return exhaustion from that observation. A later observation may filter the already-seen identity through the same typed key; only when no unseen validated card remains and the full five-sample structural window succeeds may the existing exhaustion path run. Existing `content_ref` lifetime and capability rules remain unchanged: it is session-scoped, list-surface/document-generation-bound, never persisted, never treated as a URL, and never used for cross-session deduplication.

Alternative rejected: patch only `FacebookCanonicalCardWitness::from_probe`. That would make a previously dropped unseen `content_ref` authorize Reels without first giving Cloud the card to evaluate and count.

### 5. The receipt and Cloud transition remain unchanged

Edge continues to return the existing confirmed `action.completed{action:scroll,ok:false,reason:feed_exhausted}` receipt. Cloud remains the sole authority that sends `scroll{reason:empty_feed_reels_fallback}` and applies its session, quota, pacing, and idempotency gates.

No Cloud or external protocol change is required because only the evidence producing the existing receipt changes. The Native router adds bounded integer `documentTimeOriginMs` to its internal Feed probe so a same-URL reload cannot reuse the previous document's evidence.

### 6. The predecessor active artifact must not later restore the rejected gate

The conflicting five-of-five `explicit_end` clauses in `restore-native-facebook-residual-parity` must be synchronized to cite this later decision before integration. This avoids a future archive of that still-active change reintroducing the rejected marker requirement into the baseline specification.

## Risks / Trade-offs

- **A silent Facebook pagination failure can look structurally exhausted without exposing loading.** → Require five samples over 12.5 seconds, near-bottom throughout, no height growth above 100px, an unchanged ordered validated identity vector, the same URL/document epoch/generation, and a prior same-command/same-document validated-identity witness. Reels navigation remains Cloud-authorized, session-bounded, and reversible.
- **Accepting `content_ref` only in the witness can skip unseen content.** → Drive reporting, typed session deduplication, the structural vector, and the witness from the same validator; report an unseen validated card before entering exhaustion.
- **A string that resembles `content_ref` can be mistaken for a trusted identity.** → Require the explicit identity kind plus the exact existing prefix/digest validator; malformed or mismatched values fail closed and provide no exhaustion evidence.
- **A marker-free rule could pull search or group browsing into Reels.** → Require both a home command context and a canonical home confirmation surface; a mid-command redirect from search/group to home remains continuation unless existing explicit terminal evidence is complete.
- **Virtualization can remove or reorder old cards without adding content.** → Preserve the current conservative identity-vector equality check. Such movement invalidates confirmation and continues Feed rather than fabricating exhaustion.
- **Source integration does not update installed clients.** → Report source, package, and installed-runtime state separately; do not claim live acceptance until a later package is installed and observed.

## Migration Plan

1. Update the OpenSpec deltas and synchronize the predecessor active artifact.
2. Change the Native typed identity projection, reporting/deduplication path, classifier, and focused Rust tests in an isolated Edge worktree.
3. Run focused Feed tests, the full Native gate, Edge typecheck/contract tests as proportionate, and strict OpenSpec validation.
4. Rebase and fast-forward source changes to the default branches.
5. Package or release only under a separate explicit user instruction.

Rollback is a source revert of the Edge classifier commit; no data or protocol migration is involved.

## Open Questions

None.
