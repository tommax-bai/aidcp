## Why

Dev logs showed an account in long quota wait repeatedly reconnecting and replaying the startup timeline after browser cold standby. Cold standby is intended to be a parked state that keeps the engine/cloud lifecycle stable; it must not degrade into browser restart/login loops or repeated nickname capture.

## What Changes

- Keep cold standby as an intentional standby state when cloud WebSocket reconnects are exhausted; do not turn that condition into a core recycle that restarts the browser.
- Ensure the Electron supervisor does not classify cold-standby child exits as ordinary abnormal exits that should respawn the browser immediately.
- Narrow XHS nickname capture to the first `page.cards` after a full browser startup/restart, once per browser generation.
- Prevent cloud hello/reconnect, cold-standby cloud recovery, and existing-nickname reconnects from arming nickname capture.
- Preserve honest operator visibility: standby remains standby, with cloud reconnect as an internal standby substate rather than a generic failure/login loop.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-node-supervised-recycle`: cold standby child/cloud reconnect failures must not be treated as ordinary recycle triggers that restart the browser.
- `edge-companion-ui`: cold standby must remain visible as standby while cloud connectivity recovers, without replaying startup activity as if a new browsing round began.
- `account-identity-resolution`: nickname capture must be scoped to first feed readiness after a complete browser start/restart, not every cloud hello/reconnect.

## Impact

- Affected repos: `aidcp-edge`, `aidcp-cloud`, and OpenSpec artifacts in `aidcp`.
- Edge affected areas: core cloud reconnect handling, Electron cold-standby/respawn state, lifecycle tests.
- Cloud affected areas: dispatcher nickname-capture arming and nickname enricher tests.
- Runtime impact: cloud changes deploy to dev; edge code is committed/pushed but does not produce a desktop installer unless explicitly requested.
