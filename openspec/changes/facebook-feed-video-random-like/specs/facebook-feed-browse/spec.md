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

### Requirement: Bounded present-but-unreportable Feed transitions to Reels through Cloud authorization

When a confirmed Facebook home Feed contains physical card evidence but eight bounded continuation rounds yield no reportable card, Edge SHALL report a distinct present-but-unreportable Feed list state. Edge MUST NOT report that observation as an empty Feed, MUST NOT claim `feed_exhausted`, and MUST NOT emit an uncommanded action receipt. Cloud SHALL deduplicate the observation for the active startup/document generation and authorize one Reels transition. Edge SHALL enter Reels only after that authorization and a fresh surface/blocker check. Loading, login, consent, checkpoint, unknown, non-home, or physically cardless pages MUST NOT use this fallback.

#### Scenario: Eight unreportable rounds request one Reels transition
- **WHEN** the active Facebook home page still contains physical Feed cards but all eight continuation rounds yield no trustworthy card identity
- **THEN** Edge reports the present-but-unreportable list state, Cloud sends one Reels-fallback authorization, and Edge transitions to the dedicated Reels surface

#### Scenario: A reportable card before round eight keeps the Feed active
- **WHEN** any continuation round produces a trustworthy Feed card
- **THEN** Edge reports that card through the normal Feed path and does not request the unreportable Reels fallback

#### Scenario: Loading or blocked pages never use the unreportable fallback
- **WHEN** the final probe is loading, login-like, consent-blocked, checkpoint-like, unknown, non-home, or lacks physical card evidence
- **THEN** Edge fails closed with the truthful existing state and neither Edge nor Cloud transitions to Reels from the unreportable path

#### Scenario: Repeated observation is idempotent
- **WHEN** the same startup/document generation repeats the present-but-unreportable observation
- **THEN** Cloud emits at most one Reels-fallback authorization for that generation
