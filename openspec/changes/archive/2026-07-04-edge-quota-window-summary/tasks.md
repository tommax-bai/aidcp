## 1. Specification

- [x] Add OpenSpec delta for multi-window quota status in the Electron companion.
- [x] Validate the OpenSpec change with `openspec validate edge-quota-window-summary --strict`.

## 2. Cloud

- [x] Extend protocol types with optional quota windows while preserving daily aliases. <!-- aidcp-cloud d8fed2f src/comm/protocol.ts -->
- [x] Add risk-store and publish-log reads for minute/hour/day account windows. <!-- aidcp-cloud d8fed2f src/risk/pg-risk-store.ts + src/publish-agent/publish-log-store.ts -->
- [x] Expose active session budget usage from the per-connection dispatcher/registry. <!-- aidcp-cloud d8fed2f src/orchestrator/role-dispatcher.ts + connection-runtime.ts -->
- [x] Include `session`, `minute`, `hour`, and `day` windows in `ui.snapshot.dailyUsage`. <!-- aidcp-cloud d8fed2f src/server.ts + src/comm/ui-snapshot.ts -->
- [x] Add or update cloud tests for the new snapshot payload and window aggregation. <!-- aidcp-cloud d8fed2f test/comm/ui-snapshot.test.ts + test/session-effective-limits.test.ts -->

## 3. Edge And Electron

- [x] Sync protocol definitions and forward windowed quota data in structured `[ui-event]` lines. <!-- aidcp-edge 1abefdf src/comm/protocol.ts + src/flows/ui-event-lines.ts -->
- [x] Normalize windowed quota data in Electron main process while keeping older daily-only payloads working. <!-- aidcp-edge 1abefdf src/electron/main.cjs -->
- [x] Render the quota-window strip and aggregate status chip in the daily summary card. <!-- aidcp-edge 1abefdf renderer index/js/css -->
- [x] Add or update edge/Electron tests for window rendering and backward compatibility. <!-- aidcp-edge 1abefdf test/flows/ui-event-lines.test.ts + test/electron/companion-ui.test.ts -->

## 4. Documentation, Validation, Release

- [x] Update protocol documentation. <!-- aidcp docs/protocol.md documents dailyUsage.windows and compatibility aliases -->
- [x] Run relevant cloud and edge tests/typechecks. <!-- openspec validate edge-quota-window-summary --strict; cloud npm run typecheck + targeted + acceptance + full test; edge npm run typecheck + targeted + acceptance + full test; cloud rebase retest: npm run typecheck + targeted 16/16 -->
- [x] Commit and push control/cloud/edge changes. <!-- aidcp-cloud d8fed2f pushed to origin/master; aidcp-edge 1abefdf pushed to origin/master; aidcp control commit/push contains this OpenSpec archive + protocol doc -->
- [x] Deploy cloud runtime if server behavior changed and verify production health. <!-- 2026-07-04 22:10 CST clean archive deploy from origin/master d8fed2f; backup /opt/aidcp/cloud.bak.20260704-221002.tar.gz and /opt/aidcp/cloud.env.bak.20260704-221002; aidcp-cloud.service active; 8787/8090 listening; Feishu WS ready; PG select 1 ok; online code anchors confirmed -->
