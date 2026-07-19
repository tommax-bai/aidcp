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
