## ADDED Requirements

### Requirement: Runtime-control updates drive account-scoped Edge delivery
After a successful CAS update of `interaction_runtime_controls`, the internal API SHALL make the committed account/version available to the account's negotiated online Edge through `interaction.runtime.controls`. The database commit and audit record SHALL remain authoritative; delivery count or socket enqueue MUST NOT be reported as Edge application success.

#### Scenario: CAS update reaches one online Edge
- **WHEN** an authorized operator updates runtime controls with the current expected version and exactly one negotiated Edge is online for the account
- **THEN** Cloud commits and audits version `N+1`, pushes a scope-matching `interaction.runtime.controls` payload to that Edge, and returns the committed controls without claiming Edge application

#### Scenario: Edge is offline during update
- **WHEN** the runtime-control CAS succeeds while no negotiated Edge is online
- **THEN** Cloud keeps the committed version, records delivery as deferred/zero, and includes the latest fail-closed snapshot in the next negotiated welcome

### Requirement: Downlinked write controls are effective safety projections
The write booleans delivered to Edge SHALL be false unless the account channel control is enabled, `write_paused=false`, the Cloud global interaction write gate is enabled, offboarding is not pending, and the snapshot scope is valid. Read booleans SHALL also fail closed on provider errors or scope mismatch.

#### Scenario: Account enables replies while global writes remain disabled
- **WHEN** `comments_reply_enabled=true` for an account but the Cloud global write gate is false
- **THEN** the Edge snapshot reports comment reply disabled while preserving the stored account setting for administration

#### Scenario: Runtime-control lookup fails during hello
- **WHEN** Cloud cannot load the account runtime-control row while building welcome
- **THEN** welcome either carries an explicit all-false scope-matching snapshot or omits negotiation so Edge keeps every interaction capability false
