## ADDED Requirements

### Requirement: Reels primary suppresses the Feed bootstrap before business processing

When a Facebook session pins Reels as its primary surface, Cloud SHALL intercept the initial Feed observation before card identity collection, content evaluation, interaction appraisal, mode-specific selection, or browse accounting. This rule SHALL apply whether the first Feed observation contains cards, confirms an empty Feed, or confirms present-but-unreportable cards.

#### Scenario: Non-empty Feed batch is not consumed

- **WHEN** the first reported list is `listKind:'feed'` with one or more cards and the pinned primary surface is Reels
- **THEN** Cloud authorizes configured Reels entry and returns before evaluating or counting those Feed cards

#### Scenario: Confirmed empty Feed enters configured Reels

- **WHEN** the first Feed observation is structurally confirmed empty and the pinned primary surface is Reels
- **THEN** Cloud authorizes configured Reels entry without waiting for Feed scrolling or exhaustion
- **AND** it preserves the empty observation as an observation rather than counting it as content

#### Scenario: Feed primary preserves existing fallback

- **WHEN** the pinned primary surface is Feed
- **THEN** existing Feed evaluation, empty/unreportable evidence, structural exhaustion, and evidence-based Reels fallback behavior remain unchanged
