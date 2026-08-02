## ADDED Requirements

### Requirement: Managed Facebook credential filling SHALL receive a 25-second observation window

For a freshly started managed AdsPower Facebook login document, Edge SHALL observe the exact username and password fields for up to 25 seconds while provider credential filling is pending. Empty fields during that window SHALL remain a non-terminal hydration state. Edge MUST NOT read, request, log, persist, guess, or type the stored credentials. If either exact field remains empty when the 25-second document-bound window expires, Edge SHALL report `credential_fill_unavailable` and retain the controlled browser for manual completion.

#### Scenario: Saved credentials arrive after the initial form render
- **WHEN** the exact Facebook login form first renders empty and AdsPower fills both fields within 25 seconds on the same document
- **THEN** Edge SHALL keep startup pending without reporting manual login
- **AND** the existing Native login action MAY proceed only after a fresh probe confirms both fields and the exact safe submit target

#### Scenario: Saved credentials remain unavailable
- **WHEN** either exact login field is still empty after the same document has been observed for 25 seconds
- **THEN** Edge SHALL report `credential_fill_unavailable`, preserve the browser/CDP session, and perform no credential or submit action

#### Scenario: Login document changes during observation
- **WHEN** the Facebook login document navigates or is replaced before the 25-second observation expires
- **THEN** any continued observation SHALL bind to the new document and MUST NOT carry action evidence from the prior document
