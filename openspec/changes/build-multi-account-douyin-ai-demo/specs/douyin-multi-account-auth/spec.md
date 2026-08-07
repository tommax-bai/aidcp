## ADDED Requirements

### Requirement: Operator access is token protected
The demo SHALL require one configured operator token for every non-health HTTP API, sensitive view-model response, and live-event subscription. The static operations UI shell MAY load before authorization only when it contains no account, QR, session, timeline, or runtime state. The server MUST receive the token through process configuration, and the operations UI MUST retain an entered token only in page memory. The token MUST NOT be stored in SQLite or browser persistent storage and MUST NOT appear in URLs, rendered HTML, application logs, timeline payloads, or fixture data. Requests with a missing or incorrect token MUST be rejected before account, QR, session, or runtime state is disclosed or changed.

#### Scenario: Unauthorized account listing is rejected
- **WHEN** a client requests the account list without the configured operator token
- **THEN** the server returns an authorization failure and discloses no account metadata

#### Scenario: Live-event subscription authenticates before publishing
- **WHEN** a client opens the live-event subscription with an invalid operator token
- **THEN** the server closes or rejects the connection before publishing any runtime event

### Requirement: Fixture and real platform modes are explicit and isolated
The demo SHALL start in exactly one configured platform mode: fixture or real. Fixture SHALL be the default, MUST use deterministic local identities and events, and MUST NOT launch a platform browser, load retained real sessions, contact Douyin endpoints, or perform platform writes. Real mode MUST be explicitly enabled at process startup, SHALL be labeled experimental, and MUST use only real-mode account and session storage; changing mode MUST require a process restart and MUST NOT reinterpret records created by the other mode.

#### Scenario: Default startup remains offline
- **WHEN** the service starts without an explicit real-mode setting
- **THEN** it selects fixture mode and performs no Douyin network, login, browser, or write operation

#### Scenario: Fixture records cannot authorize real mode
- **WHEN** the service restarts in real mode after fixture accounts have been created
- **THEN** those fixture accounts and sessions are not loaded as real Douyin authorization

### Requirement: QR authorization uses a short-lived Chromium session
In real mode, an operator-initiated QR authorization attempt SHALL launch at most one headed Chromium instance scoped to that attempt. Chromium MUST exist only while presenting the QR code, observing scan/confirmation, resolving the stable Douyin identity, capturing the authorized web session, and running the required post-login probe. The service MUST close the browser after confirmed capture, cancellation, expiry, challenge, identity mismatch, or terminal failure; it MUST NOT keep a browser running merely to preserve an authorized account. Fixture mode SHALL simulate the same state transitions without launching Chromium.

#### Scenario: Successful QR authorization closes Chromium
- **WHEN** the operator confirms a QR login, identity resolution succeeds, the encrypted session is stored, and the post-login probe passes
- **THEN** the account becomes authorized and the authorization Chromium instance is closed before the account runtime continues

#### Scenario: Expired QR attempt is bounded
- **WHEN** an authorization QR code expires before platform confirmation
- **THEN** the attempt reaches an expired terminal state, its Chromium instance closes, and a new attempt requires an explicit operator action

### Requirement: Retained sessions are encrypted and identity bound
The demo SHALL encrypt retained real-mode session material at rest with operator-provided key material and SHALL bind it to the resolved stable Douyin identity and local account id. Cookies, tokens, QR payloads, browser debug endpoints, encryption keys, and raw session values MUST NOT be returned by APIs or written to logs, timelines, fixtures, or error messages. A restored session MUST pass an identity and read-capability probe before its account runtime becomes active; an explicit authentication failure SHALL mark the account reauthorization-required and stop new inbound and outbound platform work.

#### Scenario: Restored session has the wrong identity
- **WHEN** decrypted session material resolves to a different Douyin identity than the account binding
- **THEN** the service rejects the session, starts no account runtime, exposes an identity-mismatch state, and requires explicit reauthorization

#### Scenario: Platform explicitly rejects authorization
- **WHEN** an active account receives a definitive platform authentication rejection
- **THEN** the service marks reauthorization-required, stops new source reads and sends, and does not translate the rejection into a transient healthy state

### Requirement: One local account and runtime own each Douyin identity
The demo SHALL maintain at most one local account record and at most one active inbound runtime for each stable Douyin identity within a platform mode. An explicit reauthorization for an existing account MUST update only that account when the resolved identity matches. A new-account authorization that resolves to an identity already bound elsewhere MUST reject the pending account rather than create, merge, or start a duplicate. Runtime creation and replacement MUST be serialized so concurrent restore, reauthorization, and operator-start requests cannot create multiple direct-message streams or comment pollers for the same identity.

#### Scenario: Reauthorization resolves its existing identity
- **WHEN** a reauthorization attempt for an existing account resolves to that account's bound stable identity
- **THEN** the service updates that account's encrypted session and retains exactly one account record and one eligible runtime

#### Scenario: New-account authorization resolves a bound identity
- **WHEN** a new-account QR attempt resolves to a stable identity already bound to another local account
- **THEN** the pending attempt is rejected and no duplicate account or runtime is created

#### Scenario: Concurrent starts are coalesced
- **WHEN** two valid operator requests try to start the same authorized account concurrently
- **THEN** the service starts at most one runtime and reports the same resulting runtime ownership to both requests

### Requirement: Logout revokes local platform capability
An operator-confirmed logout SHALL stop the account runtime, cancel unsubmitted account work, close any account-owned authorization or comment browser, delete retained session material, and mark the account logged out. Logout MUST NOT report completion until local session deletion and runtime shutdown are confirmed, and it MUST NOT delete sanitized historical timeline records needed to explain prior outcomes.

#### Scenario: Authorized account is logged out
- **WHEN** an authenticated operator confirms logout for an authorized account
- **THEN** the account can no longer read or send on Douyin without a new QR authorization and its prior sanitized timeline remains inspectable
