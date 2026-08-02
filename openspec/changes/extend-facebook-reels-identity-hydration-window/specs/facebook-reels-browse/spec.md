## MODIFIED Requirements

### Requirement: Configured Reels primary reuses the verified Reels entry path

When a Facebook session pins Reels as its primary surface, Cloud SHALL authorize entry with `page.scroll{reason:'facebook_reels_primary'}` and Edge SHALL route that command to the existing Reels entry executor. Route navigation alone MUST NOT count as entry success; after the Reels surface is reached, Edge SHALL allow up to 15 seconds for canonical Reel card hydration, and browsing SHALL begin only after Edge reports a canonical active Reel through `page.cards{listKind:'reels'}`.

#### Scenario: Configured primary reaches a reportable Reel

- **WHEN** Cloud authorizes `facebook_reels_primary` and Edge verifies one canonical active Reel within the 15-second post-surface hydration window
- **THEN** Edge reports that Reel through the existing Reels card contract
- **AND** the current persona, slow-start, rule, or consumption path continues without a parallel executor

#### Scenario: Reels route has no reportable card

- **WHEN** navigation reaches a Reels route but no canonical active Reel can be reported within the 15-second post-surface hydration window
- **THEN** Edge returns the existing honest pending, no-target, or ambiguous result
- **AND** neither Edge nor Cloud fabricates a Reel view or starts content evaluation
