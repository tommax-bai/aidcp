## ADDED Requirements

### Requirement: Video-channel environment scope precedes platform identity binding
The platform runtime abstraction SHALL allow a `wechat_channels` environment to connect with a stable logical account scope derived from its environment key before finder authorization. This exception SHALL NOT change XHS/Facebook identity resolution, and Cloud SHALL still validate `accounts.platform='wechat_channels'` before creating the interaction runtime.

#### Scenario: Multi-environment supervisor starts a new video-channel profile
- **WHEN** the supervisor removes inherited account overrides and starts a `wechat_channels` child with a valid environment/profile ID
- **THEN** the child derives a stable logical account scope from the environment ID, completes hello without a pre-known finder ID, and enters the local authorization state machine

#### Scenario: Platform metadata disagrees
- **WHEN** a video-channel Edge hello resolves to an existing account whose authoritative `accounts.platform` is not `wechat_channels`
- **THEN** Cloud rejects the handshake and MUST NOT issue controls, sync commands, or write commands

### Requirement: Video-channel identity changes do not mutate logical ownership
The platform runtime abstraction SHALL represent the public finder identity as an environment-bound authentication attribute rather than overwriting the logical account key. An identity mismatch SHALL be an authentication failure, not an account migration.

#### Scenario: User scans a different account during reauthorization
- **WHEN** the browser profile authorizes a finder identity different from the durable binding
- **THEN** the runtime keeps the original logical ownership and binding, reports a mismatch, and waits for the correct account instead of registering a second Cloud account
