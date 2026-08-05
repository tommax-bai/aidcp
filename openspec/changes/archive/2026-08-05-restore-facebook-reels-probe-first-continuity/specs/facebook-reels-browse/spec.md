## MODIFIED Requirements

### Requirement: Facebook Reels identifies exactly one active video card
Edge SHALL distinguish a keyboard-probeable Reels surface from a reportable or interactable Reel card. An exact `/reel/` or `/reels/` surface with explicit keyboard safety MAY receive one trusted navigation probe without a unique active video or canonical identity. Edge SHALL emit a Reel card or authorize an irreversible interaction only when it freshly resolves exactly one active video and binds that video to a canonical Facebook `/reel/<id>` identity. Missing or ambiguous active video, off-route observations, and identity-changing reads MUST fail closed for reporting and irreversible actions, but active-video structure MUST NOT veto reversible keyboard probing.

#### Scenario: Current Reel wins over preloaded neighbours for reporting
- **WHEN** previous, current, and next videos coexist in the DOM
- **THEN** Edge SHALL report only a uniquely resolved current video with canonical identity
- **AND** failure to make that selection SHALL emit no card without disabling an otherwise safe keyboard probe

#### Scenario: Anonymous or ambiguous landing remains probeable
- **WHEN** an exact `/reel/` surface is explicitly keyboard-safe but canonical identity or unique active-video structure is unavailable
- **THEN** Edge MAY dispatch its one trusted navigation key and SHALL emit no Reel card for the unresolved pre-state

#### Scenario: Route is not a Reel
- **WHEN** the current top-level route is home, login, checkpoint, another Facebook surface, or a non-Facebook URL
- **THEN** Edge SHALL report no Reel target and perform no Reels action

### Requirement: Configured Reels primary reuses the verified Reels entry path
When a Facebook session pins Reels as its primary surface, Cloud SHALL authorize entry with `page.scroll{reason:'facebook_reels_primary'}` and Edge SHALL route that command to the existing Reels entry executor. Edge SHALL first use bounded observation to report a canonical active Reel without input when available. If the observation ends on an exact keyboard-safe Reels surface without a reportable card, Edge SHALL continue the same command through the one-key probe boundary; active-video or axis recognition MUST NOT terminate entry before that probe. Route navigation or input delivery alone MUST NOT count as entry success.

#### Scenario: Configured primary reaches a reportable Reel without input
- **WHEN** Cloud authorizes `facebook_reels_primary` and bounded entry observation verifies one canonical active Reel
- **THEN** Edge SHALL report that Reel through the existing Reels card contract and perform no navigation input

#### Scenario: Reels route is safe but has no reportable card
- **WHEN** bounded entry observation reaches an exact keyboard-safe Reels route but cannot resolve one canonical active Reel
- **THEN** Edge SHALL dispatch exactly one preferred key through the shared navigation actuator
- **AND** it SHALL report a card only if bounded post-observation then verifies canonical progress

#### Scenario: Reels entry remains unresolved after the probe
- **WHEN** the one entry probe is delivered but no canonical active Reel appears within the bounded post-observation window
- **THEN** Edge SHALL return the existing honest ambiguous result and neither Edge nor Cloud SHALL fabricate a view or start content evaluation

## REMOVED Requirements

### Requirement: Facebook Reels advances through an axis-specific global next-card control
**Reason**: Global control labels, geometry, disabled state, occlusion, and competing-axis classification are unstable page structure and no longer authorize or implement Reels keyboard navigation.

**Migration**: Each admitted Reels scroll performs exactly one keyboard probe selected from non-blocking session preference; canonical post-observation proves progress, and control structure remains irrelevant to reversible navigation.
