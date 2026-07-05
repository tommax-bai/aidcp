## 1. OpenSpec

- [x] 1.1 Create proposal, design, and spec delta for platform credential configuration.
- [x] 1.2 Validate `platform-provider-credentials-config` with `openspec validate --strict`.
  <!-- local: openspec validate platform-provider-credentials-config --strict passed before implementation. -->

## 2. aidcp-cloud

- [x] 2.1 Add a platform credential registry that includes model API keys and Alibaba/Volcengine platform AccessKey pairs.
- [x] 2.2 Replace the config credential write whitelist with the platform credential registry.
- [x] 2.3 Extend `GET /api/config/model` credential view with platform credential metadata and configured state.
- [x] 2.4 Make billing price refresh read generic platform AccessKey fallbacks while preserving existing specific/env fallbacks.
- [x] 2.5 Adjust panel tests and billing-refresh tests for platform credentials.
  <!-- aidcp-cloud worktree: npx tsx --test test/panel-config.test.ts test/billing-price-refresh.test.ts passed; npm run build passed. -->

## 3. aidcp-console

- [x] 3.1 Rename the settings page positioning from model config to platform config.
- [x] 3.2 Render model/provider controls as a section and platform credentials as grouped editable rows.
- [x] 3.3 Update TypeScript API types and user-facing credential labels, including billing missing-credential labels.
- [x] 3.4 Run console tests/build for the changed UI.
  <!-- aidcp-console worktree: npm test passed (40 passed, 1 skipped); npm run build passed. -->

## 4. Closeout

- [x] 4.1 Run cloud validation relevant to config and billing refresh.
  <!-- validation: aidcp-cloud npm test passed (1342 tests); npm run build passed; aidcp-console npm test passed (40 passed, 1 skipped); npm run build passed; openspec validate platform-provider-credentials-config --strict passed. -->
- [x] 4.2 Update this tasks file with commit, validation, and deployment notes.
  <!-- commits: aidcp-cloud 72be2bf pushed to master; aidcp-console 57f8009 pushed to master. -->
  <!-- validation: aidcp-cloud npm test passed (1342 tests) + npm run build; aidcp-console npm test passed (40 passed, 1 skipped) + npm run build; openspec validate platform-provider-credentials-config --strict. -->
  <!-- deployment: ECS 121.89.85.150 updated 20260705-153621; backups cloud.bak.20260705-153621.tar.gz, cloud.env.bak.20260705-153621, console.bak.20260705-153621.tar.gz. Health: aidcp-cloud active since 2026-07-05 15:36:41 CST, :8787 listening, /api/health ok, PG select 1 ok, Feishu WS onReady, console 8088 HTTP 200, console bundle contains 平台配置, isales-scheduler/isales-api active. -->
- [x] 4.3 Commit, push, and deploy cloud/console if validation passes.
