## ADDED Requirements

### Requirement: Ordinary browse SHALL pause while CDP browser control is unhealthy

The browse loop MUST subscribe to CDP control-health transitions. While control is recovering or unavailable, it MUST NOT dequeue or dispatch a new ordinary browse command. An in-flight atom SHALL end at its current command boundary with an honest failure and MUST NOT be retried automatically. On successful soft recovery, the browse loop SHALL re-evaluate and report the current page rather than replaying the interrupted atom.

#### Scenario: Recovery begins with queued browse work
- **WHEN** CDP control enters recovering state while ordinary browse commands are queued
- **THEN** the edge leaves those commands undispatched until recovery succeeds or terminal recovery handling stops the session

#### Scenario: Soft recovery succeeds after a browse interruption
- **WHEN** a CDP soft-stall recovery succeeds
- **THEN** the edge reports its current page state for a new cloud decision and MUST NOT reuse the old click coordinates or replay the interrupted command
