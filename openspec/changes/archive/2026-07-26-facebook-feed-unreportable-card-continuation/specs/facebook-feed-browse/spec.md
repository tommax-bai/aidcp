## ADDED Requirements

### Requirement: Lightweight Facebook video cards preserve exact-card identity safety

A lightweight Facebook card containing video content SHALL be reportable and actionable only when the shared scanner/target resolver finds a canonical video-post link inside that exact card, using an already accepted `watch?v`, `videos/<id>`, or `reel/<id>` shape. A `<video>` element, CDN media URL, photo/video resource id, `/` timestamp anchor, opaque timestamp text, author, or content text MUST NOT be promoted to post identity.

If the current video card has no trustworthy identity, the Edge MUST classify it as structurally present but unreportable, skip it, and continue the bounded feed path. It MUST NOT substitute an identity from a neighboring card or stop the initial browse loop merely because the unreportable video occupies the first viewport.

#### Scenario: Exact-card watch link makes a lightweight video reportable
- **WHEN** a lightweight video card contains a `watch?v=<video-post-id>` link inside its own structural card boundary
- **THEN** the scanner reports that exact card with the canonical video-post identity and later target resolution finds the same card

#### Scenario: Media-only Vietnamese first video card is skipped
- **WHEN** a visible lightweight video card contains readable Vietnamese text but exposes only a `/` timestamp anchor, media resource URLs, and no accepted post-shaped link
- **THEN** the Edge does not derive identity from the text or media, skips the card, and continues downward within the existing bounded scroll policy

#### Scenario: Neighboring canonical link cannot identify the video card
- **WHEN** an unreportable video card is adjacent to another card that contains a canonical permalink
- **THEN** the video card remains unreportable and all reads/actions stay scoped to the neighboring card only when that neighboring card is separately reported
