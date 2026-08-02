## ADDED Requirements

### Requirement: Anonymous Reels entry receives one bounded local advance

For `facebook_reels_primary` and `empty_feed_reels_fallback`, Edge SHALL preserve one initial 15-second canonical-card hydration window after reaching a ready Reels surface. If that window expires, Edge SHALL invoke the existing bounded Native forward-navigation contract at most once only when fresh active and navigation readbacks bind one unique anonymous `videoKey` and both explicitly prove `inputSafe=true`. The invocation MAY use the existing bounded actuator-discovery order, but it MUST produce at most one active-video transition and MUST stop every later write as soon as any transition is observed. Pre-input same-video hydration MAY complete entry; completion after a transition SHALL require the bound moved-to `videoKey` and exactly one matching canonical-permalink Reel card. The anonymous landing, a content-derived card, input dispatch, or route arrival MUST NOT count as success or a view.

#### Scenario: First Reel hydrates before input commit

- **WHEN** the initially anonymous active video gains a matching canonical Reel card during the hydration window or fresh pre-commit readback
- **THEN** Edge reports that current canonical card and dispatches no keyboard, wheel, pointer, or second route navigation input

#### Scenario: Identity appears at the initial hydration boundary

- **WHEN** the same active video gains canonical identity as the initial 15-second window closes but its card is not yet reportable
- **THEN** Edge performs one immediate card read, dispatches no input, and does not open a second initial hydration window

#### Scenario: Anonymous horizontal landing advances

- **WHEN** the hydration window expires with one safe anonymous active video, fresh structure proves a horizontal layout, and the bounded invocation changes to a different canonically identified Reel
- **THEN** Edge reports exactly the moved-to canonical card, starts with the existing `ArrowRight` actuator, and dispatches no input after the transition

#### Scenario: Anonymous vertical landing advances

- **WHEN** the hydration window expires with one safe anonymous active video, fresh structure proves a vertical layout, and the bounded invocation changes to a different canonically identified Reel
- **THEN** Edge reports exactly the moved-to canonical card, starts with the existing `ArrowDown` actuator, and dispatches no input after the transition

#### Scenario: Original Reel hydrates after an ineffective actuator

- **WHEN** one entry actuator was dispatched, the active `videoKey` did not change, and that same video's exact canonical Reel card then becomes available
- **THEN** Edge reports the now-canonical current Reel and dispatches no second key, wheel, pointer, or route navigation input

#### Scenario: Anonymous entry target is unavailable

- **WHEN** fresh readback finds no active video, equally eligible videos, `inputSafe=false`, a missing input-safety signal, a blocker, target drift, or no remaining post-input verification budget
- **THEN** Edge dispatches no Reels navigation input and emits no fabricated card or view

#### Scenario: Entry is cancelled around the route boundary

- **WHEN** cancellation is observed immediately before the first `/reels/` route dispatch
- **THEN** Edge dispatches no route and reports `not_started`
- **AND WHEN** cancellation is observed after that route or before a retry route
- **THEN** Edge dispatches no later route or actuator and reports `ambiguous`

#### Scenario: Input leaves the anonymous Reel unchanged

- **WHEN** the one bounded navigation invocation exhausts its permitted methods without changing the active `videoKey`
- **THEN** Edge returns an ambiguous navigation-unconfirmed receipt and does not start a second entry invocation

#### Scenario: Video changes but canonical identity remains pending

- **WHEN** entry input changes the active `videoKey` but no matching canonical Reel card appears within the post-transition hydration window
- **THEN** Edge returns `ambiguous/reels_post_transition_identity_pending`, dispatches no later input, and retains a session-local read-only pending observation

#### Scenario: Later scroll encounters a pending entry transition

- **WHEN** another scroll command arrives while the prior entry transition still awaits canonical identity
- **THEN** Edge performs read-only active-card recovery and dispatches no keyboard, wheel, pointer, or route navigation input
- **AND** it clears the pending observation only after reporting one matching canonical Reel card or leaving the Reels surface

#### Scenario: Pending target drifts a second time

- **WHEN** a pending observation is already bound to one moved-to `videoKey` and either the same hydration window or a later command sees a different active video
- **THEN** Edge reports an ambiguous target-changed receipt, emits no card, and dispatches no input
- **AND** returning to the previously bound `videoKey` later cannot make that drifted observation confirm

#### Scenario: Ordinary Reels transition still awaits identity

- **WHEN** a normal Reels scroll proves one active-video transition but the moved-to video has no matching canonical card within its hydration window
- **THEN** Edge retains the exact moved-to video as a read-only pending observation and a later scroll MUST recover it before attempting another navigation
- **AND** if that video temporarily exposes the previous Reel's canonical ID, Edge MUST NOT report or count it until a distinct canonical Reel ID appears

#### Scenario: Noncanonical Reel card cannot complete entry

- **WHEN** Reels card extraction yields an invalid host or non-Reel URL, anonymous identity, `content_ref`, non-video card, non-ready batch, multiple cards, the previous Reel's stale canonical ID, or a card that does not match the freshly active canonical Reel
- **THEN** Edge does not confirm entry and Cloud receives no Reel view from that batch
