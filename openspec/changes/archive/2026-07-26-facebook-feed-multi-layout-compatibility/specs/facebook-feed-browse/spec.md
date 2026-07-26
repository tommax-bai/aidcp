## ADDED Requirements

### Requirement: Facebook feed card targeting supports both observed layouts with one identity boundary

The Facebook feed reader and every in-feed target resolver SHALL share one locale-neutral top-level card abstraction that supports both the semantic `[role="feed"]` / `[role="article"]` layout and the lightweight story-message div layout. A lightweight card SHALL be bounded to the smallest visible structural container that contains its message and at least one linked author heading, and target-scoped reads, observations, and actions MUST remain inside that resolved card.

A discovered card MUST NOT become a reportable or actionable target unless the existing canonical-post identity parser accepts a post-shaped link inside that exact card. Photo/video resource identifiers or obfuscated timestamp links that do not satisfy that parser MUST NOT be promoted to post identity. When no reliable card target exists, the edge SHALL continue the existing bounded browse path and return an honest no-target/exhausted outcome rather than searching a neighboring card or claiming success.

#### Scenario: Semantic feed card remains resolvable
- **WHEN** a reported target came from a top-level semantic article inside `[role="feed"]`
- **THEN** the later in-feed reader and action resolver locate that exact article by canonical post id and keep all observation/action scope inside it

#### Scenario: Lightweight feed card is reported and resolved by the same rule
- **WHEN** a lightweight story-message card contains at least one linked author heading and a whitelisted canonical post link
- **THEN** the initial scanner can report it and a later in-feed reader can resolve the same exact card by the same canonical post id without leaving the feed

#### Scenario: Ambiguous media-only lightweight card fails closed
- **WHEN** a lightweight card exposes only photo/video resource identifiers or a non-canonical obfuscated timestamp link
- **THEN** the edge does not report or act on that card and MUST NOT substitute a neighboring card or fabricate a post identity

#### Scenario: Layout detection does not depend on writing language
- **WHEN** two accounts receive different UI languages but one of the two supported structural layouts
- **THEN** the same structural detector recognizes their cards without matching localized author, timestamp, menu, or expand-control text for layout classification
