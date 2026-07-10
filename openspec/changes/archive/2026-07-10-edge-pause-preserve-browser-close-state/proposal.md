## Why

The desktop client currently implements “pause” by terminating the edge core, and the core shutdown path also stops the owned browser. Operators therefore lose the browser window and login context when they only intended to stop automation temporarily, while the UI has no distinct state or action for explicitly closing the browser.

## What Changes

- Change the desktop pause lifecycle so automation and cloud participation stop cleanly while the owned browser remains open.
- Add an explicit close action and an honest “closed” session state; only this close action (or application shutdown/removal/recycle) closes the owned browser.
- Resume a paused environment by reusing its retained browser and restarting the edge core without opening a second browser instance.
- Keep pause, resume, close, bulk controls, app shutdown, and multi-environment status projections isolated per environment.
- Add lifecycle and renderer tests covering browser retention, explicit close, state labels, and control visibility.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-companion-ui`: Extend the session control and status contract with a paused-browser state, an explicit close action, and an honest closed state.
- `pluggable-browser-provider`: Distinguish temporary automation deactivation from final owned-browser shutdown while preserving the provider ownership boundary.

## Impact

- `aidcp-edge` Electron supervisor, preload IPC bridge, renderer controls/state projection, and lifecycle tests.
- `aidcp-edge` core shutdown coordination and browser-provider ownership semantics.
- No cloud protocol or persistence schema change is required; lifecycle control remains local to each desktop environment.
