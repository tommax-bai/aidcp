## MODIFIED Requirements

### Requirement: Facebook provisioning records one mutually exclusive operation intent

The customer environment-provisioning completion request MAY include `facebookOperationMode=persona|slow_start|rule|consumption`. This field is Facebook-only and SHALL be mutually exclusive with released `slowStartEnabled` and `facebookRuleModeEnabled` inputs; mixing new and legacy operation intents SHALL reject the entire completion before environment, ownership, policy, audit or intent state mutation.

When present, environment registration, ownership assignment, slow-start anchor, initial revisioned operation-policy snapshot, initial audit and provisioning completion SHALL commit atomically. `slow_start` SHALL activate the existing lifecycle and persist `consumption` as its resumable base; `persona`, `rule` and `consumption` SHALL persist their matching base mode; all initial cadence values SHALL come from Cloud defaults. The success response SHALL include the committed customer policy projection, and the client MUST NOT claim that the selected mode was configured unless that projection matches.

#### Scenario: Consumption environment is provisioned atomically

- **WHEN** a valid Facebook provisioning intent completes with `facebookOperationMode=consumption`
- **THEN** Cloud creates the environment, ownership and initial consumption base policy in one transaction
- **AND** any policy/audit failure rolls back all of them, leaving the intent unconsumed

#### Scenario: New and legacy intents cannot be mixed

- **WHEN** a completion request includes `facebookOperationMode` together with either legacy operation Boolean
- **THEN** Cloud rejects the request as a conflicting run mode
- **AND** it does not silently choose a priority or partially create the environment

#### Scenario: Slow-start provisioning resumes into consumption

- **WHEN** a Facebook environment is provisioned with `facebookOperationMode=slow_start` (or a legacy input resolving to slow start) and later graduates without operator reselection
- **THEN** the environment's effective mode becomes `consumption`
