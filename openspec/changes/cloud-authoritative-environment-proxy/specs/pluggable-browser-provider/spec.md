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

### Requirement: Managed AdsPower Local API traffic SHALL be runtime-serialized
Every AdsPower Local API request owned by one Electron desktop runtime SHALL pass through one main-process FIFO, including requests made for main-process UI/runtime operations and managed Edge-child browser lifecycle operations. A configured proxy write and its exact readback SHALL execute as one uninterrupted batch with the required request spacing.

#### Scenario: Main-process refresh overlaps managed child startup
- **WHEN** the Electron main process requests AdsPower profile data while a managed child is synchronizing its startup proxy
- **THEN** both operations SHALL execute through the same FIFO
- **AND** the main-process request SHALL NOT interleave between the child's proxy write and exact readback

#### Scenario: Managed child waits for the coordinator
- **WHEN** a child browser operation is queued behind an earlier AdsPower request
- **THEN** the child SHALL remain in a non-terminal starting state without launching the browser
- **AND** queue waiting SHALL NOT consume the child's failure or respawn budget

#### Scenario: Broker rejects an unsafe child request
- **WHEN** a managed child requests an unapproved endpoint, method, batch size, or another profile identifier
- **THEN** Electron SHALL reject it before contacting AdsPower
- **AND** SHALL NOT disclose the API key or proxy credentials in status or logs
