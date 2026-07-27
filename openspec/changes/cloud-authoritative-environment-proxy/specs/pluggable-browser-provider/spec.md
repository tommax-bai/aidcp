## ADDED Requirements

### Requirement: AdsPower proxy configuration SHALL be an execution copy of the frozen Cloud authority
Before starting an AdsPower profile with a configured proxy, Edge SHALL write exactly one effective proxy into AdsPower `user_proxy_config`: the frozen Cloud original proxy in direct mode, or the current AIDCP/GOST loopback in double-hop mode. Edge SHALL read the profile back and stop before browser launch if the effective proxy was not adopted.

#### Scenario: Direct start uses original authority
- **WHEN** system-upstream mode is disabled and the frozen Cloud authority is configured
- **THEN** Edge SHALL write the original Cloud proxy to AdsPower before launch
- **AND** SHALL not inject a competing browser proxy authority

#### Scenario: Double-hop start uses only the GOST loopback
- **WHEN** system-upstream mode is enabled and the frozen Cloud authority is configured
- **THEN** Edge SHALL write only the current GOST loopback to AdsPower before launch
- **AND** SHALL not retain or inject a second competing browser proxy authority

#### Scenario: Effective proxy readback differs
- **WHEN** AdsPower readback does not match the intended effective proxy
- **THEN** Edge SHALL stop startup and report the synchronization failure

#### Scenario: Close restores the frozen original as fallback
- **WHEN** a managed profile closes after an execution-copy override
- **THEN** Edge SHALL attempt to restore the original proxy from the frozen Cloud revision
- **AND** a restoration failure SHALL be observable without changing Cloud authority
