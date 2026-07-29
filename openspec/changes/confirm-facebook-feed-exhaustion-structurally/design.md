## Context

The current Native adapter enters bottom confirmation when a list is near-bottom and stable, then samples at `t=0 / 5 / 7.5 / 10 / 12.5s`. It nevertheless returns `feed_exhausted` only when a localized `explicit_end` marker is present in all five samples. Real runtime evidence shows the complete 12.5-second window repeating as `feed_continuation_unconfirmed` because that marker is absent or unstable, even though there is no loading signal, document growth, new canonical post, navigation, or refresh.

The retired TypeScript path used structural near-bottom, no-growth, and no-new-card evidence rather than a localized end marker. The newer five-sample schedule is a stronger bounded observation window and can restore that structural business meaning without restoring the retired executor.

The active `restore-native-facebook-residual-parity` change introduced the five-sample schedule together with the stricter five-of-five marker gate. This change is the later product decision and supersedes only that marker requirement for a previously non-empty canonical home Feed.

## Goals / Non-Goals

**Goals:**

- Let a canonical home Feed that has shown real canonical posts reach `feed_exhausted` after all five structural samples remain stable.
- Treat near-bottom—remaining distance no greater than the actual scrolling container's viewport—as sufficient; do not require exact mathematical bottom or substitute the browser-window height for a smaller nested scroller.
- Keep the full 12.5-second schedule, no-early-success rule, cancellation, deadline, and structural invalidation behavior.
- Preserve Cloud ownership of the actual Reels transition.

**Non-Goals:**

- Do not make search or group near-bottom stability authorize the home-Feed Reels fallback.
- Do not change the separate confirmed-empty or present-unreportable ladders.
- Do not add a retry counter, fallback timer, protocol field, reason code, Cloud handler, or configurable threshold.
- Do not package or release an Edge installer as part of source implementation.

## Decisions

### 1. Five structural samples, not five localized marker samples, prove home-Feed exhaustion

The fixed sample offsets remain `0 / 5 / 7.5 / 10 / 12.5s`. A home confirmation is valid only while every sample:

- stays on the same URL and exact `document_time_origin_ms` document epoch and the same document generation, with `document_age_ms` never moving backward relative to the immediately preceding sample;
- stays on the canonical home list surface;
- is non-loading and near-bottom according to the actual feed scroll node's `scroll_viewport_height`;
- grows by no more than the existing 100px reflow noise floor relative to the initial sample (`>100px` invalidates); and
- exposes the same canonical card identity vector as the initial sample.

The fifth valid structural sample produces the confirmed exhaustion state. None of the first four samples may succeed.

Alternative rejected: require the scrollbar to reach exactly zero remaining distance. Facebook virtualized layouts can retain padding or a terminal card below the effective content boundary; exact bottom is less stable than the existing one-viewport near-bottom predicate.

### 2. `explicit_end` remains observable but is not a home exhaustion gate

The router continues to extract the bounded localized marker. It remains useful for diagnostics, settle-key changes, the existing initial-home-empty evidence, and unchanged non-home behavior. Home exhaustion classification no longer counts or resets on this field.

Alternative rejected: expand the marker vocabulary. Layout and localization variants make vocabulary maintenance an open-ended hard dependency; it cannot guarantee progress.

### 3. A non-empty-feed witness is required before structural exhaustion

The commanded list context must have begun on home, and the command must have observed at least one real canonical card on the same home URL and document time origin before it may return marker-free `feed_exhausted`. A search/group command that is redirected to home mid-command does not inherit this authorization. The witness is intentionally not bound to the earlier visible-card generation because Facebook virtualization may remove that card before the later stable near-bottom window. A structurally quiet zero-card home continues through the existing empty, loading, blocked, and present-unreportable evidence ladder.

Alternative rejected: classify any stable near-bottom zero-card page as exhausted. That would conflate a non-empty Feed reaching its end with first-screen empty, blocked, or unreportable states.

### 4. The receipt and Cloud transition remain unchanged

Edge continues to return the existing confirmed `action.completed{action:scroll,ok:false,reason:feed_exhausted}` receipt. Cloud remains the sole authority that sends `scroll{reason:empty_feed_reels_fallback}` and applies its session, quota, pacing, and idempotency gates.

No Cloud or external protocol change is required because only the evidence producing the existing receipt changes. The Native router adds bounded integer `documentTimeOriginMs` to its internal Feed probe so a same-URL reload cannot reuse the previous document's evidence.

### 5. The predecessor active artifact must not later restore the rejected gate

The conflicting five-of-five `explicit_end` clauses in `restore-native-facebook-residual-parity` must be synchronized to cite this later decision before integration. This avoids a future archive of that still-active change reintroducing the rejected marker requirement into the baseline specification.

## Risks / Trade-offs

- **A silent Facebook pagination failure can look structurally exhausted without exposing loading.** → Require five samples over 12.5 seconds, near-bottom throughout, no height growth above 100px, an unchanged ordered canonical identity vector, the same URL/document epoch/generation, and a prior same-document canonical-card witness. Reels navigation remains Cloud-authorized, session-bounded, and reversible.
- **A marker-free rule could pull search or group browsing into Reels.** → Require both a home command context and a canonical home confirmation surface; a mid-command redirect from search/group to home remains continuation unless existing explicit terminal evidence is complete.
- **Virtualization can remove or reorder old cards without adding content.** → Preserve the current conservative identity-vector equality check. Such movement invalidates confirmation and continues Feed rather than fabricating exhaustion.
- **Source integration does not update installed clients.** → Report source, package, and installed-runtime state separately; do not claim live acceptance until a later package is installed and observed.

## Migration Plan

1. Update the OpenSpec deltas and synchronize the predecessor active artifact.
2. Change the Native classifier and focused Rust tests in an isolated Edge worktree.
3. Run focused Feed tests, the full Native gate, Edge typecheck/contract tests as proportionate, and strict OpenSpec validation.
4. Rebase and fast-forward source changes to the default branches.
5. Package or release only under a separate explicit user instruction.

Rollback is a source revert of the Edge classifier commit; no data or protocol migration is involved.

## Open Questions

None.
