## Why

The environment rail currently treats browser placement as a per-row three-click toggle. When the operator double-clicks a different environment, the first click only selects it, the second click is discarded, and the previously shown browser is only forgotten in renderer state rather than physically returned to its configured parking position. This prevents reliable browser switching across environments.

## What Changes

- Replace the environment-avatar three-click control with two distinct gestures: one click selects an environment; a double-click recalls an unshown environment's browser behind AIDCP or restores the already shown environment to its configured parking position.
- On exclusive recall, return every other controllable environment browser to its own configured parking bounds before completing the target placement.
- Serialize/cancel overlapping recall and restore operations so the latest operator gesture determines whether the target is shown or parked.
- Add correlated completion for browser parking and report target-show failure separately from partial failures to park other browsers; the UI MUST NOT claim an exclusive arrangement that was not completed.
- Keep guided login and explicit recovery controls unchanged: they may continue to place the browser itself in the foreground for manual action.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-companion-ui`: replace the environment rail's three-click control with single-click selection and a double-click recall/restore toggle.
- `edge-fleet-console`: make avatar-triggered recall and shown-target restore latest-request-wins operations that use configured parking plans and report incomplete placement honestly.

## Impact

- `aidcp-edge/src/electron/renderer/renderer.js`: environment-row click/double-click gesture routing and shown-state projection.
- `aidcp-edge/src/electron/preload.cjs` and `src/electron/main.cjs`: targeted exclusive-recall and correlated shown-target restore IPCs with main-process orchestration across live environment handles.
- `aidcp-edge/src/cdp/browser-window.ts`: correlated `browser.park` completion alongside the existing correlated show completion.
- Electron renderer/main/core regression tests and the two modified OpenSpec capabilities.
- No Cloud, protocol v2, risk, publish, browser-slot, packaging, installation, or deployment changes.
