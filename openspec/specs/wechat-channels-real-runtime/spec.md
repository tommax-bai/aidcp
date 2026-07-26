# wechat-channels-real-runtime Specification

## Purpose
TBD - created by archiving change wechat-channels-real-runtime-closure. Update Purpose after archive.
## Requirements
### Requirement: First authorization establishes a durable platform identity binding
For `wechat_channels`, the system SHALL establish the logical account scope from the stable environment key before platform login, SHALL bind the first successfully verified finder identity to that environment after authorization, and MUST NOT require the operator to preconfigure or know the finder external ID. The logical `accountId` and bound `finderIdentity` SHALL be distinct fields and MUST NOT be treated as equal by construction.

#### Scenario: New environment authorizes for the first time
- **WHEN** a new video-channel environment has no encrypted identity binding and the assigned browser profile returns a valid authorized finder identity
- **THEN** Edge binds that finder identity to the current `envKey + accountId + browserProfileId`, reports the public identity projection, and continues only after enabled read probes succeed or are explicitly disabled

#### Scenario: Existing environment observes another finder identity
- **WHEN** a stored environment binding exists and an active or restored browser session reports a different finder identity
- **THEN** Edge reports identity mismatch, clears all effective read/write capabilities, and MUST NOT replace the durable binding or sync data from the observed account

### Requirement: Account-scoped controls are required for every effective capability
Edge SHALL derive video-channel effective capabilities by intersecting build support, the latest scope-matching Cloud runtime-control snapshot, active authorization, durable identity match, endpoint probe state, and local circuit/kill switches. Missing, malformed, stale, unnegotiated, or scope-mismatched Cloud controls MUST NOT grant a capability.

#### Scenario: New Edge connects to an old Cloud
- **WHEN** Edge declares `interaction_runtime_controls_v1` but welcome omits an account-scoped runtime-control snapshot
- **THEN** Edge keeps every video-channel read and write capability false while preserving the Cloud connection and authorization guidance

#### Scenario: Online control update arrives out of order
- **WHEN** Edge receives a scope-matching control update whose version is lower than the latest applied version
- **THEN** Edge ignores the update and MUST NOT roll back to an older capability set

### Requirement: Private endpoint requests are evidence-bound
Every video-channel private endpoint SHALL use an explicit request descriptor backed by a sanitized capture from a real authorized session. The descriptor SHALL fix method, path, query shape, body encoding, necessary non-secret header names, cookie-jar class, retry safety, and success parsing. A capability without capture coverage MUST remain disabled.

#### Scenario: Captured descriptor serializes a comment request
- **WHEN** the API client builds the comment request represented by the sanitized real-session fixture
- **THEN** its method, path, query keys, content type, body keys/types, header names, and cookie-jar selection exactly match the fixture without embedding any captured secret value

#### Scenario: Write endpoint has not been captured
- **WHEN** an operator enables an account write control but the current build has no capture-backed descriptor/write probe for that endpoint
- **THEN** Edge reports the write capability false and rejects the command before any platform request is dispatched

### Requirement: Capture evidence is secret-free and honest
The repository SHALL contain only sanitized request-shape evidence and MUST NOT contain raw HAR files, Cookie or token values, QR data, full finder IDs, full message bodies, or private-message content. Capture observation, request dispatch, platform acceptance, and platform-confirmed send SHALL be recorded as separate evidence states.

#### Scenario: Sanitized fixture is committed
- **WHEN** a real authorized request is converted into a repository fixture
- **THEN** automated scans find only structural names/types and redacted identifiers, and the fixture states whether the request was merely observed, dispatched, accepted, or platform-confirmed

### Requirement: Real write validation remains target-gated
Real comment or direct-message writes SHALL execute only for an operator-approved disposable target whose exact identifier is supplied for the current validation. Request-format calibration or a successful read-only authorization MUST NOT satisfy this gate.

#### Scenario: Authorized session exists without a disposable target
- **WHEN** a real account is active but no exact disposable comment or DM target has been approved
- **THEN** the system may capture read traffic and validate gated serialization but MUST NOT submit a real write or mark write acceptance complete

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

