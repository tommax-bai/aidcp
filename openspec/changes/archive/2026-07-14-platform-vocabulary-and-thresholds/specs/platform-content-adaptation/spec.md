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

### Requirement: Captured post comments feed the browse-loop compose step

Post comments captured on a detail note MUST be carried into the cloud event model and made available to the browse-loop compose step, so a platform whose image posts commonly lack body text still has comment context to write from. On a platform whose detail payload does not itself carry comments, the on-page comment samples gathered while scrolling the comment section MUST be attached to the current note so the same compose step can use them.

#### Scenario: Image post with no body still has comment context to compose from

- **WHEN** a Facebook image post has no body text but carries sampled post comments
- **THEN** the browse-loop compose step receives those comments as context
- **AND** the compose prompt renders the existing-comments block rather than composing from an empty body

### Requirement: Compose language follows the content's language per platform

On a platform whose content is commonly written in a local language other than the account's default writing language, the browse-loop compose step MUST instruct the model to write in the language of the post body and existing comments, sourced from the single per-platform comment profile (no second table). A platform without such a declaration MUST render no language rule, leaving its prompt unchanged.

#### Scenario: Facebook comment follows the post's language

- **WHEN** the browse-loop compose step runs for a Facebook post written in a local language
- **THEN** the prompt carries the platform profile's language rule (write in the content's language)
- **AND** a Xiaohongshu compose prompt renders no such rule and is byte-unchanged
