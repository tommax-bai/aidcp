## Why

AdsPower browser windows currently open in the foreground and interfere with the operator's normal desktop use. We need a low-disruption desktop setting that keeps the browser headful and visible to the OS, while avoiding minimized/headless states that raise page-visibility and anti-detection risk.

## What Changes

- Add a browser window parking setting to the Electron companion settings drawer with three modes:
  - `parking-display`: prefer a non-primary display when one is available.
  - `edge-strip`: keep the browser mostly off the primary display while leaving a small visible strip for recovery.
  - `offscreen`: move the browser fully outside the primary display as an advanced mode.
- Persist the selected parking mode with existing local desktop settings and inject it into the spawned edge core process.
- Extend the edge browser attach path to apply window parking after CDP attach and verify the page remains visible and at the required desktop viewport size.
- Add honest fallback behavior: if the preferred mode cannot be verified, degrade to `edge-strip` or keep the browser in a recoverable visible position rather than continuing in a hidden/broken state.
- Add operator recovery affordances in the client for showing/resetting the parked browser window.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-companion-ui`: adds a persisted browser parking setting in the desktop settings drawer and recovery controls.
- `pluggable-browser-provider`: adds browser window parking behavior below the provider layer without changing provider selection or browser lifecycle ownership.

## Impact

- Affected repo: `aidcp-edge`.
- Affected areas:
  - Electron main process settings/env injection and tray/menu IPC.
  - Electron renderer settings drawer UI and smoke tests.
  - CDP browser/window utility logic after page attach.
  - Browser provider launch args for early AdsPower positioning hints.
- No cloud protocol change and no ECS deployment required.
- No production cloud behavior change; this is an edge desktop runtime behavior change.
