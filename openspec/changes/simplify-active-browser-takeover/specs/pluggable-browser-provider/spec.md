## MODIFIED Requirements

### Requirement: AdsPower proxy configuration SHALL be an execution copy of the frozen Cloud authority
Before starting an Inactive AdsPower profile with a configured proxy, Edge SHALL write exactly one effective proxy into AdsPower `user_proxy_config`: the frozen Cloud original proxy in direct mode, or the current AIDCP/GOST loopback in double-hop mode. Edge SHALL read the profile back and stop before browser launch if the effective proxy was not adopted. When AdsPower reports the profile Active, Edge SHALL attach directly without resolving, synchronizing, preflighting, or validating its proxy and SHALL NOT claim that the running browser matches Cloud authority.

#### Scenario: Direct start uses original authority
- **WHEN** system-upstream mode is disabled, the frozen Cloud authority is configured, and AdsPower reports the profile Inactive
- **THEN** Edge SHALL write the original Cloud proxy to AdsPower before launch
- **AND** SHALL not inject a competing browser proxy authority

#### Scenario: Double-hop start uses only the GOST loopback
- **WHEN** system-upstream mode is enabled, the frozen Cloud authority is configured, and AdsPower reports the profile Inactive
- **THEN** Edge SHALL write only the current GOST loopback to AdsPower before launch
- **AND** SHALL not retain or inject a second competing browser proxy authority

#### Scenario: Effective proxy readback differs
- **WHEN** AdsPower reports the profile Inactive and readback does not match the intended effective proxy
- **THEN** Edge SHALL stop startup and report the synchronization failure

#### Scenario: Configured profile is already Active
- **WHEN** AdsPower reports a configured profile as Active
- **THEN** Edge SHALL attach to and take over that Active browser without rewriting its running profile
- **AND** SHALL NOT resolve Cloud proxy authority, prepare a proxy chain, run proxy preflight, probe public egress, compare proxy state, or require a profile-generation marker before takeover

#### Scenario: Active-only observation races with browser close
- **WHEN** Electron selected direct Active takeover but the child subsequently observes the profile as Inactive
- **THEN** the child SHALL fail that takeover without starting a new browser
- **AND** a future fresh start SHALL still pass the normal authority, preflight, synchronization, and readback gates

#### Scenario: No-proxy Active browser uses the same direct path
- **WHEN** AdsPower reports the profile as Active regardless of configured or explicit `no_proxy` state
- **THEN** Edge SHALL use the same direct takeover behavior without proxy gates or mutation

#### Scenario: Close restores the frozen original as fallback
- **WHEN** a managed profile closes after an execution-copy override
- **THEN** Edge SHALL attempt to restore the original proxy from the frozen Cloud revision
- **AND** a restoration failure SHALL be observable without changing Cloud authority
