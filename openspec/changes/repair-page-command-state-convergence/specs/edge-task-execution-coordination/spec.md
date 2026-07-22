## ADDED Requirements

### Requirement: Native task takeover SHALL block only the ordinary browse lane
After an edge has confirmed acquisition of a page-task lease, the Native page session MUST admit commands whose task ID matches the active lease and MUST continue to reject commands with no task ID or a different task ID until release.

#### Scenario: Current task command executes while ordinary browse is quiesced
- **WHEN** a Native page session has quiesced ordinary browsing for task `T` and receives a page command owned by task `T`
- **THEN** Edge SHALL execute the command under Native owner `T` rather than returning `native_session_quiesced`

#### Scenario: Ordinary browse remains blocked during the lease
- **WHEN** task `T` owns the page lease and a command without a task ID arrives
- **THEN** Edge SHALL reject or suppress that command without touching the page

#### Scenario: Stale task remains blocked during the lease
- **WHEN** task `T` owns the page lease and a command carrying task ID `U` arrives
- **THEN** Edge SHALL reject or suppress that command without touching the page
