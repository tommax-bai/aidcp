## Why

When the edge process exits abnormally, the desktop app currently surfaces the actionable reason mainly through a transient notification and generic status text. If that notification is dismissed, operators lose the specific recovery reason, such as an AdsPower profile being locked by another account.

## What Changes

- Persist and display the latest abnormal edge-process failure details inside the Electron companion window.
- Keep the existing notification behavior, but make it secondary to an in-app status surface that remains visible after notifications are dismissed.
- Include the honest underlying error text from the edge process where available, while preserving concise human-readable status labels.
- Clear stale failure details when the operator starts, restarts, pauses, or successfully runs a fresh edge process.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `edge-companion-ui`: abnormal edge-process failures must remain visible in the client UI after transient notifications disappear.

## Impact

- Affected repo: `aidcp-edge`
- Affected areas: Electron main process status state, renderer status rendering, UI tests.
- No protocol, cloud API, database, or deployment contract changes.
