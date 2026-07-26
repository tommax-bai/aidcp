## ADDED Requirements

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
