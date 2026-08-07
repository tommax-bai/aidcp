# wechat-channels-browser-foreground-control Specification

## Purpose
TBD - created by archiving change wechat-channels-browser-foreground-control. Update Purpose after archive.
## Requirements
### Requirement: Active video-channel sessions support explicit browser foreground control
The system SHALL allow an authorized customer to open the visible browser sidecar for an `active + closed` video-channel environment and SHALL keep the existing API session active while the browser remains open. The system SHALL allow the customer to close that sidecar and return to `active + closed` API-only operation without clearing or rebinding the encrypted session.

#### Scenario: Customer opens an active API-only environment
- **WHEN** the authoritative auth projection is `status=active`, `browserState=closed`, the identity still matches, and the customer submits an open action for the owned environment
- **THEN** the matching Edge opens that environment's headful browser sidecar, keeps it open, and publishes `status=active` with `browserState=open`
- **AND** comment and direct-message capabilities continue to be derived from the existing auth and runtime-control gates

#### Scenario: Customer returns an open browser to background operation
- **WHEN** the authoritative auth projection is `status=active`, `browserState=open` and the customer submits a close action
- **THEN** the matching Edge closes the sidecar, retains the encrypted API session, and publishes `status=active` with `browserState=closed`

### Requirement: Browser foreground control is scoped, idempotent, and lifecycle-safe
Every browser control command MUST carry the exact `envKey + accountId + platform` scope and MUST execute only on the uniquely matched online Edge. Repeated actions for the already-reached state SHALL be idempotent. Environment pause, stop, offboard, or runtime destruction MUST close a manually opened sidecar.

#### Scenario: Scope does not match the connected Edge
- **WHEN** a browser control command names a different environment, account, or platform than the connected Edge runtime
- **THEN** Edge rejects the command without opening, focusing, or closing any browser

#### Scenario: Repeated action targets the current state
- **WHEN** Edge receives open while the owned sidecar is already open, or close while it is already closed
- **THEN** Edge leaves the current state unchanged and publishes or preserves the same truthful browser projection without spawning or stopping another profile

#### Scenario: Environment lifecycle ends while browser is visible
- **WHEN** a manually opened sidecar exists and the environment is paused, stopped, offboarded, or its runtime is destroyed
- **THEN** Edge closes the owned sidecar before completing lifecycle cleanup and MUST NOT affect another environment's browser

### Requirement: Browser command acceptance is not execution success
Cloud SHALL report browser control requests as accepted only after ownership and routing checks pass. The client MUST use a later Edge `wechat_channels.inbox.auth.status.browserState` projection as execution truth and MUST NOT infer success from enqueue, socket delivery, or HTTP acceptance.

#### Scenario: Open command is accepted but Edge has not confirmed state
- **WHEN** Cloud accepts and routes an open action but no later `browserState=open` projection has arrived
- **THEN** the client reports that the request is waiting for Edge state and MUST NOT state that the browser is open

#### Scenario: Browser launch is unavailable
- **WHEN** the owned Edge cannot launch or attach the sidecar
- **THEN** the prior API auth state remains truthfully represented, browser state is unavailable or unchanged, and the system MUST NOT fabricate an open result or fall back to another browser profile

### Requirement: Manual foreground control remains separate from reauthorization
Manual browser open/close SHALL NOT clear the session, change the bound platform identity, or count as reauthorization. Auth expiry, challenge, and identity mismatch MUST continue through the existing reauthorization flow and fail-closed capability rules.

#### Scenario: Active customer opens browser only for inspection
- **WHEN** the customer opens an `active + closed` environment and performs no reauthorization
- **THEN** the bound identity and encrypted session remain unchanged and the system describes the action as browser foreground control rather than login success

#### Scenario: Authentication becomes invalid while manually visible
- **WHEN** auth expiry, challenge, or identity mismatch is detected while the browser is manually open
- **THEN** Edge enters the corresponding reauthorization or challenge state, keeps writes fail closed, and MUST NOT treat browser visibility as proof of valid authorization
