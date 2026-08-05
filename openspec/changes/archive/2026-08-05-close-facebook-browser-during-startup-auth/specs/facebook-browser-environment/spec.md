## ADDED Requirements

### Requirement: Facebook startup lifecycle interruption SHALL confirm owned browser teardown

Before the normal runtime lifecycle controller is available, Edge SHALL treat an operator pause or close during Facebook startup authentication as a request to stop and confirm the currently owned AdsPower browser. Edge MUST NOT advance to identity, Cloud connection, or account-scoped work after that interruption unless the operator explicitly resumes.

#### Scenario: Close during authenticated quiet-window confirmation

- **WHEN** a Facebook startup authentication coordinator is observing an authenticated quiet window and the operator closes the environment
- **THEN** Edge calls the existing confirmed close operation for that owned AdsPower browser and emits browser-close evidence before exiting the core
- **AND** Electron displays closed only after receiving evidence scoped to the same lifecycle generation

#### Scenario: Startup browser close cannot be confirmed

- **WHEN** the owned browser close operation cannot confirm that the profile CDP endpoint is dark
- **THEN** Edge emits the existing close-failed result, keeps the core at the blocked startup boundary, and releases no browser slot as confirmed closed
- **AND** Electron MUST NOT display the browser as closed or advance the environment to account-scoped work

#### Scenario: Operator retries close after an unconfirmed startup close

- **WHEN** startup is blocked after an unconfirmed close and the operator requests pause or close again
- **THEN** Edge retries the same existing confirmed close operation for the same owned browser generation
- **AND** it exits only after confirmed browser-close evidence is delivered

#### Scenario: Operator resumes after an unconfirmed startup close

- **WHEN** startup is blocked after an unconfirmed close and the operator explicitly resumes
- **THEN** Edge resumes Facebook authentication reconciliation in the same retained browser generation
- **AND** it MUST NOT open a second profile browser or bypass the stable-identity gate

#### Scenario: Intentional core exit lacks browser-close evidence

- **WHEN** an Edge core exits under a local pause or close intent without generation-matched browser-close evidence
- **THEN** Electron reports that browser closure is unconfirmed instead of displaying the browser as closed
