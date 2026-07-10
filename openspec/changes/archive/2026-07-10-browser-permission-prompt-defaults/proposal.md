## Why

The fingerprint browser launched for automated browsing still surfaces native permission prompts (e.g. the "allow notifications" dialog), which interrupt automated interaction and require manual dismissal on the operator machine. The only permission policy in the client today is installed on the Electron companion window (`installPermissionPolicy`, added for geolocation): it governs a different browser surface and has no effect on the separately-launched fingerprint Chrome. That same Electron-window policy also over-blocks the client's own notifications, which the companion UI needs in order to surface status to the operator.

## What Changes

- Suppress permission prompts in the driven fingerprint browser for both AdsPower and self providers, so no permission dialog (notifications, geolocation, camera, microphone, …) interrupts automated browsing:
  - Pass `--deny-permission-prompts` at launch (race-free for fresh launches; auto-denies all permission types without removing any web API, so it stays detection-clean).
  - Add a CDP `Browser.setPermission … denied` backstop in the shared attach path so **reused** browser instances and reconnects are also covered — the launch flag cannot reach an already-running browser (AdsPower may hand back a live profile; self reuses an already-open CDP port).
- Restore the Electron companion window's own notifications: keep `notifications` allowed while continuing to deny device-access permissions (geolocation, camera, microphone, …). Only the fingerprint browser is silenced.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pluggable-browser-provider`: the driven browser denies permission prompts by default at launch and via a CDP backstop after attach, for both providers and across reconnects.
- `edge-companion-ui`: the companion window permission policy allows the client's own notifications while continuing to deny device-access permissions.

## Impact

- Affected repo: `aidcp-edge`.
- Affected areas:
  - AdsPower and self provider launch args (`src/cdp/browser-provider.ts`, `src/cdp/chrome-launcher.ts`).
  - CDP attach path (`src/cdp/session.ts` `reEnableAndInject`), applied on first attach and on reconnect.
  - Electron companion window permission policy (`src/electron/main.cjs`).
- No cloud protocol change and no ECS deployment required. Edge desktop runtime behavior only; the operator machine must pull/rebuild for it to take effect.
