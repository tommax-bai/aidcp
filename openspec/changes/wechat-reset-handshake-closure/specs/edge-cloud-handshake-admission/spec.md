## ADDED Requirements

### Requirement: Cloud routes only successfully welcomed Edge connections
Cloud SHALL add an Edge socket to its online routing registry only after the `hello` handler returns a successful `welcome`. A rejected, errored, malformed, or dependency-not-ready hello MUST NOT be resolvable by account, edge id, or declared capability and MUST be closed after the error response is emitted.

#### Scenario: Runtime dependency is not ready
- **WHEN** an Edge sends hello before Cloud's connection runtime dependencies are ready
- **THEN** Cloud rejects and closes the connection, and account/capability routing cannot resolve it

#### Scenario: Successful welcome becomes routable
- **WHEN** Cloud accepts hello and returns a valid welcome
- **THEN** Cloud registers the socket exactly once and may route commands using the accepted session identity and negotiated capabilities

### Requirement: Cloud listens only after handshake dependencies are ready
Cloud MUST construct all dependencies required by hello handling before opening the Edge WebSocket listener. Service startup MUST NOT expose a window in which a syntactically valid hello can reach an uninitialized runtime registry.

#### Scenario: Edge reconnects during Cloud startup
- **WHEN** an Edge retries while Cloud is still assembling handshake dependencies
- **THEN** the TCP/WebSocket listener is not yet available, and the Edge retries until a fully initialized Cloud can return welcome

### Requirement: Edge accepts only a valid welcome
Edge SHALL treat hello as completed only when the correlated response type is `welcome` and its payload contains a valid non-empty session id. An error or malformed response MUST NOT set connected handshake state, peer capabilities, interaction runtime controls, or other welcome-derived state.

#### Scenario: Hello receives handler error
- **WHEN** Edge receives an `error` response correlated to its hello request
- **THEN** Edge rejects the handshake and enters the existing recovery path without presenting itself as command-ready

#### Scenario: Valid welcome completes negotiation
- **WHEN** Edge receives a valid welcome with a non-empty session id and negotiated capabilities
- **THEN** Edge records the welcome state and accepts only commands covered by those negotiated capabilities

### Requirement: Transport admission is independent from business readiness
Cloud SHALL complete hello/welcome for a connection with valid account identity, edge id, and matching supported platform before activating persona-dependent or browse-orchestration business runtime. Missing persona, inactive dispatch, exhausted quota, unsupported browse capability, or a business-role construction/setup error MUST NOT be returned as a handshake error and MUST NOT close the transport. Business actions MUST remain fail-closed when their runtime is unavailable.

#### Scenario: Video Channels account has no persona
- **WHEN** a valid `wechat_channels` Edge without persona completes hello
- **THEN** Cloud returns welcome with negotiated interaction capabilities, keeps the connection online, does not construct browse orchestration, and does not read or require persona

#### Scenario: XHS or Facebook account has no persona
- **WHEN** a valid XHS or Facebook Edge without persona completes hello
- **THEN** Cloud returns welcome and later reports the unbound persona state, while browse/publish business sessions remain inactive until persona is actually bound

#### Scenario: Business runtime activation throws
- **WHEN** dispatcher construction or setup fails after a valid connection has been welcomed
- **THEN** Cloud records a degraded activation failure, keeps transport routing online, and all dispatcher-dependent operations fail closed without causing Edge reconnect

#### Scenario: Post-welcome asynchronous business handler rejects
- **WHEN** a fire-and-forget event handler or hello snapshot push rejects after welcome
- **THEN** Cloud records the rejected operation with context, contains it inside that business path, and keeps the process and Edge transport alive

### Requirement: Same-edge replacement commits only after welcome
Cloud SHALL close an older connection with the same edge id only after the candidate connection has returned a successful welcome and entered the online routing registry. A rejected, errored, or incomplete candidate MUST NOT displace the older healthy connection.

#### Scenario: Replacement candidate fails before welcome
- **WHEN** a candidate hello uses an edge id already held by a healthy connection but fails admission before welcome
- **THEN** Cloud leaves the older connection and its runtime untouched

#### Scenario: Replacement candidate is welcomed
- **WHEN** a candidate with the same edge id completes welcome
- **THEN** Cloud closes the older session and retains the welcomed candidate as the replacement
