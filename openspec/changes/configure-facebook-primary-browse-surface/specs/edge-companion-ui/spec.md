## ADDED Requirements

### Requirement: Facebook mode and primary surface are independent client choices

For a selected Facebook environment, the Edge client SHALL present operation mode as one mutually exclusive four-option choice (`persona`, `slow_start`, `rule`, `consumption`) and primary browse surface as one independent Feed/Reels choice. Creation and existing-environment editing SHALL use the same concepts. The client MUST render and confirm Cloud write-after-read truth rather than treating a local selection as persisted success.

#### Scenario: Existing environment changes operation mode

- **WHEN** the user selects one of the four operation modes
- **THEN** exactly one mode is selected and the current primary surface remains unchanged

#### Scenario: Existing environment changes primary surface

- **WHEN** the user switches the primary surface between Feed and Reels
- **THEN** the current operation mode remains unchanged
- **AND** the confirmed Cloud projection becomes the displayed selection

#### Scenario: Creation defaults to Reels

- **WHEN** the Facebook creation form opens or resets
- **THEN** its operation mode and primary-surface controls are separate
- **AND** Reels is selected as the primary surface
