## 1. Persona Unbind

- [x] 1.1 Update cloud persona write path so empty persona saves unbind the account and return `source=none` truth state.
  <!-- aidcp-cloud c978588: empty persona PUT now clears the binding row and returns source=none; onBound is only triggered by real non-empty bindings. -->
- [x] 1.2 Update console persona page so clearing the editor can be saved as unbind without client-side required blocking.
  <!-- aidcp-console 4313874: removed local empty-content block, updated copy, and shows unbind success when source=none is returned. -->
- [x] 1.3 Add cloud and console tests for clear-and-save unbind behavior.
  <!-- aidcp-cloud c978588 / aidcp-console 4313874: persona facade, acceptance, and PersonaPage tests cover clear-and-save unbind. -->

## 2. Startup Nickname Refresh

- [x] 2.1 Update cloud nickname persistence policy so verified non-empty startup nicknames update when different from the stored nickname.
  <!-- aidcp-cloud c978588: nickname capture compares stored nickname before setNickname; same nickname is no-op, different nickname updates. -->
- [x] 2.2 Ensure XHS startup nickname capture runs on each task startup where a verified nickname can be read, not only when the stored nickname is empty.
  <!-- aidcp-cloud c978588: XHS connections keep pending nickname refresh armed for startup capture; FB remains on hello nickname path. -->
- [x] 2.3 Ensure Facebook startup handshake nickname updates existing stored nickname when verified and different.
  <!-- aidcp-cloud c978588: FB accountNickname from validated hello overwrites different stored nicknames and skips same-name writes. -->
- [x] 2.4 Add tests covering empty/no-op nickname cases and changed-nickname updates.
  <!-- aidcp-cloud c978588: nickname enricher and connection runtime tests cover empty, same-name no-op, and changed-name update. -->

## 3. Validation And Closeout

- [x] 3.1 Run targeted cloud, console, and edge validation for the touched paths.
  <!-- Validation: aidcp-cloud targeted tsx tests passed; aidcp-cloud npm test passed 1883 tests; aidcp-cloud npm run typecheck passed; aidcp-console targeted vitest passed; aidcp-console npm run typecheck and npm run build passed; aidcp-edge had no source change and npm run typecheck passed. Dev deploy health passed: aidcp-cloud.service active, 8787/8090/8088 listening, /api/health 200, PG ready, Feishu WSClient onReady, isales services still active. -->
- [x] 3.2 Run `openspec validate unbind-persona-refresh-nickname --strict`.
  <!-- Validation: openspec validate unbind-persona-refresh-nickname --strict passed. -->
- [x] 3.3 Commit and push relevant repo changes; update this task file with commits and validation notes.
  <!-- Pushed to default branches: aidcp-cloud master c978588; aidcp-console master 4313874; aidcp main 911def2 plus deployment-note follow-up. Deployed dev from clean master worktrees. Backups: /opt/aidcp/cloud.bak.20260712-201902.tar.gz, /opt/aidcp/cloud/.env.bak.20260712-201902, /opt/aidcp/console.bak.20260712-201919.tar.gz. -->
