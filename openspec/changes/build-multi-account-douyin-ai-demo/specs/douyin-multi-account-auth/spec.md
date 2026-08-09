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
In real mode, an operator-initiated QR authorization attempt SHALL launch at most one bounded Chromium instance scoped to that attempt. It MAY use headless mode when the platform-owned QR is projected into the authenticated operations UI and the same environment proves the required identity/read context; comment-writing Chromium remains subject to its separate headed-worker requirement. Chromium MUST exist only while presenting the QR code, observing scan/confirmation, resolving the stable Douyin identity, capturing the authorized web session, and running the required post-login probe. The displayed real QR expiry MUST use the matching platform challenge expiry, with any configured login timeout acting only as an earlier upper bound; the service MUST NOT present an unscanned QR as valid after the platform has expired it. It MAY retain the context for one fixed response-drain window of at most two seconds after that display boundary solely to classify a status request already accepted near expiry, without presenting or admitting a new scan. Official scan and confirmation evidence MUST come from the exact first-party status request associated with the displayed challenge, MUST expose only sanitized states, and MUST NOT retain or project the raw challenge token or response body. A known status in the token-bound response data SHALL be authoritative for the QR transition; localized or absent presentation-copy fields MUST NOT override that status. A scanned or confirmed attempt MAY keep the same context past the display expiry only within the original bounded authorization attempt and MAY begin the read-only identity probe, but neither state is authorization by itself. A credential MUST NOT be created until that same context proves the stable identity and read capability and yields a structurally valid Douyin-scoped cookie set; the implementation MUST NOT require or guess a fixed authentication cookie name. A legacy session cookie already issued to the fresh Profile MAY remain compatible scan evidence but MUST NOT replace identity proof. The service MUST close the browser after confirmed capture, cancellation, expiry, challenge, identity mismatch, or terminal failure; it MUST NOT keep a browser running merely to preserve an authorized account. Fixture mode SHALL simulate the same state transitions without launching Chromium.

#### Scenario: Successful QR authorization closes Chromium
- **WHEN** the operator confirms a QR login, identity resolution succeeds, the encrypted session is stored, and the post-login probe passes
- **THEN** the account becomes authorized and the authorization Chromium instance is closed before the account runtime continues

#### Scenario: Expired QR attempt is bounded
- **WHEN** an authorization QR code expires before platform confirmation
- **THEN** the attempt reaches an expired terminal state, its Chromium instance closes, and a new attempt requires an explicit operator action

#### Scenario: Phone confirmation precedes session settlement
- **WHEN** the matching first-party QR status reports scanned or confirmed before the same browser context has completed identity and session proof
- **THEN** the UI shows authorizing, the context remains bounded by the original authorization deadline, and no credential is persisted until both proofs complete

### Requirement: Explicit secondary verification retains only the bounded official context
The token-bound first-party `error_code=2046` response SHALL be treated as a bounded secondary-verification state, not authorization, generic schema drift, or the terminal challenge referenced by the QR cleanup rule. The service SHALL keep the same Chromium page, Profile, Cookie context, and QR tracker alive only within the original authorization deadline. It MUST NOT create a credential or begin identity proof while that state remains current. The official page SHALL own all verification configuration and request replay; the service MUST NOT parse, persist, project, log, or independently submit verification decision configuration, SMS keys, QR tokens, Cookies, or raw response bodies. The service MAY expose bounded input through the existing operator-authenticated HTTPS origin only when exactly one visible official Verify Center surface is admitted across two exact forms: the allowlisted Verify Center iframe origin and pathname, or the structurally verified same-document `#vc-second-valid` dialog under its fixed, high-z-index, viewport-covering official mask. The candidate MUST be fully inside the current Creator viewport. The service MUST screenshot only that surface element, MUST NOT fall back to the Creator viewport, and MUST bind each JPEG to the exact pending account, challenge, current snapshot revision, Creator document pathname, surface kind, surface-document digest, frame and element identity, and bounding box, plus a latest-only, one-use memory-only frame identity, absolute expiry, and bounded remaining lifetime no more than thirty seconds. The client MUST derive a conservative local deadline from the request start and that remaining lifetime, recheck it after JPEG decode and before every input, and disable and replace the frame before expiry; input MUST first consume the frame identity and revalidate every bound property. It may permit only normalized click, one-shot drag, bounded scroll, at-most-64-character control-free text, and an allowlisted key. Text and keys require an editable focus contained by the admitted surface; an iframe candidate additionally requires that iframe to own top-level focus. Escape is not allowlisted. Top-level navigation MUST be blocked while verification remains current; any newly observed popup MUST be closed immediately and MUST NOT be exposed as a control or image surface. The service MUST NOT expose CDP, a browser debug endpoint, clipboard, upload, download, arbitrary navigation, DevTools, or script execution. Frame identities, screenshots, coordinates, and temporary text MUST NOT be stored. A transiently missing, hidden, moved, malformed, replaced, or ambiguous verification surface SHALL yield no image or input while the attempt stays pending within its original deadline. Creator origin/path mismatch, closing, timeout, explicit expiry/refusal, QR schema failure, or cleanup failure SHALL terminate or quarantine the context without a credential. Official verification completion SHALL only resume the existing stable-identity, IM-bootstrap, and structurally valid Douyin-Cookie proofs.

#### Scenario: Douyin requires official secondary verification
- **WHEN** the token-bound QR status returns the explicit secondary-verification response
- **THEN** the same bounded Chromium context remains alive, the account stays authorizing, only the sanitized verification flag and expiry are projected, and no identity probe or credential creation occurs until the official page replays a confirmed QR response

#### Scenario: Secondary verification does not finish in time
- **WHEN** the official secondary-verification UI remains incomplete at the original authorization deadline
- **THEN** the attempt fails with a distinct sanitized timeout, closes its Chromium/Profile resources, and requires an explicit new QR attempt

#### Scenario: Verification surface is missing, replaced, or ambiguous
- **WHEN** neither exact official surface is currently valid because it is absent, hidden, outside the viewport, duplicated, malformed, replaced, or moved after capture
- **THEN** the service returns no Creator-page fallback, applies no input, and keeps the authorization pending until a fresh valid surface exists or the original deadline expires

#### Scenario: Creator authorization document changes during verification
- **WHEN** the pending page leaves the exact Creator origin and pathname that issued the QR challenge
- **THEN** the service applies no input, closes and cleans the attempt without a credential, and exposes a sanitized terminal error

#### Scenario: Verification frame identity is stale or replayed
- **WHEN** an input names an expired, already-consumed, or non-current frame identity
- **THEN** the service applies no input and requires the operator to act on a newly fetched frame

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
