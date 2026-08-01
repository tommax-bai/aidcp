## ADDED Requirements

### Requirement: Facebook provisioning persists the selected primary surface

The client provisioning request for a Facebook environment SHALL carry one primary browse surface independent from the selected operation mode. Cloud SHALL validate the value, persist it atomically with the environment's operation policy and ownership, and return the committed surface projection. The client creation form SHALL preselect Reels.

#### Scenario: Default creation persists Reels

- **WHEN** a user creates a Facebook environment without changing the preselected surface control
- **THEN** the request carries `reels`
- **AND** Cloud returns the committed Reels surface with the new environment

#### Scenario: Explicit Feed creation persists Feed

- **WHEN** a user selects Feed before creating the Facebook environment
- **THEN** Cloud persists and returns Feed without changing the selected operation mode

#### Scenario: Non-Facebook creation rejects a surface intent

- **WHEN** a provisioning request for another platform carries a Facebook primary surface
- **THEN** Cloud rejects the request without partially creating or assigning the environment
