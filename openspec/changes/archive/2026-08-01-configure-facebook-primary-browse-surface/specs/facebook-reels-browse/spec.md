## ADDED Requirements

### Requirement: Configured Reels primary reuses the verified Reels entry path

When a Facebook session pins Reels as its primary surface, Cloud SHALL authorize entry with `page.scroll{reason:'facebook_reels_primary'}` and Edge SHALL route that command to the existing Reels entry executor. Route navigation alone MUST NOT count as entry success; browsing SHALL begin only after Edge reports a canonical active Reel through `page.cards{listKind:'reels'}`.

#### Scenario: Configured primary reaches a reportable Reel

- **WHEN** Cloud authorizes `facebook_reels_primary` and Edge verifies one canonical active Reel
- **THEN** Edge reports that Reel through the existing Reels card contract
- **AND** the current persona, slow-start, rule, or consumption path continues without a parallel executor

#### Scenario: Reels route has no reportable card

- **WHEN** navigation reaches a Reels route but no canonical active Reel can yet be reported
- **THEN** Edge returns the existing honest pending or no-target result
- **AND** neither Edge nor Cloud fabricates a Reel view or starts content evaluation
