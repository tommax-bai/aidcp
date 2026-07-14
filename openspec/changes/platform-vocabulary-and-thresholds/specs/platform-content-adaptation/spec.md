## ADDED Requirements

### Requirement: Browse-loop prompts read platform vocabulary from the single comment profile

The browse-loop role prompts (content evaluation, quality curation, comment review, comment appraisal, comment-like appraisal, concept extraction, follow decision, comment compose) MUST source their site name, content noun, and metric nouns from the existing per-platform comment profile rather than hardcoding a specific platform's terms. There MUST NOT be a second lexicon table for the same facts, and roles MUST NOT branch on a platform literal or import the registry directly.

#### Scenario: Facebook prompts do not say Xiaohongshu

- **WHEN** a Facebook session runs content evaluation, quality curation, and comment compose
- **THEN** the prompts use the Facebook profile's site and content nouns
- **AND** no browse-loop prompt hardcodes 「小红书」 or 「收藏」 and no second lexicon exists

### Requirement: Deep-read heuristic is platform-aware

The deep-read image-versus-text heuristic MUST be platform-aware so a platform whose image posts commonly carry empty body text is not misjudged as a long-text post and under-reads its images.

#### Scenario: Facebook image post is not treated as long text

- **WHEN** a Facebook image post arrives with empty body content
- **THEN** the deep-read heuristic does not classify it as a long-text post
- **AND** it plans image browsing appropriate to an image-led post

### Requirement: Heat-velocity parsing is platform-aware

Published-time text parsing that feeds heat velocity MUST be parameterized per platform rather than assuming one platform's relative-time wording.

#### Scenario: Facebook published-time text is parsed by its own conventions

- **WHEN** heat velocity parses a Facebook post's published-time text
- **THEN** it uses Facebook's time-wording conventions
- **AND** it does not misparse it using another platform's wording

### Requirement: Captured post comments feed the browse-loop compose step

Post comments captured on a detail note MUST be carried into the cloud event model and made available to the browse-loop compose step, and the two Facebook compose paths MUST be unified into a shared draft helper with platform-specific callers that preserve the existing approval-versus-validators wrapping.

#### Scenario: Image post with no body still has comment context to compose from

- **WHEN** a Facebook image post has no body text but carries sampled post comments
- **THEN** the browse-loop compose step receives those comments as context
- **AND** the same shared draft helper serves both the browse-loop and targeted comment paths
