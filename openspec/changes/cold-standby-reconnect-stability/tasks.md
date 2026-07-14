## 1. OpenSpec and Worktrees

- [x] 1.1 Create proposal, design, spec deltas, and implementation tasks.
  <!-- aidcp: OpenSpec artifacts created under openspec/changes/cold-standby-reconnect-stability. -->
- [x] 1.2 Open isolated `aidcp-edge` and `aidcp-cloud` worktrees named `cold-standby-reconnect-stability`.
  <!-- aidcp-edge/aidcp-cloud: worktrees created for branch-local implementation; both were removed by land-change after successful push. -->

## 2. Edge Standby Stability

- [x] 2.1 Keep core in cold standby when cloud reconnect is exhausted during standby.
  <!-- aidcp-edge 13251bc: cloud.unrecoverable during active cold standby now stays in standby and schedules background cloud recovery instead of recycle shutdown. -->
- [x] 2.2 Preserve Electron standby classification when a child exits during pending/active cold standby.
  <!-- aidcp-edge 13251bc: Electron child-close handling keeps cold-standby pending/active exits in standby instead of ordinary crash respawn. -->
- [x] 2.3 Add focused edge regression tests for standby cloud-unrecoverable and child-close behavior.
  <!-- aidcp-edge 13251bc: test/electron/lifecycle-contract.test.ts covers standby cloud exhaustion and standby child-close classification. -->

## 3. Cloud Nickname Capture Scope

- [x] 3.1 Remove hello/reconnect-driven nickname capture arming.
  <!-- aidcp-cloud 709c894: RoleDispatcher no longer arms nickname capture from hello/reconnect/session_start. -->
- [x] 3.2 Arm nickname capture only once after first `page.cards` for a full browser startup/restart generation.
  <!-- aidcp-cloud 709c894: NicknameEnricher consumes first page.cards startupId per browser generation and de-dupes repeated cards. -->
- [x] 3.3 Add focused cloud tests for reconnect no-op and startup first-card capture.
  <!-- aidcp-cloud 709c894: nickname-enricher and persona-gated-start tests cover reconnect no-op and startup page.cards capture. -->

## 4. Validation, Integration, and Dev Deploy

- [x] 4.1 Run focused edge tests and `npm run typecheck` in the edge worktree.
  <!-- aidcp-edge 13251bc validation: focused lifecycle test passed; test:acceptance passed; npm test passed (1152 tests); typecheck passed. -->
- [x] 4.2 Run focused cloud tests and `npm run typecheck` in the cloud worktree.
  <!-- aidcp-cloud 709c894 validation: focused nickname/persona tests passed; test:acceptance passed; npm test passed (1919 tests); typecheck passed. -->
- [x] 4.3 Run `openspec validate cold-standby-reconnect-stability --strict`.
  <!-- aidcp: strict validation passed before integration and was rerun after task/doc updates. -->
- [x] 4.4 Commit and push edge/cloud/default-branch changes; update this task file with commit SHAs and validation notes.
  <!-- aidcp-edge master 13251bc and aidcp-cloud master 709c894 pushed to origin/master; aidcp control docs/tasks are committed in this closeout. Deviation: no edge desktop installer built. -->
- [x] 4.5 Deploy cloud changes to dev from the clean default checkout and verify health.
  <!-- dev deploy 20260714-103425 backup: /opt/aidcp/backups/cloud.bak.20260714-103425.tar.gz and cloud.env.bak.20260714-103425. Deployed aidcp-cloud 709c894 from origin/master archive; service active, ports 8787/8090/8088 listening, local/public /api/health ok, Feishu WS ready, PostgreSQL select 1 ok. -->
