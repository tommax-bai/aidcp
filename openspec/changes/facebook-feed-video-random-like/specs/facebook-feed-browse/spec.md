## ADDED Requirements

### Requirement: Strict lightweight Feed videos are reportable only when actually presented

The Facebook Feed scanner SHALL merge semantic top-level posts with lightweight video-card roots found inside the same Feed container. A lightweight video root SHALL be reportable only when it contains exactly one numeric `data-video-id`, exactly one video, publisher or story-message evidence, and one post-level like/comment action boundary. Its video MUST have meaningful horizontal intersection and at least 35% vertical intersection with the primary viewport. If multiple strict videos satisfy the viewport threshold in one scan, Edge SHALL report only the one whose video center is closest to the viewport center and SHALL leave the others eligible for a later scan. Existing non-video card reporting MUST remain unchanged.

#### Scenario: Lightweight video inside a semantic Feed is reported
- **WHEN** a Feed contains a non-article video root with one video id, one video, author/caption evidence, one action boundary, and at least 35% viewport intersection
- **THEN** Edge reports it as one `isVideo:true` card with its extracted author and caption

#### Scenario: Off-screen mounted video is deferred
- **WHEN** a strict video card exists in the DOM but has less than 35% vertical viewport intersection
- **THEN** Edge does not report it in the current batch and does not mark its identity seen, allowing a later scroll to present it

#### Scenario: Multiple visible videos yield one primary presentation
- **WHEN** two strict video cards satisfy the viewport threshold in a large viewport
- **THEN** Edge reports only the center-nearest video in that scan and defers the other

#### Scenario: Embedded Reels rail is not a Feed video card
- **WHEN** an embedded Reels rail mounts multiple videos without one strict video id and one local post action boundary
- **THEN** Edge excludes it from ordinary-Feed video reporting and MUST NOT attribute it to an adjacent post by ancestor order

#### Scenario: Ambiguous lightweight card continues browsing
- **WHEN** a candidate contains multiple ids/videos, lacks publisher/caption/action witnesses, or has mismatched explicit and data-derived identities
- **THEN** Edge reports no synthetic card for it, performs no action on it, and retains the existing bounded continuation behavior
