## Why

When an account hits a minute or hour quota, the Electron companion can keep showing "有一会儿没有新动态了" after the last event becomes stale. That copy makes a quota pause look like missing source activity instead of an intentional safety rest.

## What Changes

- Update the Electron presence copy for running sessions with a current saturated quota window.
- Show the saturated action/window and remaining wait time when the cloud-supplied window metadata supports it.
- Keep the existing "没有新动态" fallback when there is no fresh quota saturation evidence.
- No protocol shape change; reuse existing `ui.snapshot.dailyUsage.windows`.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-companion-ui`: Electron presence text distinguishes quota-driven rest/wait states from generic stale activity.

## Impact

- `aidcp-edge` Electron renderer logic and tests.
- `aidcp` OpenSpec delta for `edge-companion-ui`.
- No cloud, console, database, or wire-protocol change.
