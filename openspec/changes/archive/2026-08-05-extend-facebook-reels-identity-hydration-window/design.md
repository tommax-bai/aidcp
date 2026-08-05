## Context

The shared Native Facebook Reels completion helper starts only after Edge has either reached a Reels surface or observed an active-video transition. It currently polls `reel_cards` for five seconds and returns `ambiguous/reels_identity_unresolved` or `ambiguous/reels_navigation_unconfirmed` when no canonical card appears. A real account reached the surface within the command deadline but hydrated its canonical card after that five-second window; a later read-only probe found the card ready.

The completed `stabilize-facebook-reels-entry-and-navigation` change remains the prerequisite for exact-target entry and input suppression. This change does not edit that prerequisite or alter its navigation authority.

## Goals / Non-Goals

**Goals:**

- Give both Reels entry and post-transition canonical-card hydration up to 15 seconds.
- Preserve the existing timer start point, polling interval, success proof, terminal reasons, and no-further-input rule.
- Add focused regression evidence that the shared deadline is 15 seconds rather than 5 seconds.

**Non-Goals:**

- Add Cloud retries, protocol fields, navigation recovery, or another browser input.
- Treat route arrival, video visibility, or elapsed time as a successful Reel view.
- Package, install, or deploy the desktop client.

## Decisions

### Change the shared hydration deadline only

Replace the inline five-second duration in `finish_facebook_reel_transition` with a named 15-second constant. The helper is shared by successful Reels entry and an observed active-video transition, so one change keeps both paths consistent. The timer still starts only when this helper is entered; navigation/readiness and movement detection remain outside the 15-second window.

Alternative considered: add a second retry command. Rejected because a post-transition retry could dispatch another input and skip a Reel whose first transition already occurred.

### Keep fail-closed receipts unchanged

When the 15-second window expires, Edge retains the existing `ambiguous` phase and reason selection. No empty `page.cards`, fabricated view, or extra input is emitted.

Alternative considered: convert late hydration to `reels_pending`. Rejected because that would broaden Cloud control flow beyond the user's requested timeout adjustment.

### Verify the configured window and its outer budget

Expose the duration as a constant and cover it with a Rust unit assertion alongside the existing Fake CDP behavior test. The unhydrated-entry test SHALL retain an outer command budget larger than the 15-second inner hydration window so it proves the typed ambiguous receipt rather than an unrelated atomic timeout. That behavior test intentionally waits through the full configured window.

## Risks / Trade-offs

- [A genuinely unresolvable Reel holds the command ten seconds longer] → Keep the deadline bounded at 15 seconds and preserve the same terminal receipt.
- [A longer command approaches an outer watchdog] → The Native Facebook command ceiling remains larger than the navigation/readiness plus 15-second hydration path; focused timing coverage will guard the configured duration.
- [A later card is counted without proof] → Continue requiring one non-empty canonical `page.cards` result before success.

## Migration Plan

Implement and validate in an isolated `aidcp-edge` worktree, integrate source and OpenSpec evidence, and do not package or replace the installed client. Rollback is a source revert from the named 15-second constant to five seconds; there is no data or protocol migration.

## Open Questions

None.
