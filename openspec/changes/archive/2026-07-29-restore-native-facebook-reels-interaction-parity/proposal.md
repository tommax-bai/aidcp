## Why

The Facebook Native-only cutover regressed established Reel like and follow behavior: Cloud intents reach Edge, but the Native router fails before actuation because its generic CTA matching and active-root scoping do not cover real Reel controls. The same cutover also removed the bounded terminal diagnostics needed to distinguish target, control, and verification failures.

## What Changes

- Restore multilingual Facebook Reel like and follow CTA recognition from the established TypeScript behavior oracle without adding a JavaScript execution fallback.
- Resolve candidate controls against the uniquely active canonical Reel even when Facebook renders its action rail beside, rather than inside, the video/article root.
- Preserve trusted actuation, bounded attempts, and same-Reel selected-state confirmation; ambiguity, movement, or unproven state remain honest non-success outcomes.
- Emit bounded local diagnostics for each Native action receipt, including action, effect phase, and redacted reason, without logging page content or credentials.
- Add Native regression cases for real CTA variants, sibling action rails, ambiguity, movement, already-complete state, and unconfirmed writes.
- Keep Cloud probability, quota, pacing, protocol, and user-visible success semantics unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-note-scoped-targeting`: restore exact-target Reel like/follow resolution, trusted commit, same-Reel confirmation, and honest terminal evidence in the Native-only runtime.

## Impact

- Edge Native Page Engine embedded Facebook router, Rust command orchestration, TypeScript Native facade diagnostics, and focused Native tests.
- Control contract delta and implementation evidence.
- No protocol, Cloud policy, database, Console, installer, or OL deployment change.
- The pre-existing `facebook-reels-like-commit-reliability` live-account acceptance remains open and is not satisfied by source or local tests from this change.
