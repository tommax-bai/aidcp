## Why

A real Facebook Reels-primary entry can reach `/reels/` with one safe active video but no canonical `/reel/<id>` after the existing 15-second hydration window. Edge currently terminates that entry as `reels_identity_unresolved`, while a generic idle scroll about four minutes later advances the same anonymous landing and begins confirmed Reels browsing, leaving a systematic first-entry stall.

## What Changes

- Preserve the existing 15-second canonical-card hydration window for a reached Reels surface.
- When that window expires, allow only one fresh, input-safe, uniquely identified anonymous active video to invoke the existing bounded Native Reels forward-navigation contract once inside the same entry command.
- Preserve horizontal and vertical actuator selection, fresh same-video checks, late-movement suppression, and the rule that any observed `videoKey` transition forbids later input.
- Confirm entry after actuator dispatch only when either the unchanged original `videoKey` has since hydrated to one exact canonical `/reel/<id>` card, or the moved-to video has a distinct `videoKey` and one exact canonical card; never emit or count an anonymous landing as a Reel view.
- Keep any moved-to Reel with unresolved identity in a session-local read-only observation, including ordinary browsing transitions, and reject a remounted video that still exposes the previous Reel ID.
- Keep missing, ambiguous, unsafe, unchanged, or moved-but-unidentified outcomes honest and bounded, with no second entry navigation, Cloud retry, or fabricated card.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-reels-browse`: connect a uniquely targetable anonymous Reels landing to one bounded local forward-navigation invocation before entry terminates.

## Impact

- Owning repo: `aidcp-edge` Native Facebook Reels entry orchestration and focused Fake CDP/Rust regression coverage.
- Control repo: OpenSpec behavior delta and validation evidence.
- No Cloud, Console, protocol, database, policy, pacing, package, installation, deployment, or real-account action change.
