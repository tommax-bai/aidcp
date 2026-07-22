## ADDED Requirements

### Requirement: Facebook Feed-video presentations appear exactly once in the activity stream

When Edge reports an ordinary Facebook Feed batch containing exactly one `isVideo:true` card with a canonical non-Reel Facebook post identity, the client SHALL add exactly one “读” activity for that presented video. The activity SHALL use truthful “看了” wording with the reported caption and author when present, MUST use a bounded generic fallback when metadata is absent, and MUST NOT expose a URL, noteId, or other machine identifier. The event MAY add one immediate local fallback view, but Cloud customer-auth `dailyUsage` SHALL remain the authoritative total.

The client MUST deduplicate the activity by canonical post identity for the active session. A repeated cards batch or later detail report for an already-projected Feed video SHALL continue through the existing Cloud data path but MUST NOT add another read activity or local fallback view. Non-video, empty, multi-video, malformed-identity, and Reel-shaped Feed batches MUST NOT produce this activity.

#### Scenario: Strict Feed video produces one readable activity

- **WHEN** Edge reports one ordinary Feed video with a canonical post identity, caption, and author
- **THEN** “今天做了这些” adds one “读” activity using the actual caption and author
- **AND** the local fallback view increases once until Cloud refreshes the authoritative total

#### Scenario: Missing metadata uses a safe generic fallback

- **WHEN** an otherwise valid Feed-video presentation lacks caption and author metadata
- **THEN** the activity uses bounded generic “看了一个视频” wording
- **AND** it exposes no URL, post id, or other machine identifier

#### Scenario: Duplicate presentation and later detail remain idempotent

- **WHEN** the same canonical Feed video is reported again or later produces `note.detail` in the same active session
- **THEN** the Cloud cards/detail data continues through its existing path
- **AND** the client adds no second read activity and no second local fallback view

#### Scenario: Unqualified Feed batches remain silent

- **WHEN** a Feed batch has zero or multiple video cards, lacks a canonical post identity, is non-video, or carries a Reel-shaped identity
- **THEN** the client emits no Feed-video read activity and adds no local fallback view

#### Scenario: Feed video uses the existing read marker

- **WHEN** a `feed_video_view` activity reaches the renderer
- **THEN** the activity stream displays the existing “读” marker rather than a generic system marker
