## Why

Facebook Reels navigation currently treats a session-local `videoKey` as durable content identity. Normal media/DOM replacement can therefore be mistaken for an extra transition, latch the Native session into read-only recovery, and leave Cloud waiting for the generic idle watchdog even though the browser is still usable.

## What Changes

- **BREAKING** Remove `videoKey` from the maintained Facebook Reels probe, Native session state, movement decisions, interaction targeting, and verification.
- Make canonical `noteId` the only reportable Reel identity. A scroll command performs one freshly resolved trusted forward actuation, observes its post-state once within a bounded window, and then terminates without retaining a cross-command transition latch.
- Keep scrolling available after missing, unchanged, or unresolved canonical identity: Edge reports the honest terminal result and Cloud issues a bounded, normally paced continuation instead of waiting for the idle watchdog.
- Use the same first canonical one-card Reel presentation as the single fact for view risk accounting and mode cadence. A presentation without canonical `noteId` produces neither view accounting nor a like/follow opportunity, but it does not stop later scrolling.
- Resolve every Reel like or follow target freshly from the command's canonical `noteId`; do not reuse navigation identity or saved DOM state.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-reels-navigation`: replace active-video identity ladders and transition suppression with one fresh, note-scoped post-navigation observation and no cross-command latch.
- `facebook-reels-native-scroll`: remove the `videoKey` contract and define one trusted forward actuation per scroll command with canonical `noteId` as the only reportable result.
- `browse-loop-resilience`: recover promptly from terminal Reels scroll outcomes by scheduling the next normally admitted scroll rather than waiting for the generic idle watchdog.

## Impact

- Edge Native Facebook router payloads, Rust decoding/session state, Reels scroll execution, Reel like/follow target verification, and focused Native tests.
- Cloud Facebook cards ingestion, Reel cadence input, failed-scroll recovery, and focused orchestration/risk tests.
- No protocol-v2 field changes outside the Native Facebook page-engine boundary, no new policy knobs, no anonymous view accounting, no interaction debt, and no Edge packaging in this change.
