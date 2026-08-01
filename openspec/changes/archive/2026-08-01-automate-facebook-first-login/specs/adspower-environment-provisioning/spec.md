## ADDED Requirements

### Requirement: Facebook first-login TOTP is brokered as a profile-bound one-time value

Electron main SHALL provide a named first-login TOTP operation only to the currently managed child and bind it to that child's exact AdsPower profile id. The operation SHALL query AdsPower V2 for exactly that profile, require one successful exact-id match, extract the stored `fakey` only in main-process memory, compute the TOTP for the caller's validated Facebook server-time window, and return only the six-digit code and non-secret validity timestamps. It MUST NOT return the username, password, 2FA key, cookies, proxy fields, or raw AdsPower response to the child, and MUST NOT add the sensitive V2 profile-list response to the generic AdsPower child broker.

#### Scenario: Exact managed profile receives one fresh code
- **WHEN** the current managed child requests TOTP for its bound Facebook AdsPower profile and a validated current server-time window
- **THEN** Electron requires exactly one matching V2 profile record, computes a six-digit code for that window, and returns only the code plus validity timestamps over the private correlated IPC reply

#### Scenario: Child cannot select another profile
- **WHEN** a managed child supplies, implies, or attempts to query a profile id different from its bound environment
- **THEN** Electron rejects the request without reading or returning login material for either profile

#### Scenario: Raw profile material never crosses the broker boundary
- **WHEN** AdsPower returns a profile record containing username, password, `fakey`, cookies, proxy fields, or other metadata
- **THEN** Electron projects only a generated code and validity timestamps into the reply
- **AND** raw response bodies and secret fields MUST NOT appear in child messages, settings, logs, UI receipts, Cloud messages, errors, or OpenSpec task records

#### Scenario: Missing or ambiguous 2FA material fails closed
- **WHEN** AdsPower is unavailable, returns a nonzero code, returns zero or multiple matches, returns a mismatched profile id, or the exact profile lacks a valid Base32 `fakey`
- **THEN** Electron returns only a safe bounded failure reason
- **AND** edge MUST NOT use another profile, a persisted copy, an old code, or a guessed key

#### Scenario: Server-time request is outside the current bounded window
- **WHEN** the requested Facebook server time is malformed or outside the allowed skew from the current request
- **THEN** Electron rejects code generation and returns no secret-derived value
