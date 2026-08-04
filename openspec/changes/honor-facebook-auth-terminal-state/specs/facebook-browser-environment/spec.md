## ADDED Requirements

### Requirement: Terminal Facebook startup authentication failure SHALL close the owned browser

When the Facebook startup authentication coordinator reaches a terminal failure, Edge SHALL report the existing authentication failure, call the existing confirmed close operation for the AdsPower browser owned by that startup, and then exit the core. It MUST NOT retain that browser merely because normal runtime lifecycle assembly was not reached.

#### Scenario: Unsupported checkpoint stops startup

- **WHEN** startup authentication terminates with `unsupported_facebook_checkpoint`
- **THEN** Edge reports the existing structured authentication failure and invokes the existing owned-browser confirmed close operation before process exit
- **AND** confirmed closure is reported through the existing generation-scoped browser-close evidence

#### Scenario: Browser closure cannot be confirmed

- **WHEN** the existing owned-browser close operation cannot confirm that the startup browser is dead
- **THEN** Edge exits with the original authentication failure and supplies no false browser-close evidence
- **AND** the existing supervisor projection keeps browser closure unconfirmed

#### Scenario: Manual login is still required

- **WHEN** startup authentication returns the existing controlled `manual_required` result
- **THEN** Edge retains the current browser and CDP session under the existing manual-login contract
- **AND** MUST NOT treat that non-terminal state as a terminal authentication failure
