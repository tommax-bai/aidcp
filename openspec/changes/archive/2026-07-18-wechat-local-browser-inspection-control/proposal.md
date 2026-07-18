## Why

The video-channel interaction workspace currently treats browser foreground control as an engine-owned action: the button is shown only after WeChat authentication is active and sends a Cloud request that requires an online Edge engine. Operators also need a simpler local action to inspect the login page or backend data even when the engine is stopped or disconnected.

## What Changes

- Make engine connectivity and WeChat Channels authentication the two primary status signals in the interaction workspace.
- Move browser state into a secondary "manual inspection" area so an unconfirmed browser state does not look like the main blocker.
- Replace the workspace browser button with a local desktop action that opens the selected AdsPower profile directly from the Electron main process.
- Keep the local action independent from Cloud delivery and the environment engine lifecycle: it MUST NOT start, resume, pause, or otherwise mutate the engine.
- Revalidate the selected environment against the current customer-visible WeChat Channels scope in the main process; the renderer cannot provide a profile id, URL, API base, token, or launch arguments.
- Keep browser opening non-authoritative for WeChat authentication. The UI continues to report authentication only from the engine/Cloud projection.

## Capabilities

### New Capabilities

- `wechat-local-browser-inspection-control`: narrow local AdsPower browser opening for manual inspection without an online engine.

### Modified Capabilities

- `edge-companion-ui`: the video-channel overview prioritizes engine and WeChat authentication, while browser state and manual opening are secondary.

## Impact

- `aidcp-edge` Electron main/preload IPC, AdsPower local API client, video-channel interaction renderer, focused tests, and renderer styling.
- No Cloud API, database, interaction protocol, or console change.
- No installer build or runtime deployment is required; the change ships with the next desktop client build.
- This supersedes the interaction workspace's Cloud-routed open/close button from `wechat-channels-browser-foreground-control`; the existing Cloud endpoint remains compatible but is no longer the manual inspection UI path.
