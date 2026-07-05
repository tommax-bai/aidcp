## 1. OpenSpec

- [x] 1.1 Specify Wanxiang reference-image generation semantics. <!-- control: proposal + publish-multi-image spec delta added. -->
- [x] 1.2 Validate `wanxiang-reference-image-generation` with `openspec validate --strict`. <!-- passed locally. -->

## 2. aidcp-cloud

- [x] 2.1 Update `WanxiangClient` to submit reference image URLs as Wan 2.7 image content when `referenceImages` are present. <!-- aidcp-cloud 8b30ccb: submit body now sends image content before text content. -->
- [x] 2.2 Mark reference status honestly: `used` only on successful image-input generation, `unavailable` on reference-path failures, no status for ordinary text-only generation. <!-- aidcp-cloud 8b30ccb. -->
- [x] 2.3 Keep Seedream reference handling unsupported until the official request shape is confirmed. <!-- no Seedream support flag changed; current unsupported audit remains honest. -->
- [x] 2.4 Add focused tests for text-only zero regression, reference request body, successful `used`, and failed `unavailable`. <!-- validation: npx tsx --test test/publish-agent/wanxiang-client.test.ts passed (9 tests). -->

## 3. Closeout

- [x] 3.1 Run focused cloud tests and typecheck/build. <!-- validation: focused Wanxiang tests passed; npm run typecheck passed; npm run build passed; npm test passed (1360). -->
- [x] 3.2 Commit and push control/cloud changes. <!-- aidcp-cloud 8b30ccb pushed to master; control commit pending after this task update. -->
- [x] 3.3 Deploy cloud if validation passes; switch production image provider only if the user wants Wanxiang to be the active reference-image path now. <!-- deployed 2026-07-05 17:30 CST from aidcp-cloud master 8b30ccb: backup /opt/aidcp/backups/aidcp-cloud-20260705-173046.tgz + env /opt/aidcp/backups/aidcp-cloud-20260705-173046.env; rsync src/publish-agent/wanxiang-client.ts; service active since 17:30:49; code sha256 matched local. Production image config switched to dashscope/wan2.7-image at 17:32 CST after backing up /opt/aidcp/backups/model_config-20260705-173218.sql; restart active since 17:32:18. Health: NRestarts=0, ports 8787/8090/8088 listening, /api/health ok, /api/version ok, PG select 1 ok, Feishu WSClient onReady, no recent systemd errors, isales-scheduler/isales-api active. -->
