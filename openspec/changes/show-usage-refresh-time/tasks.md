## 1. Spec

- [x] 1.1 Create OpenSpec proposal, design, and `edge-companion-ui` spec delta.
- [x] 1.2 Validate `show-usage-refresh-time` with `openspec validate --strict`. <!-- 2026-07-05 local: valid -->

## 2. Cloud

- [x] 2.1 Extend `UiDailyUsageWindowStatus` with optional `refreshAt` and `releaseAt`.
- [x] 2.2 Add a read-only risk-controller helper for per-action/per-window quota release timing.
- [x] 2.3 Populate daily usage window timing in cloud snapshots.
- [x] 2.4 Schedule best-effort targeted daily-usage refresh snapshots for online edges.
- [x] 2.5 Add focused cloud regression coverage.

## 3. Edge

- [x] 3.1 Mirror the protocol timing fields in edge.
- [x] 3.2 Preserve timing fields through `ui.snapshot` sanitization and Electron main-process normalization.
- [x] 3.3 Render release/refresh hints in the expanded daily usage window UI.
- [x] 3.4 Add focused edge regression coverage.

## 4. Validation And Release

- [x] 4.1 Run relevant cloud tests and typecheck. <!-- 2026-07-05 local: focused npx tsx --test test/risk-controller.test.ts test/comm/ui-snapshot.test.ts (25 pass); npm run test:acceptance (44 pass); npm test (1346 pass); npm run typecheck; openspec strict valid -->
- [x] 4.2 Run relevant edge tests and typecheck. <!-- 2026-07-05 local: focused npx tsx --test test/flows/ui-event-lines.test.ts test/electron/companion-ui.test.ts (40 pass); npm run test:acceptance (13 pass); npm test (615 pass); npm run typecheck -->
- [x] 4.3 Update task notes with commits, validation, and deployment/publish outcome.
  <!-- aidcp 4ea9dda created OpenSpec artifacts; aidcp-cloud e0c4a9f pushed to origin/master and deployed 2026-07-05 16:38 CST from clean origin/master archive to /opt/aidcp/cloud; backup /opt/aidcp/backups/cloud.bak.20260705-163803.tar.gz and /opt/aidcp/backups/cloud.env.bak.20260705-163803; health active, 8787/8090 listening, Feishu WS ready, PG select 1 ok, /api/health ok, remote source contains refreshAt/quotaReleaseAfterMs/dailyUsage刷新, isales-api/isales-scheduler/isales-engine active. aidcp-edge eb12ac7 pushed to origin/master; desktop package not published because no release target was specified. -->
