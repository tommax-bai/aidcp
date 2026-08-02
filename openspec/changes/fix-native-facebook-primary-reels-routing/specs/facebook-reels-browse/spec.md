## MODIFIED Requirements

### Requirement: Configured Reels primary reuses the verified Reels entry path

When a Facebook session pins Reels as its primary surface, Cloud SHALL authorize entry with `page.scroll{reason:'facebook_reels_primary'}` and every active Edge executor, including the shipped Native executor, SHALL route that exact reason to the existing Reels entry executor. The configured-primary reason SHALL remain distinct from `empty_feed_reels_fallback`, although both authorizations SHALL reuse the same navigation, readiness, canonical-card, and honest failure postconditions. Route navigation alone MUST NOT count as entry success; browsing SHALL begin only after Edge reports a canonical active Reel through `page.cards{listKind:'reels'}`.

#### Scenario: Configured primary reaches a reportable Reel

- **WHEN** Cloud authorizes `facebook_reels_primary` and the active Edge executor verifies one canonical active Reel
- **THEN** Edge reports that Reel through the existing Reels card contract
- **AND** the current persona, slow-start, rule, or consumption path continues without a parallel executor

#### Scenario: Shipped Native executor receives configured-primary authorization

- **WHEN** the shipped Native Facebook executor receives `page.scroll{reason:'facebook_reels_primary'}` while the current surface is Feed
- **THEN** it enters the same verified Reels navigation and hydration path used by the evidence-based fallback
- **AND** it MUST NOT execute the command as an ordinary Feed scroll

#### Scenario: Reels route has no reportable card

- **WHEN** navigation reaches a Reels route but no canonical active Reel can yet be reported
- **THEN** Edge returns the existing honest pending or no-target result
- **AND** neither Edge nor Cloud fabricates a Reel view or starts content evaluation

#### Scenario: Unrelated Feed scroll remains ordinary work

- **WHEN** the active executor receives `page.scroll` with a reason other than the configured-primary or evidence-based fallback authorization
- **THEN** it preserves the existing Feed or Reels continuation behavior for that reason
- **AND** it MUST NOT redirect the browser to Reels merely because the command is a page scroll
