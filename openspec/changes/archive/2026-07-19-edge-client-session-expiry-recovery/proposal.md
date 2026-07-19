## Why

The Edge desktop client can restore a customer session that is still valid at
startup but expires before the first four-minute maintenance tick. Startup
opens the main window, the first maintenance tick silently returns because the
session is already invalid, and protected customer APIs then fail locally with
`client_session_required` without returning the client to the login gate.

This was reproduced in dev with a cached session that had about 95 seconds left
when Edge started. The inspiration library request never reached Cloud.

## What Changes

- Refresh a near-expiry customer session during authenticated startup, before
  the main window and environment handles proceed.
- Treat a locally expired customer session as invalid during periodic
  maintenance instead of silently returning.
- When a protected customer-content request observes a locally expired session,
  trigger the existing fail-closed invalidation path and report an expired
  session rather than leaving the stale main window active.
- Add focused regression coverage for near-expiry startup, periodic local
  expiry, and protected-request expiry.

## Impact

- `aidcp-edge`: Electron customer session lifecycle and focused Electron tests.
- No Cloud, console, WebSocket protocol, customer-auth API, or curated-content
  data contract changes.
- Existing invalidation semantics remain authoritative: invalid sessions stop
  all environment handles and return to the login gate.
