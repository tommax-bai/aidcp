## ADDED Requirements

### Requirement: Managed AdsPower first-open policy separates credential filling from password saving

For a fresh managed AdsPower profile start, edge SHALL send the AdsPower first-open policy that enables imported credential filling while disabling browser password saving. The start request MUST use `password_filling: "1"` and `password_saving: "0"` and SHALL retain the existing permission-denial launch policy. Enabling credential filling MUST NOT be treated as authority to read, log, persist, or type the stored password. Disabling password saving applies to browser chrome and MUST NOT suppress the separate Facebook Remember Password page signal.

#### Scenario: Fresh AdsPower start applies the policy before Facebook loads
- **WHEN** edge starts an inactive managed AdsPower profile
- **THEN** the V2 start body contains `password_filling: "1"` and `password_saving: "0"`
- **AND** its launch arguments retain permission-prompt suppression before the start URL loads

#### Scenario: AdsPower fills a complete login form
- **WHEN** the imported profile opens the exact Facebook login form and AdsPower has filled both credential fields
- **THEN** the Facebook Native login handler MAY submit the form without receiving or typing a password

#### Scenario: Credential filling is unavailable
- **WHEN** either exact Facebook login field remains empty after the bounded fill observation
- **THEN** edge reports `credential_fill_unavailable` and MUST NOT request the password, guess a value, or submit the incomplete form

#### Scenario: Browser and Facebook remember-password layers remain distinct
- **WHEN** login succeeds
- **THEN** the browser Save Password bubble is suppressed by `password_saving: "0"`
- **AND** a later Facebook Remember Password page modal, if present, remains eligible for its independent Native signal/action

#### Scenario: Already-running profile lacks fresh-start evidence
- **WHEN** AdsPower returns an already-active profile and edge cannot establish that the required password-saving policy was applied to that browser generation
- **THEN** edge MUST NOT claim browser-chrome suppression or run first-login assistance that depends on it
- **AND** an already-authenticated profile MAY still proceed through the ordinary stable-identity gate
