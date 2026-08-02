## ADDED Requirements

### Requirement: Anonymous Reels entry receives one bounded local advance

For `facebook_reels_primary` and `empty_feed_reels_fallback`, Edge SHALL preserve the initial 15-second canonical-card hydration window after reaching a ready Reels surface. If that window expires, Edge SHALL invoke the existing bounded Native forward-navigation contract at most once only when fresh readback proves one unique, input-safe active `videoKey` with no canonical identity. The invocation MAY use the existing bounded actuator-discovery order, but it MUST produce at most one active-video transition and MUST stop every later write as soon as any transition is observed. Entry success SHALL require a distinct moved-to `videoKey` and exactly one matching canonical-permalink Reel card. The anonymous landing, a content-derived card, input dispatch, or route arrival MUST NOT count as success or a view.

#### Scenario: First Reel hydrates before input commit

- **WHEN** the initially anonymous active video gains a matching canonical Reel card during the hydration window or fresh pre-commit readback
- **THEN** Edge reports that current canonical card and dispatches no keyboard, wheel, pointer, or second route navigation input

#### Scenario: Anonymous horizontal landing advances

- **WHEN** the hydration window expires with one safe anonymous active video, fresh structure proves a horizontal layout, and the bounded invocation changes to a different canonically identified Reel
- **THEN** Edge reports exactly the moved-to canonical card, starts with the existing `ArrowRight` actuator, and dispatches no input after the transition

#### Scenario: Anonymous vertical landing advances

- **WHEN** the hydration window expires with one safe anonymous active video, fresh structure proves a vertical layout, and the bounded invocation changes to a different canonically identified Reel
- **THEN** Edge reports exactly the moved-to canonical card, starts with the existing `ArrowDown` actuator, and dispatches no input after the transition

#### Scenario: Anonymous entry target is unavailable

- **WHEN** fresh readback finds no active video, equally eligible videos, unsafe input focus, a blocker, target drift, or no remaining post-input verification budget
- **THEN** Edge dispatches no Reels navigation input and emits no fabricated card or view

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

#### Scenario: Noncanonical Reel card cannot complete entry

- **WHEN** Reels card extraction yields an anonymous identity, a `content_ref`, multiple cards, or a card that does not match the freshly active canonical Reel
- **THEN** Edge does not confirm entry and Cloud receives no Reel view from that batch
