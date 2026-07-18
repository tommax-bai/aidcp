## ADDED Requirements

### Requirement: Environment nickname double-click is a show-only browser gesture

The Electron environment rail SHALL interpret a double-click on an environment nickname as an explicit request to show that environment's driven browser. The second physical click belonging to the same double-click gesture MUST NOT advance the ordinary `select -> show -> park` phase a second time. A nickname double-click MUST NOT emit a park request, including when the environment was already selected before the gesture.

#### Scenario: Operator double-clicks an already-selected nickname

- **WHEN** the selected environment's browser is parked and the operator double-clicks its nickname
- **THEN** the companion requests that environment's browser be shown
- **AND** it emits no park request for that gesture

#### Scenario: Operator double-clicks an unselected nickname

- **WHEN** the operator double-clicks another environment's nickname
- **THEN** the companion selects that environment and requests its browser be shown
- **AND** it emits no park request for that gesture

