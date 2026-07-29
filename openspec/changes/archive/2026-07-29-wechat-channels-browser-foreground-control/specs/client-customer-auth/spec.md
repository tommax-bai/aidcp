## ADDED Requirements

### Requirement: Customer browser control API is ownership-scoped and acceptance-only
Customer auth SHALL expose an idempotent browser control operation for an owned video-channel environment. Every request MUST revalidate enabled-user state, environment ownership, and authoritative interaction account binding before routing the exact `envKey + accountId` to one negotiated online Edge. The success response SHALL mean accepted only and MUST NOT represent browser execution success.

#### Scenario: Owner requests browser open
- **WHEN** an enabled customer submits an idempotent open action for an owned video-channel environment with an authoritative interaction binding and one compatible Edge online
- **THEN** Cloud returns an accepted envelope with an action request ID and routes one scoped browser control command
- **AND** the response MUST NOT state that the browser is already open

#### Scenario: Owner requests browser close
- **WHEN** an enabled customer submits an idempotent close action for an owned video-channel environment with one compatible Edge online
- **THEN** Cloud returns an accepted envelope with an action request ID and routes one scoped browser control command
- **AND** the response MUST NOT state that the browser is already closed

#### Scenario: Environment is not owned by the customer
- **WHEN** a customer submits browser control for an environment they do not own
- **THEN** the API rejects the request without resolving or exposing the environment's account, Edge, or browser state

#### Scenario: Compatible Edge is unavailable
- **WHEN** ownership and binding are valid but no uniquely matched negotiated Edge can receive browser control
- **THEN** the API returns a stable unavailable or unsupported error and MUST NOT fall back to another environment, profile, or reauthorization command
