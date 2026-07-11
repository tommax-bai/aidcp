## Why

When `aidcp-cloud.service` restarts cleanly, the edge core can keep running while its cloud WebSocket is closed. Electron then still looks alive locally, but the cloud has no online edge and the browse loop stops without a clear operator action path.

## What Changes

- Add first-class cloud WebSocket reconnect handling inside the edge core.
- Re-run the cloud hello/session handshake after reconnect without treating the old socket state as still valid.
- Reset transient command state and re-report the current page snapshot so cloud can resume decisions from observed reality.
- Surface reconnecting/reconnected/exhausted states through existing edge logs and Electron status parsing.
- Fail or drop in-flight work from the broken connection conservatively; do not replay stale cloud commands or fabricate success.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `browse-loop-resilience`: edge must self-heal from unexpected cloud WebSocket closure, or terminate honestly when reconnect is exhausted.

## Impact

- Affected repo: `aidcp-edge`
- Affected areas: edge cloud client lifecycle, browse session recovery hooks, Electron status/log mapping, focused edge tests.
- No cloud protocol shape, database schema, or risk-state ownership changes.
