## MODIFIED Requirements

### Requirement: Native Facebook Reels scrolling uses a surface-specific trusted actuator
When the Native-only Facebook runtime receives `page.scroll` on Reels, Edge SHALL freshly resolve one unique active video and one structural navigation axis, then dispatch exactly one trusted CDP key: ArrowDown for vertical or ArrowRight for horizontal. It MUST NOT serialize or compare `videoKey`, dispatch a wheel or next-control click, try both axes, or retain navigation transition state after the command. A missing or ambiguous target, unresolved axis, unsafe keyboard context, cancellation, or deadline SHALL terminate honestly without another write.

#### Scenario: Anonymous landing Reel advances vertically
- **WHEN** `/reel/` has one active video without canonical `noteId`, a vertical axis is uniquely resolved, and one ArrowDown leads to a canonical active Reel
- **THEN** Edge SHALL report that Reel and SHALL dispatch no other input

#### Scenario: Identified Reel advances horizontally
- **WHEN** an identified active Reel has a uniquely resolved horizontal axis and one ArrowRight leads to a different canonical active Reel
- **THEN** Edge SHALL report the new Reel and SHALL dispatch no other input

#### Scenario: Unsafe or unresolved navigation dispatches nothing
- **WHEN** the active target is ambiguous, keyboard context is unsafe, or the structural axis is not unique
- **THEN** Edge SHALL return one pre-dispatch failure and SHALL emit no keyboard, wheel, or pointer input

### Requirement: Reels progress requires stable identity change
Edge SHALL use canonical `noteId` as the only reportable Reel identity. A Reel card or interaction target requires an exact canonical Facebook Reel URL freshly associated with the unique active video. For an anonymous pre-state, navigation success requires a canonical post-state `noteId`; for an identified pre-state, success requires a different canonical post-state `noteId`. Document scroll, input delivery, coordinates, media URLs or segments, and DOM element replacement MUST NOT independently prove progress.

#### Scenario: Anonymous active video is targetable but not reportable
- **WHEN** `/reel/` has one unique active video but no canonical Reel identity
- **THEN** Edge MAY target the one command's trusted input using fresh geometry but MUST NOT emit a card, count a view, or authorize an interaction for that pre-state

#### Scenario: Media implementation changes without canonical change
- **WHEN** the video source, media segment, poster, or DOM element changes but canonical `noteId` remains absent or unchanged
- **THEN** Edge SHALL NOT report a new Reel

#### Scenario: Canonical active identity changes
- **WHEN** the freshly observed post-state satisfies the applicable anonymous or identified canonical transition rule
- **THEN** Edge SHALL report one fresh Reels card batch derived from that active Reel

#### Scenario: Route identity has no matching permalink-bearing article
- **WHEN** a `/reel/<id>` page has one active video whose bounded container contains only repeated `/reel/hashtag/` navigation links and no current-Reel permalink
- **THEN** Edge SHALL bind the exact canonical route `noteId` to that active video, exclude discovery routes, and report exactly one current Reels card

### Requirement: Reels no-change terminates honestly
If Reels has no unique active video, safe input context, or unambiguous navigation axis, Edge SHALL fail before input with `effectPhase:not_started` and emit no normal `page.cards`. If its one trusted input was dispatched but no eligible canonical post-state appears within the bounded observation window, Edge SHALL emit one failed scroll receipt with an ambiguous effect phase and no cards. Either result SHALL clear command-local navigation state and MUST NOT disable a later scroll command.

#### Scenario: Active Reel or axis is unavailable
- **WHEN** the fresh pre-write probe cannot resolve one safe active video and one axis
- **THEN** Edge SHALL emit `reels_target_unavailable` before input and no fabricated cards

#### Scenario: Canonical identity remains unchanged
- **WHEN** the one trusted input is dispatched and the canonical active `noteId` remains unchanged through the bounded window
- **THEN** Edge SHALL emit `reels_navigation_unconfirmed` with ambiguous effect and no cards

#### Scenario: Canonical identity remains absent
- **WHEN** the one trusted input is dispatched and no canonical active `noteId` appears through the bounded window
- **THEN** Edge SHALL emit `reels_identity_unresolved` with ambiguous effect and no cards

#### Scenario: Later command remains independent
- **WHEN** Cloud sends another scroll after any terminal Reels failure
- **THEN** Edge SHALL evaluate and execute it from a fresh probe without a saved transition latch
