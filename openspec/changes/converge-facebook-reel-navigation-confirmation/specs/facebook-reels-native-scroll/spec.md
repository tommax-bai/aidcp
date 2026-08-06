## MODIFIED Requirements

### Requirement: Reels progress requires stable identity change
Edge SHALL use canonical `noteId` as the only reportable Reel identity. A Reel card or interaction target requires an exact canonical Facebook Reel URL freshly associated with one active video, but that association SHALL be a reporting or irreversible-target postcondition rather than a reversible keyboard precondition. For an anonymous pre-state, navigation success requires a canonical post-state `noteId`; for an identified pre-state, success requires a different canonical post-state `noteId`. Document scroll, input delivery, coordinates, control state, media URLs or segments, DOM replacement, and keyboard preference MUST NOT independently prove progress.

The post-actuation confirmation predicate SHALL consist only of: the observation is a card batch, its list kind is `reels`, the card identity and the probe identity each parse as a canonical Reel URL, and — when movement is required — the probe identity differs from the pre-state identity. List readiness state, card count, a separate probe success flag, video-element typing, and identity-kind allowlists MUST NOT be admitted as additional conditions, because each either restates one of the four or rejects page states that satisfy them. The card identity and the probe identity MUST NOT be required to be equal: both are derived from the same active-Reel reader within one command, so equality asserts nothing about agreement between independent sources and rejects samples taken while the surface is still settling.

Where the confirmation reads a card out of the batch it SHALL do so through a checked access that treats an absent card as unconfirmed. An empty batch SHALL NOT be able to abort the command.

#### Scenario: Anonymous surface is probeable but not reportable
- **WHEN** `/reel/` is keyboard-safe but no unique canonical active Reel can be resolved before input
- **THEN** Edge MAY dispatch the one trusted probe but MUST NOT emit a pre-state card, count a view, or authorize an interaction

#### Scenario: Canonical active identity appears after input
- **WHEN** bounded post-observation resolves one canonical active Reel satisfying the anonymous or identified transition rule
- **THEN** Edge SHALL report one fresh Reels card batch for that canonical post-state

#### Scenario: Implementation structure changes without canonical progress
- **WHEN** video selection, controls, coordinates, media segments, or DOM elements change while canonical `noteId` is absent or unchanged
- **THEN** Edge SHALL NOT report a new Reel or count a view

#### Scenario: Route identity has no matching permalink-bearing article
- **WHEN** a `/reel/<id>` page has one active video whose bounded container contains only repeated `/reel/hashtag/` navigation links and no current-Reel permalink
- **THEN** Edge SHALL bind the exact canonical route `noteId` to that active video, exclude discovery routes, and report exactly one current Reels card

#### Scenario: Settling surface does not defeat a real transition
- **WHEN** the card identity and the probe identity are read one CDP round trip apart during the same command and resolve to different canonical Reels, while the probe identity differs from the pre-state identity
- **THEN** Edge SHALL confirm the transition on the probe identity and MUST NOT reject the sample for the two identities being unequal

#### Scenario: Structural observations do not veto a confirmed transition
- **WHEN** bounded post-observation resolves a canonical post-state `noteId` different from the pre-state while list readiness, card count, probe success flag, video typing, or identity kind would not satisfy their former checks
- **THEN** Edge SHALL confirm the transition and report the post-state Reel

#### Scenario: Empty card batch is unconfirmed, not fatal
- **WHEN** the card batch carries no card at a sampling point
- **THEN** Edge SHALL treat that sample as unconfirmed and continue bounded observation without aborting the command

### Requirement: Reels no-change terminates honestly
If stable surface, keyboard-safety, cancellation, or deadline admission fails, Edge SHALL terminate before keyboard input and emit no cards. An ordinary scroll with no earlier write SHALL report `effectPhase:not_started`; a Reels-entry command that already dispatched route navigation SHALL retain an honest ambiguous phase. If its one trusted key was delivered but no eligible canonical post-state appears within bounded observation, Edge SHALL emit one failed scroll receipt with an ambiguous effect phase and no cards. The result SHALL update only the non-blocking key preference after actual keyboard input and MUST NOT create a pending latch, disable a later command, or trigger another write in the same command.

When bounded observation ends without confirmation, Edge SHALL read the canonical identity it is standing on once and SHALL carry that identity on the emitted receipt. `reels_navigation_unconfirmed` SHALL be reserved for the case where that identity resolves, and `reels_identity_unresolved` for the case where it does not. Carrying the identity SHALL NOT emit a card and SHALL NOT count a view; it exists so that a consumer can distinguish a Reel that did not advance from a Reel that could not be read, without re-deriving either fact.

#### Scenario: Canonical identity remains unchanged
- **WHEN** the one trusted key is delivered and the canonical active `noteId` remains unchanged through bounded observation
- **THEN** Edge SHALL emit `reels_navigation_unconfirmed` with ambiguous effect, emit no card, and prefer the other key for the next admitted command
- **AND** the receipt SHALL carry that unchanged canonical identity

#### Scenario: Canonical identity remains absent
- **WHEN** the one trusted key is delivered and no canonical active `noteId` appears through bounded observation
- **THEN** Edge SHALL emit `reels_identity_unresolved` with ambiguous effect, emit no card, and dispatch no further input in that command
- **AND** the receipt SHALL carry no identity

#### Scenario: Unsafe context fails before input
- **WHEN** a fresh explicit keyboard-safety or lifecycle gate fails
- **THEN** Edge SHALL perform zero keyboard input and leave the key preference unchanged
- **AND** its effect phase SHALL remain not-started unless Reels entry already dispatched route navigation

#### Scenario: Later command is never latched off
- **WHEN** Cloud sends another scroll after any terminal Reels outcome
- **THEN** Edge SHALL evaluate it from fresh stable safety facts and SHALL NOT consult active-video, axis, or pending-transition state as an eligibility gate
