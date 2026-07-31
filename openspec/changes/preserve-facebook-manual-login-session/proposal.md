## Why

When AdsPower does not fill the unique Facebook login form, Native reports the known business result `credential_fill_unavailable`, but the core currently exits non-zero and the Electron supervisor restarts it as if the process had crashed. That loses CDP control of the still-Active browser and prevents the operator from completing login in the same session.

## What Changes

- Treat unavailable AdsPower credential fill as `manual_login_required`, not as a fatal core-process failure.
- Keep the core, AdsPower browser, and CDP control alive while stopping all automated login actions and polling only for a stable authenticated identity.
- Project one structured local lifecycle notification so the desktop UI shows the exact Facebook login action required and keeps “Show browser” available.
- Continue the existing startup path in place after stable identity is confirmed; do not relaunch or reattach the browser.
- Close and confirm the browser only when the operator explicitly pauses/closes the waiting environment.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-browser-environment`: A known unavailable credential fill enters a controlled manual-login wait and resumes in place after stable identity instead of terminating the core.
- `edge-fleet-console`: The desktop supervisor and fleet UI expose the exact Facebook manual-login reason while retaining browser foreground control.

## Impact

- Affected repo: `aidcp-edge` only.
- Affected areas: Native Facebook auth signals, TypeScript startup auth coordination, local core-to-Electron lifecycle IPC, fleet status projection, renderer wording, and focused tests.
- No Cloud API, protocol-v2, database, Console, deployment, or installer change.
