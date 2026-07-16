## ADDED Requirements

### Requirement: Customer interaction scope resolves through the environment binding
Customer interaction APIs SHALL resolve `envKey` to the authoritative video-channel `interaction_auth_state.account_id` binding on every request. They MUST NOT assume that the external finder ID or customer-provided input is the Cloud logical account ID.

#### Scenario: Authorized environment uses an env-key logical account
- **WHEN** an enabled customer owns a video-channel environment whose auth binding maps the environment to a logical account derived from that env key
- **THEN** list, detail, sync, reopen, reply, and offboard operations use the bound account ID and return the same `envKey` without exposing the finder identity as an authorization selector

#### Scenario: Environment ownership exists before identity binding
- **WHEN** a customer owns a video-channel environment but no authoritative interaction auth binding exists yet
- **THEN** read APIs return an honest login/binding-required state or scoped not-ready response and MUST NOT fall back to an unrelated account

### Requirement: Customer auth projections preserve control/application uncertainty
Customer-facing interaction responses SHALL distinguish Cloud-stored runtime controls, Edge-reported effective capabilities, and authorization status. Missing Edge application evidence MUST keep writes disabled.

#### Scenario: Cloud control version exceeds Edge-applied version
- **WHEN** the stored account control version is newer than the latest Edge auth/capability projection
- **THEN** the customer response marks the Edge capability state pending/stale and MUST NOT enable send controls
