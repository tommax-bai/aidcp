## ADDED Requirements

### Requirement: Comment create uses the platform-confirmed capture shape

The WeChat Channels comment-create descriptor SHALL be backed by a sanitized, platform-confirmed authorized-session capture. It SHALL fix POST method, create-comment path, `_aid`/`_rid`/`_pageUrl` query names, required non-secret header names, interaction-comment referer, JSON body keys and value types, authenticated cookie-jar use, non-retry-safe classification, and acknowledgement parsing without embedding captured secret or personal values. The uncaptured direct-message descriptor MUST retain its candidate evidence label and existing development-only boundary.

#### Scenario: Edge serializes an approved comment reply

- **WHEN** Edge has the synchronized target-comment context and serializes an approved top-level comment reply
- **THEN** the request exactly matches the sanitized fixture structure, includes a fresh UUID client ID and bounded target-comment snapshot, and contains no captured cookie, token, finder ID, comment ID, profile value, or message content
- **AND** the descriptor remains `retrySafe=false`

#### Scenario: Direct-message evidence is unchanged

- **WHEN** this change promotes the comment-create descriptor
- **THEN** the direct-message descriptor remains non-capture-backed and unavailable outside its existing exact development override

### Requirement: Comment write context remains local and bounded

Edge SHALL retain only the explicitly observed target-comment fields required by comment-create in account/environment-scoped local state. Edge MUST NOT add the context to the Cloud protocol, interaction message projection, or arbitrary raw metadata. Nested reply arrays SHALL be normalized to an empty array so persisted and dispatched context is bounded.

#### Scenario: Comment sync records future reply context

- **WHEN** Edge parses and syncs a platform comment
- **THEN** it stores the sanitized bounded target-comment context by inbound platform comment ID in the current account/environment state
- **AND** the Cloud interaction message remains unchanged

#### Scenario: Approved target has no local context

- **WHEN** an approved reply command names an inbound comment whose local target context is missing
- **THEN** Edge MAY use a bounded read-only lookup to refresh that exact target context
- **AND** if no complete context is found, Edge rejects the command before comment-create `fetch` and MUST NOT reconstruct or dispatch a partial speculative request

### Requirement: Comment confirmation follows captured acknowledgement truth

Edge SHALL report a comment reply confirmed only when transport is successful, platform status is successful, and the response contains a non-empty `data.comment.commentId`. An observed HTTP 201 response with `errCode=0` and that identifier SHALL be accepted. The request remains non-retry-safe: a rejection is failed, while a lost or unreadable response after dispatch remains ambiguous and MUST NOT trigger a blind retry or resend.

#### Scenario: Captured HTTP 201 acknowledgement is confirmed

- **WHEN** the platform returns HTTP 201, `errCode=0`, and a non-empty `data.comment.commentId`
- **THEN** Edge records the returned external comment identifier and reports confirmed delivery

#### Scenario: Dispatch acknowledgement is missing

- **WHEN** dispatch may have occurred but no qualifying acknowledgement can be read
- **THEN** Edge reports the existing ambiguous result and MUST NOT automatically retry the comment-create request
