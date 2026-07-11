## 1. Preview Coverage

- [x] 1.1 Add preview-only instances/adapters for command-style comment search roles so catalogued browse roles can render prompts even when absent from RoleDispatcher.
  <!-- repo: aidcp-cloud; commit: 40f11d9; note: preview-only CommentSearchTermGenerator/CommentTargetPicker instances are supplied to the provider without registering them in RoleDispatcher. -->
- [x] 1.2 Add publish preview builders for TopicGenerator and TopicEvaluator using their existing prompt builder functions.
  <!-- repo: aidcp-cloud; commit: 40f11d9; note: added buildTopicGenerationPrompt/buildTopicEvaluationPrompt coverage to publish preview registry. -->
- [x] 1.3 Make publish prompt preview accept an optional account persona and fall back honestly to sample persona for unbound accounts.
  <!-- repo: aidcp-cloud; commit: 40f11d9; note: publish previews now accept account Soul and mark missing-persona fallback honestly. -->

## 2. Labels And Notes

- [x] 2.1 Replace stale publish preview notes that claim a built-in non-account persona with sample-data/account-persona wording.
  <!-- repo: aidcp-cloud/aidcp-console; commits: 40f11d9, 8be7b42; note: preview copy now says sample persona by default and selected account persona when supplied. -->
- [x] 2.2 Broaden role category display labels in cloud and console without changing category keys or runtime model fallback.
  <!-- repo: aidcp-cloud/aidcp-console; commits: 40f11d9, 8be7b42; note: changed display labels only; category keys remain publish_create/publish_gate. -->

## 3. Verification And Closeout

- [x] 3.1 Add/update cloud tests covering command comment roles, topic roles, publish account-persona preview, and unbound-account fallback.
  <!-- repo: aidcp-cloud; commit: 40f11d9; note: role-prompt-preview tests cover 15 publish text roles, topic roles, preview-only comment roles, account persona, and fallback. -->
- [x] 3.2 Run targeted cloud role prompt tests and typecheck.
  <!-- repo: aidcp-cloud/aidcp-console; validation: cloud targeted role prompt tests 32/32 pass; cloud npm run typecheck pass; console npm run typecheck pass. -->
- [x] 3.3 Run OpenSpec strict validation and update this task list with validation notes.
  <!-- repo: aidcp; validation: openspec validate align-role-prompt-preview --strict pass. -->
- [x] 3.4 Deploy cloud and console production artifacts and record health checks.
  <!-- deployment: 2026-07-05 16:41 CST; aidcp-cloud 40f11d9 deployed to ECS /opt/aidcp/cloud via committed src checksum rsync; backups /opt/aidcp/backups/aidcp-cloud-20260705-164151.tgz and /opt/aidcp/backups/aidcp-cloud-20260705-164151.env; health active, :8787/:8090 listening, /api/version ok, PG select 1 ok, Feishu WS onReady, code anchors verified, isales-scheduler/isales-api active. -->
  <!-- deployment: 2026-07-05 16:41 CST; aidcp-console 8be7b42 dist deployed to /opt/aidcp/console; backup /opt/aidcp/backups/aidcp-console-20260705-164151.tgz; health 8088 root ok, assets/index-DXe1KdCe.js 200, /api/version ok, bundle contains broadened publish category label and sample-persona copy. -->
