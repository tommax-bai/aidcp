## 1. Control Repo

- [x] 1.1 Add proposal/design/spec deltas/tasks for reference image usage audit. <!-- aidcp proposal/design/spec deltas/tasks added -->
- [x] 1.2 Validate `reference-image-usage-audit` with `openspec validate --strict`. <!-- 2026-07-05 strict valid -->

## 2. aidcp-cloud

- [x] 2.1 Add reference image audit types to publish metadata and panel DTOs. <!-- cloud src/publish-agent/types.ts + src/panel/panel-store.ts -->
- [x] 2.2 In `PublishExecutor`, build audit from `trigger.generateInput.referenceNote.images` and `imageDirective.referenceImageStatus`, then persist it in `publish_metadata`. <!-- cloud src/publish-agent/roles/publish-executor.ts -->
- [x] 2.3 Project the audit through `PanelStore.publishedHistory`. <!-- cloud panel-store SELECT publish_metadata + parse imageReferenceAudit -->
- [x] 2.4 Add focused tests for unsupported, used, no-reference, and historical null cases. <!-- cloud targeted tests pass: publish-executor 10/10; panel-store 12/12 -->

## 3. aidcp-console

- [x] 3.1 Mirror the new `imageReferenceAudit` DTO. <!-- console src/types/api.ts -->
- [x] 3.2 Display the audit in content detail near the image strip with clear Chinese status text. <!-- console src/pages/ContentPage.tsx -->
- [x] 3.3 Add/extend content page tests for unsupported and historical null display. <!-- console ContentPage targeted test 11/11 pass; jsdom getComputedStyle warnings pre-existing non-fatal -->

## 4. Validation and Closeout

- [x] 4.1 Run relevant cloud tests and typecheck. <!-- aidcp-cloud: target publish-executor 10/10, panel-store 12/12; npm run test:acceptance 44/44; npm test 1344/1344; npm run typecheck passed; npm run build passed -->
- [x] 4.2 Run relevant console tests and typecheck. <!-- aidcp-console: target ContentPage 11/11; npm test 42 passed / 1 skipped; npm run typecheck passed; npm run build passed (assets/index-BufGDWrd.js); jsdom getComputedStyle warnings are non-fatal test-environment noise -->
- [x] 4.3 Update tasks with commit/validation notes and run final OpenSpec strict validation. <!-- commits: aidcp-cloud 24b27a3 pushed to master; aidcp-console 0e60b87 pushed to master. validation: openspec validate reference-image-usage-audit --strict passed. deployment: ECS 121.89.85.150 updated 20260705-154848; backups /opt/aidcp/cloud.bak.20260705-154848.tar.gz, /opt/aidcp/cloud/.env.bak.20260705-154848, /opt/aidcp/console.bak.20260705-154848.tar.gz; synced cloud runtime files with checksum match and console dist assets/index-BufGDWrd.js; aidcp-cloud.service active since 2026-07-05 15:50:03 CST, NRestarts=0; health 8787/8090/8088 listening, /api/health ok, /api/content/published 200 with imageReferenceAudit field, PG select 1 ok, Feishu WS onReady, no recent systemd errors, isales-scheduler/isales-api active. -->
