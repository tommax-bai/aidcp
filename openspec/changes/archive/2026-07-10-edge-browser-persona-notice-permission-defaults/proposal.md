## Why

Accounts can become logged in and cloud-connected without a bound persona, but the current client does not reliably force that setup into view and its preference model is too coarse. An operator working in the driven AdsPower browser can also miss the client prompt, while newly created profiles leave geolocation permission at the browser default and can surface native prompts that interrupt automation.

## What Changes

- Automatically open the Electron persona setup dialog and emit one desktop notification for each unresolved logged-in, cloud-connected account without a persona.
- Replace the persona keyword form with two panels: `语气调性` followed by grouped `内容偏好`, with `招聘求职` first and the requested second-level interests.
- Allow each content-preference group to accept bounded custom interests that participate in persona generation.
- Show an AIDCP-owned persona reminder inside the controlled browser page when the environment is logged in, connected to cloud, and not bound to a persona.
- Remove the controlled-page reminder as soon as the account becomes persona-bound, and keep the injected UI isolated from the site's DOM and automation selectors.
- Deny unnecessary sensitive permission requests in the Electron app window and surface the denial honestly.
- Configure newly created AdsPower profiles with geolocation permission set to `block` while retaining IP-based location fingerprint behavior.
- Add focused tests for browser-page reminder lifecycle, environment routing, and the AdsPower `fingerprint_config` payload.

## Capabilities

### New Capabilities

<!-- None. -->

### Modified Capabilities

- `edge-companion-ui`: Define automatic persona prompting, the two-panel preference editor, custom interests, controlled-page reminder lifecycle, and honest Electron permission handling.
- `adspower-environment-provisioning`: Require newly created AdsPower profiles to default geolocation permission to block without disabling IP-based fingerprint location.

## Impact

- Code: `../aidcp-edge/src/electron/main.cjs`, preload and renderer assets, `../aidcp-edge/src/cdp/browser-window.ts`, `../aidcp-edge/src/electron/ads-fingerprint.cjs`, focused edge tests, and `../aidcp-console/src/config/downloads.ts` for the published package version.
- Protocol: no edge-cloud message type changes; the Electron-to-core stdin control channel gains a local `browser.personaNotice` command.
- Existing AdsPower profiles are unchanged; only new `user/create` payloads receive the permission default.
- Release: requires rebuilding and publishing the Electron desktop package; no cloud runtime deployment is required.
