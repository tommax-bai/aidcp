## 1. Cloud Prompt Preview

- [x] 1.1 Fix `CuratedNoteEvaluator.personaSegments()` to match its rendered prompt exactly, including seed keywords.
  <!-- repo: aidcp-cloud; commit: a044548a92b1a932d6a322844f44f2441d21c9a8; note: personaSegments now matches the actual curated note prompt label and includes seed_keywords. -->
- [x] 1.2 Add optional persona-source metadata and accurate sample/selected/fallback notes to role prompt preview responses.
  <!-- repo: aidcp-cloud; commit: a044548a92b1a932d6a322844f44f2441d21c9a8; note: RolePromptView now carries personaSource/personaSourceLabel and distinguishes sample, selected-account, and fallback-sample notes. -->
- [x] 1.3 Add/update cloud tests for curated note persona segmentation and persona-source notes.
  <!-- repo: aidcp-cloud; commit: a044548a92b1a932d6a322844f44f2441d21c9a8; note: role-prompt-preview and role-prompt-persona-segments tests cover metadata and curated-note highlighting. -->

## 2. Console Prompt Viewer

- [x] 2.1 Update API types for the optional persona-source metadata.
  <!-- repo: aidcp-console; commit: 520c107c5f34e85569f007dc5647702b812475c9; note: RolePromptView mirrors personaSource/personaSourceLabel. -->
- [x] 2.2 Make the role prompt modal surface the preview persona source prominently while keeping fallback warnings explicit.
  <!-- repo: aidcp-console; commit: 520c107c5f34e85569f007dc5647702b812475c9; note: role page now shows a visible Prompt preview persona banner and modal source alert. -->
- [x] 2.3 Add/update console tests for the more visible persona-source UI.
  <!-- repo: aidcp-console; commit: 520c107c5f34e85569f007dc5647702b812475c9; note: promptPersonaSourceSummary unit tests cover sample, selected-account, and fallback cases. -->

## 3. Validation And Closeout

- [x] 3.1 Run targeted cloud role prompt tests and cloud typecheck.
  <!-- validation: npm test was invoked for role prompt files but script expands to full test suite; both full cloud runs passed 1393/1393, and npm run typecheck passed. -->
- [x] 3.2 Run targeted console tests/build/typecheck relevant to the role page.
  <!-- validation: npx vitest run src/pages/rolePromptPersonaSource.test.ts passed 3/3; npm run typecheck passed; npm test passed 54/55 with 1 existing skipped and existing jsdom getComputedStyle noise; npm run build passed. -->
- [x] 3.3 Run `openspec validate improve-role-prompt-persona-preview --strict`.
  <!-- validation: openspec validate improve-role-prompt-persona-preview --strict passed. -->
- [x] 3.4 Commit, push, merge to default branches, deploy dev, and record validation/deployment notes in this task list.
  <!-- repos: aidcp-cloud a044548a92b1a932d6a322844f44f2441d21c9a8 merged/pushed to master; aidcp-console 520c107c5f34e85569f007dc5647702b812475c9 merged/pushed to master. -->
  <!-- deployment: dev target preflight passed; remote backups cloud=/opt/aidcp/backups/cloud-20260706-220745.tgz env=/opt/aidcp/backups/cloud-20260706-220745.env console=/opt/aidcp/backups/console-20260706-220745.tgz. -->
  <!-- dev validation: synced cloud runtime files and console dist; restarted aidcp-cloud.service; active/running, NRestarts=0, ports 8787/8090/8088 listening, /api/version 200, console index and new asset 200, PostgreSQL select 1 passed, Feishu WSClient onReady observed, isales services remained active. -->
