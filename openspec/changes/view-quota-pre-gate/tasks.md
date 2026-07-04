## 1. Spec

- [x] 1.1 Add OpenSpec delta for the `view` pre-dispatch quota gate.
- [x] 1.2 Validate with `openspec validate view-quota-pre-gate --strict`. <!-- 2026-07-05 local: valid -->

## 2. Cloud

- [x] 2.1 Add a `view` quota gate to `RoleDispatcher` before `open_note` dispatch and session starts. <!-- aidcp-cloud 8be807b: src/orchestrator/role-dispatcher.ts adds canView start/open_note gate -->
- [x] 2.2 Wire the gate to each connection's real-account `RiskController.canDo('view')`. <!-- aidcp-cloud 8be807b: src/server.ts buildDispatcher passes ctx.controller.canDo('view') -->
- [x] 2.3 Add focused regression coverage for blocked `open_note` and session ending. <!-- aidcp-cloud 8be807b: test/integration/risk-gating-dispatch.test.ts covers canView=false and edge.hello start block -->
- [x] 2.4 Run targeted tests plus cloud typecheck. <!-- 2026-07-05 local: npx tsx --test test/integration/risk-gating-dispatch.test.ts; npm run test:acceptance; npx tsx --test "test/**/*.test.ts" (1325 pass); npm run typecheck -->

## 3. Release

- [x] 3.1 Commit and push control/cloud changes after validation. <!-- 2026-07-05 local: aidcp-cloud 8be807b pushed to origin/master; aidcp 4ec576c pushed to origin/main -->
- [x] 3.2 Deploy cloud from the default branch snapshot and run production healthchecks if runtime changes are accepted. <!-- 2026-07-05 07:47 CST: archived aidcp-cloud HEAD to /opt/aidcp/cloud; backup /opt/aidcp/backups/cloud.bak.20260705-074730.tar.gz and /opt/aidcp/backups/cloud.env.bak.20260705-074730; aidcp-cloud.service active; ports 8787/8090 listening; Feishu ws ready; pg select 1 ok -->
