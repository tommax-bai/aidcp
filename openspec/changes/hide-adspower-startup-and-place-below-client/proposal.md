## Why

AdsPower cold starts can briefly paint a maximized browser on the operator's primary screen before AIDCP receives the dynamic CDP port and parks the window. Separately, showing a browser from the environment rail currently raises it above the AIDCP client, hiding the control surface the operator is using.

## What Changes

- Give every parked-browser cold start a machine-local right-side staging position and stop passing `--start-maximized` when that position is available, while retaining the fixed desktop size and authoritative CDP correction.
- Keep the staging position separate from the operator-selected final parking position, so the browser can start out of view and then settle into `primary-screen`, `parking-display`, `edge-strip`, or `offscreen` after attach and verification.
- Change the environment-avatar show action to center the driven browser on the AIDCP client's current window frame, then restore the AIDCP client as the foreground window instead of leaving the browser above it or offset at the primary-screen inspection position.
- Preserve honest failure behavior: unsupported/clamped staging remains best-effort, failed show/park commands do not advance the rail phase, and page visibility/desktop viewport verification still gates automation.

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `pluggable-browser-provider`: refine parked browser launch arguments and the pre-attach staging contract.
- `edge-companion-ui`: keep AIDCP above the driven browser after the environment-avatar show gesture.
- `edge-fleet-console`: change browser-window show semantics from browser-foreground focus to visible placement below the AIDCP control surface.

## Impact

- `aidcp-edge/src/electron/browser-parking.cjs` and Electron spawn wiring: compute and inject separate startup staging and final parking bounds.
- `aidcp-edge/src/cdp/browser-provider.ts` and browser-window control: remove parked-launch maximization and accept explicit show bounds.
- `aidcp-edge/src/electron/main.cjs`: derive a browser target centered on the current AIDCP window frame, send it with the show request, and restore the AIDCP main window to foreground after completion.
- Focused provider, parking, Electron main/renderer, and acceptance coverage; no cloud protocol, database, dependency, installer, or deployment change.
