## ADDED Requirements

### Requirement: Cloud SHALL own the durable environment proxy authority
Cloud SHALL persist exactly one proxy-authority record for each managed environment. The record SHALL distinguish `configured` from explicit `no_proxy`; a missing record SHALL mean uninitialized rather than direct connection. For `configured`, Cloud SHALL persist proxy type, host, port, username, and password in PostgreSQL plaintext as an explicitly accepted product tradeoff.

#### Scenario: Configured proxy survives a machine change
- **WHEN** an owned environment has a configured Cloud proxy authority and the customer signs in from another Edge installation
- **THEN** the new installation SHALL resolve the same original proxy from Cloud without reading an AdsPower profile or the former installation's user-data directory

#### Scenario: Explicit no-proxy remains distinguishable
- **WHEN** the customer explicitly saves an environment without a proxy
- **THEN** Cloud SHALL persist `no_proxy` for that environment
- **AND** Edge SHALL not treat the environment as missing proxy authority

#### Scenario: Missing authority fails closed
- **WHEN** an environment has no Cloud proxy-authority record
- **THEN** proxy detection and managed browser startup SHALL report the authority as uninitialized
- **AND** they SHALL NOT infer the original proxy from the current AdsPower profile

### Requirement: Proxy authority access SHALL be exact, owned, revisioned, and minimum-disclosure
Customer-authenticated proxy-authority reads and writes SHALL address one exact owned environment. Writes SHALL use optimistic revision comparison, and successful responses SHALL return the new revision. Broad environment list/status projections, logs, errors, command arguments, and telemetry SHALL NOT expose the proxy username or password.

#### Scenario: Exact owned read
- **WHEN** an authenticated customer requests proxy authority for an environment assigned to that customer
- **THEN** Cloud SHALL return that exact environment's state, configuration when present, and revision

#### Scenario: Cross-customer access is rejected
- **WHEN** a customer reads or writes proxy authority for an environment that is not assigned to that customer
- **THEN** Cloud SHALL reject the request without disclosing whether credentials exist

#### Scenario: Concurrent edit is rejected by revision
- **WHEN** a client writes with an `expectedRevision` that differs from the current Cloud revision
- **THEN** Cloud SHALL reject the stale write
- **AND** SHALL preserve the newer authority unchanged

#### Scenario: Credentials stay out of broad projections
- **WHEN** Cloud returns environment rosters, status, runtime diagnostics, or operational logs
- **THEN** the proxy username and password SHALL be absent

### Requirement: Provisioning SHALL persist environment ownership and proxy authority atomically
Completing a provisioning intent SHALL require the proxy-authority state supplied from the validated creation input and SHALL persist environment registration, customer assignment, installation ownership, and proxy authority in one PostgreSQL transaction.

#### Scenario: Creation completes with configured proxy
- **WHEN** AdsPower profile creation succeeds and provisioning completion includes a configured proxy
- **THEN** Cloud SHALL atomically persist the environment and the complete original proxy authority

#### Scenario: Creation completes without proxy
- **WHEN** AdsPower profile creation succeeds and provisioning completion explicitly includes `no_proxy`
- **THEN** Cloud SHALL atomically persist the environment and explicit no-proxy authority

#### Scenario: Idempotent completion detects authority mismatch
- **WHEN** provisioning completion is retried for an already completed intent
- **THEN** Cloud SHALL succeed only if the supplied proxy-authority state and fields match the persisted authority
- **AND** SHALL reject a mismatching retry

### Requirement: Local proxy authority SHALL only be a bounded migration source or cache
Edge MAY use its existing safeStorage-backed authority as a bounded migration source when Cloud has no authority, and MAY cache a Cloud response locally. Migration SHALL require a structurally valid original proxy and SHALL reject loopback hosts and known AIDCP/GOST runtime endpoints. AdsPower's current `user_proxy_config` SHALL never be a migration source.

#### Scenario: Valid legacy authority migrates once
- **WHEN** Cloud authority is uninitialized and the local safeStorage record contains a valid non-loopback original proxy
- **THEN** Edge MAY create the Cloud authority with an uninitialized-revision compare
- **AND** subsequent decisions SHALL use the Cloud result

#### Scenario: Loopback legacy record is rejected
- **WHEN** the only local authority points to `127.0.0.1`, `::1`, or a known AIDCP/GOST loopback listener
- **THEN** Edge SHALL reject migration and report manual proxy repair is required
