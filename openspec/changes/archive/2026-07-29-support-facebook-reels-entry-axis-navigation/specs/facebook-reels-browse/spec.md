## RENAMED Requirements

- FROM: `### Requirement: Facebook Reels advances through the global next-card control`
- TO: `### Requirement: Facebook Reels advances through an axis-specific global next-card control`

## MODIFIED Requirements

### Requirement: Facebook Reels identifies exactly one active video card

Edge SHALL distinguish a structurally targetable active video from a reportable Reel card. On `/reel/` or `/reels/`, Edge MAY resolve one unique visible video by greatest viewport intersection, using viewport-center distance only as a tie-breaker, and bind it to a session-local `videoKey` for navigation even when canonical identity is absent. Edge SHALL emit a Reel card only when that same active video is bound to a canonical Facebook `/reel/<id>` identity; the canonical Reel URL SHALL be the card and note identity. Missing or ambiguous active video, off-route observations, and identity-changing reads MUST fail closed and MUST NOT fabricate a card.

#### Scenario: Current Reel wins over preloaded neighbours
- **WHEN** previous, current, and next videos coexist in the DOM
- **THEN** Edge resolves only the video with the greatest current viewport intersection
- **AND** it reports that video only if a canonical current Reel identity is available

#### Scenario: Anonymous Reel landing is navigation-only
- **WHEN** `/reel/` exposes one unique active video but no canonical Reel id
- **THEN** Edge exposes its stable video observation only to the Native navigation actuator and emits no Reel card

#### Scenario: Route is not a Reel
- **WHEN** the current top-level route is home, login, checkpoint, another Facebook surface, or a non-Facebook URL
- **THEN** Edge reports no Reel target and performs no Reels action

### Requirement: Facebook Reels advances through an axis-specific global next-card control

For `page.scroll` while in the authorized Reels list mode, Edge SHALL classify the current global navigation controls as one unambiguous vertical or horizontal rail relative to the active video. Vertical navigation MAY use its lower global next control after the vertical key and wheel fallbacks; horizontal navigation MAY use its right global next control after the horizontal key fallback. Edge MUST NOT use an in-video media control or a control from another axis. Success SHALL require the applicable canonical Reel URL plus active-video transition rule and the new active card to pass the same identity and summary probe before reporting. Disabled, missing, ambiguous, stale, or axis-drifting controls and unchanged identity MUST fail honestly.

#### Scenario: Vertical next control changes active Reel
- **WHEN** the unique enabled lower control in a proven vertical rail is clicked and a new canonical active Reel is proven
- **THEN** Edge reports exactly the new Reel card and marks it seen through the existing canonical deduplication path

#### Scenario: Horizontal next control changes active Reel
- **WHEN** the unique enabled right control in a proven horizontal rail is clicked and a new canonical active Reel is proven
- **THEN** Edge reports exactly the new Reel card and marks it seen through the existing canonical deduplication path

#### Scenario: Wheel does not count as navigation
- **WHEN** vertical wheel input leaves route and active-video identity unchanged
- **THEN** Edge MUST NOT claim a new card or a successful scroll

#### Scenario: In-video control is not used as next Reel
- **WHEN** a bottom media or attachment control exists inside the active video
- **THEN** Edge ignores it and considers only the unique global control belonging to the proven navigation rail

#### Scenario: Generic single next control has no axis proof
- **WHEN** only one generic next-labelled control is visible and neither a structural pair nor directional semantics proves its axis
- **THEN** Edge clicks nothing and emits no fabricated progress
