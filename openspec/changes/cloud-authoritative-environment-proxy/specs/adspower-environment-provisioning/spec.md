## ADDED Requirements

### Requirement: Environment proxy creation and editing SHALL synchronize the Cloud authority
The user-entered proxy configuration SHALL remain the creation input sent to AdsPower. After AdsPower creates the profile, Edge SHALL include the same configured or explicit no-proxy authority in provisioning completion. For an existing environment edit, Edge SHALL commit the Cloud authority with revision comparison before updating the AdsPower execution copy.

#### Scenario: New environment preserves the entered proxy
- **WHEN** a user creates an environment with a validated proxy
- **THEN** Edge SHALL create the AdsPower profile with that proxy
- **AND** SHALL complete Cloud provisioning with the same original proxy authority

#### Scenario: New environment explicitly has no proxy
- **WHEN** a user creates an environment without a proxy
- **THEN** Edge SHALL create the AdsPower profile without a proxy
- **AND** SHALL complete Cloud provisioning with explicit `no_proxy`

#### Scenario: Existing environment edit is Cloud-first
- **WHEN** a user saves a new proxy for an owned existing environment
- **THEN** Edge SHALL first write the exact Cloud authority using the observed revision
- **AND** only after Cloud accepts the write SHALL Edge update AdsPower

#### Scenario: AdsPower update fails after Cloud commit
- **WHEN** Cloud accepts an existing-environment proxy edit but AdsPower rejects the execution-copy update
- **THEN** Edge SHALL report that Cloud is authoritative and AdsPower synchronization failed
- **AND** the next managed start SHALL overwrite AdsPower from the Cloud authority

#### Scenario: Cloud write fails
- **WHEN** Cloud rejects or cannot persist a creation completion or proxy edit
- **THEN** Edge SHALL NOT report the proxy authority as saved
- **AND** an existing-environment edit SHALL NOT update AdsPower
