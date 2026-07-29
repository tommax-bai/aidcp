## ADDED Requirements

### Requirement: Customer proxy-authority routes SHALL recheck exact environment ownership
Cloud SHALL expose customer-authenticated exact-environment proxy-authority read and compare-and-set write routes. Every request SHALL resolve current ownership from server-side assignment state and SHALL fail closed when ownership is missing, revoked, or ambiguous.

#### Scenario: Owned environment can be read and updated
- **WHEN** an authenticated customer addresses one currently assigned environment
- **THEN** Cloud SHALL permit the exact authority read or revision-checked write

#### Scenario: Revoked assignment cannot reuse an earlier read
- **WHEN** ownership is revoked after a client read but before its write
- **THEN** the write SHALL be rejected even if its revision otherwise matches

### Requirement: Customer environment projections SHALL not disclose proxy credentials
Existing customer environment roster and browser-independent status routes SHALL remain minimum-disclosure projections and SHALL NOT include proxy username or password. Credential-bearing authority data SHALL only be returned from the exact owned authority route.

#### Scenario: Roster remains credential-free
- **WHEN** a customer loads the environment roster
- **THEN** no proxy username or password SHALL be present in the response
