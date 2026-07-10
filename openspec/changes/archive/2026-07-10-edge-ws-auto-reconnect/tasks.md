## 1. Edge Cloud Client Lifecycle

- [x] 1.1 Add bounded automatic reconnect to the edge cloud WebSocket client, including intentional-close suppression and pending request failure on disconnect.
  <!-- repo=aidcp-edge commit=d9a444a added bounded cloud WS reconnect with pending failure and intentional-close suppression -->
- [x] 1.2 Re-run `edge.hello` after reconnect and expose connection lifecycle callbacks/logs for reconnecting, reconnected, and exhausted states.
  <!-- repo=aidcp-edge commit=d9a444a reconnect path re-runs hello and emits cloud lifecycle events/logs -->

## 2. Browse Session Recovery

- [x] 2.1 Wire reconnect callbacks into the edge runtime so reconnect success refreshes pacing/session state and asks the browse session to report the current page snapshot.
  <!-- repo=aidcp-edge commit=d9a444a main.ts applies reconnect pacing and calls BrowseSession.recoverAfterCloudReconnect -->
- [x] 2.2 Clear or fail transient command/publish state from the broken connection without replaying stale commands after reconnect.
  <!-- repo=aidcp-edge commit=d9a444a clears queued cloud commands and in-flight publish state on cloud disconnect -->

## 3. Electron Status

- [x] 3.1 Ensure Electron companion status parsing reflects cloud reconnecting/reconnected/exhausted states instead of leaving the UI in a stale running state.
  <!-- repo=aidcp-edge commit=d9a444a Electron log parsing maps reconnecting/exhausted/reconnected cloud states -->

## 4. Verification

- [x] 4.1 Add focused tests for edge client reconnect behavior and intentional close behavior.
  <!-- repo=aidcp-edge commit=d9a444a added edge-client reconnect tests for re-hello, pending failure/no replay, and intentional close -->
- [x] 4.2 Add focused recovery/status tests for the touched runtime or Electron modules.
  <!-- repo=aidcp-edge commit=d9a444a added browse-session cloud reconnect recovery test; existing Electron/UI tests covered by full suite -->
- [x] 4.3 Run edge validation (`npm test`, `npm run test:acceptance`, and `npm run typecheck` where applicable).
  <!-- repo=aidcp-edge commit=d9a444a validation: npm run typecheck passed; npm run test:acceptance passed 13/13; npm test passed 619/619 -->
- [x] 4.4 Run `openspec validate edge-ws-auto-reconnect --strict`.
  <!-- repo=aidcp validation=openspec validate edge-ws-auto-reconnect --strict passed -->
