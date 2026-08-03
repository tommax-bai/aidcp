## Why

Operators can select Facebook cold-start mode but cannot correct which cold-start day an environment is on or explicitly mark the lifecycle complete from the desktop client. This leaves account recovery and imported-history cases dependent on direct backend intervention and makes the client unable to express the intended Cloud-authoritative state.

## What Changes

- Add compact "current day" and "completed" controls immediately after the Facebook primary browse surface in the desktop client.
- Show those controls only when the confirmed operation mode is `slow_start`; keep them hidden for other modes, unknown reads, and non-Facebook environments.
- Add an environment-scoped progress read/write surface that preserves the existing operation-policy response shape, adjusts the persisted slow-start anchor and completion fact atomically, and returns authoritative progress plus operation-policy projections.
- Keep pending, conflict, failure, and cross-environment responses honest: the client retains the last confirmed state until Cloud write-after-read confirms the requested progress.
- Reuse the configured global cold-start duration as the day bound and the existing completion table; do not add a second Edge-local progress authority or a new database table.

## Capabilities

### New Capabilities

- `client-facebook-slow-start-progress`: Client presentation and Cloud-authoritative read/write semantics for correcting an environment's Facebook cold-start day and completion status.

### Modified Capabilities

None.

## Impact

- `aidcp-cloud`: customer-auth routing, Facebook operation-policy projection/store, mirror refresh, and focused API/store tests.
- `aidcp-edge`: renderer markup/styles/state, preload/main IPC, customer-auth request validation, and renderer/contract tests.
- No protocol-v2 command change, new dependency, new table, OL deployment, or Edge installer is required.
