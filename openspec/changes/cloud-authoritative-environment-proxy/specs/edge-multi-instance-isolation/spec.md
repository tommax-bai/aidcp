## ADDED Requirements

### Requirement: Instance user-data isolation SHALL not fork environment proxy authority
`AIDCP_USER_DATA_DIR` SHALL isolate local Edge instance state but SHALL NOT define the durable environment proxy authority. All instances authenticated as an owning customer SHALL resolve the same environment authority from Cloud; local safeStorage records SHALL be migration/cache data only.

#### Scenario: Alternate user-data directory starts the same environment
- **WHEN** Edge starts with a different `AIDCP_USER_DATA_DIR` for an environment whose Cloud authority exists
- **THEN** it SHALL use the same Cloud authority and revision as another installation
- **AND** SHALL not initialize authority from that directory's AdsPower state

#### Scenario: Local caches disagree
- **WHEN** two user-data directories contain different cached proxy values
- **THEN** the current Cloud authority SHALL win
- **AND** neither cache SHALL overwrite Cloud except through the explicit bounded migration path
