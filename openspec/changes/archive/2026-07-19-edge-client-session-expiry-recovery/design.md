## Context

Customer JWTs default to a 15-minute lifetime. Edge maintenance runs every four
minutes and refreshes tokens with less than five minutes remaining. However,
`proceedAfterAuth()` currently refreshes only the visible environment scope, not
the token itself. A restored token can therefore be valid at startup yet expire
before the first interval callback. The callback begins with
`!hasValidSession() -> return`, contradicting the lifecycle comment and leaving
the main window in a stale authenticated state.

## Goals / Non-Goals

**Goals:**

- Close the startup timing gap without changing token lifetime or server APIs.
- Reuse the existing `onSessionInvalid()` fail-closed teardown and login gate.
- Preserve transient-network behavior while a token is still locally valid.
- Keep the change small and test the exact ordering invariants.

**Non-Goals:**

- Change customer JWT TTL, refresh endpoint semantics, or credential storage.
- Keep environments running after authentication is invalid.
- Add a new login UI or change curated-content behavior.

## Decisions

### D1 - One refresh helper is shared by startup and maintenance

Extract the existing near-expiry refresh block into a bounded helper. Startup
calls it before scope refresh and before creating the main window. Periodic
maintenance calls the same helper before refreshing scope. A successful refresh
replaces the persisted token using the existing encrypted storage path; a 401
uses the existing invalidation path.

A transient non-401 refresh failure does not immediately destroy a still-valid
session. Scope refresh retains its existing fail-closed/network behavior, and a
later maintenance tick invalidates the client once local expiry is reached.

### D2 - Local expiry is an authentication failure, not a no-op

When customer auth is enabled and maintenance sees no locally valid session, it
must call `onSessionInvalid()` and stop. This restores the documented invariant:
invalid authentication tears down environment handles and returns to the login
gate.

### D3 - Protected content requests close the stale-window gap immediately

`delegatedTaskRequest()` distinguishes disabled authentication from an expired
local session. For local expiry it invokes `onSessionInvalid()` and returns
`client_session_expired`. This prevents a user action during the interval window
from producing only a retryable inspiration-library error while the stale main
window remains open.

## Risks / Trade-offs

- Calling the existing invalidation path stops all environment processes. This
  is intentional and already required by the customer-auth lifecycle contract.
- Startup adds at most one bounded refresh request when the cached token is near
  expiry. Normal fresh sessions incur no extra refresh request.
- Source-contract tests are used because `main.cjs` has Electron top-level side
  effects and is not safely importable in unit tests; assertions lock the call
  order and fail-closed branches.
