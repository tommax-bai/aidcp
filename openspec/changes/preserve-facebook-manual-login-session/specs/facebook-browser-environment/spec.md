## ADDED Requirements

### Requirement: Unavailable Facebook credential fill SHALL preserve a controlled manual-login session

When Native confirms one visible Facebook login form but AdsPower has not filled its credential fields after the bounded fill grace, edge SHALL enter `manual_login_required` with reason `credential_fill_unavailable`. Edge MUST stop automated auth actions, keep the current core/browser/CDP generation alive, and MUST NOT exit or relaunch solely because credential fill is unavailable.

#### Scenario: Empty credential fields enter manual login
- **WHEN** the unique Facebook login form remains empty after the credential-fill grace
- **THEN** Native returns `manual_login_required` with reason `credential_fill_unavailable`
- **AND** the core remains alive with browser control available and dispatches no further automated login action

#### Scenario: Manual login resumes in place
- **WHEN** the operator completes login while the environment is waiting for manual login
- **THEN** edge confirms a stable identity through the existing identity gate and continues startup in the same core and browser generation
- **AND** it MUST NOT call browser launch or perform a new CDP attachment for that recovery

#### Scenario: Manual login wait is explicitly closed
- **WHEN** the operator pauses or closes an environment waiting for manual login
- **THEN** edge closes and confirms the owned AdsPower browser through the existing lifecycle close path before releasing the browser slot
- **AND** the supervisor MUST NOT automatically restart that intentional stop
