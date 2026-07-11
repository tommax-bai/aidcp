## 1. OpenSpec

- [x] 1.1 Create proposal, design, and spec delta for platform settings redesign.
- [x] 1.2 Validate `redesign-platform-settings-page` with `openspec validate --strict`.
  <!-- local: openspec validate redesign-platform-settings-page --strict passed before implementation. -->

## 2. aidcp-console

- [x] 2.1 Work in a clean console worktree/branch for this change.
  <!-- aidcp-console worktree: ../aidcp-console.wt/redesign-platform-settings-page on codex/redesign-platform-settings-page from origin/master. -->
- [x] 2.2 Redesign `SettingsPage` layout and copy for platform configuration.
- [x] 2.3 Make credential inputs use stable independent state and autofill-safe field metadata.
- [x] 2.4 Add a focused SettingsPage regression test for AccessKey ID/Secret input independence.

## 3. Validation and Release

- [x] 3.1 Run focused console tests for SettingsPage.
  <!-- aidcp-console worktree: npm test -- src/pages/SettingsPage.test.tsx passed. -->
- [x] 3.2 Run full console validation (`npm test` and `npm run build`).
  <!-- aidcp-console worktree after rebase to origin/master 0e60b87: npm test -- src/pages/SettingsPage.test.tsx passed; npm test passed (43 passed, 1 skipped); npm run build passed. Existing jsdom getComputedStyle warnings and Vite chunk-size warning only. -->
- [x] 3.3 Update this task list with commits, validation, and deployment notes.
  <!-- commits: aidcp-console 2b5d43a pushed to master. -->
  <!-- validation: openspec validate redesign-platform-settings-page --strict passed; aidcp-console npm test -- src/pages/SettingsPage.test.tsx passed; npm test passed (43 passed, 1 skipped); npm run build passed. -->
  <!-- deployment: ECS 121.89.85.150 console static release updated 20260705-155617; backup /opt/aidcp/console.bak.20260705-155617.tar.gz; rsync dist/ to /opt/aidcp/console; health: 8088 / 200, /settings 200, /api/health 200, index references assets/index-LuKGWiGs.js, bundle contains 保存规则, aidcp-cloud active, isales-scheduler/isales-api active. -->
- [x] 3.4 Commit, push, and deploy the console static release if validation passes.
