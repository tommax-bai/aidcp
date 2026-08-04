## Why

Closing a Facebook environment during startup authentication can terminate the Edge core before it asks AdsPower to stop the owned browser. The supervisor then treats the intentional core exit as proof that both resources were closed, leaving the profile active while the UI reports success.

## What Changes

- Route pause/close interruptions received during Facebook startup authentication through one owned-browser teardown that calls the existing confirmed AdsPower close path before the core exits.
- Keep the core alive and report the existing close-failed terminal when the browser cannot be confirmed dead.
- Prevent the Electron supervisor from projecting an intentional core exit as browser-closed unless the child supplied confirmed-close evidence.
- Add focused regressions for an authenticated quiet-window interruption, successful teardown, failed teardown, and supervisor projection.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-browser-environment`: Extend the existing startup/manual-login lifecycle contract so every pause or close interruption during Facebook startup authentication closes and confirms the owned browser before releasing the slot or reporting closed.

## Impact

- `aidcp-edge` startup authentication and local lifecycle handling.
- Electron child-process lifecycle projection and its focused tests.
- No Cloud, protocol v2, risk, database, Console, deployment, dependency, or installer changes.
