## ADDED Requirements

### Requirement: Spawn startup projections SHALL use the lifecycle-frozen deployment target

Before spawning an automation core, the desktop supervisor SHALL freeze the authenticated deployment target and automation target on that lifecycle generation. The child environment, pending `targetCloudKey` status projection, and later connection-receipt validation MUST use those frozen values; post-spawn setup MUST NOT read a removed alias or re-resolve mutable session state.

#### Scenario: Pending target matches the spawned core

- **WHEN** the supervisor freezes target OL and spawns an environment core
- **THEN** the child's automation URL and the pending `targetCloudKey` projection both identify OL from the same lifecycle-frozen value

#### Scenario: Mutable session state changes after spawn

- **WHEN** token refresh or another session transition occurs after the child is spawned but before its connection receipt
- **THEN** startup projection and receipt validation remain scoped to the target frozen for that child and MUST NOT reinterpret it from transient session validity
