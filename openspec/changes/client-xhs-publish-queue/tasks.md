## 1. Cloud customer queue contract

- [x] 1.1 Add minimum-disclosure customer publish-queue DTO mapping for queued tasks, active lifecycle, recent terminal results, four-stage progress, and truthful summary counts.
  <!-- aidcp-cloud 9745558: whitelist projection, account/XHS filtering, four-stage lifecycle compression, and honest submitted semantics. -->
- [x] 1.2 Add the environment-owned XHS `GET /environments/:envKey/publish-queue` route with exact ownership/platform checks and no internal account or snapshot disclosure.
  <!-- aidcp-cloud 9745558: customer-auth environment binding is resolved before the account-scoped read; response omits accountId and internal lifecycle evidence. -->
- [x] 1.3 Add the exact-environment `POST /environments/:envKey/publish-queue/tasks/:taskId/cancel` route with publish-family/status guards, required version CAS, and truthful immediate-versus-safe-stop receipts.
  <!-- aidcp-cloud 9745558: task/account/action/status guards precede DelegatedTaskService versioned cancellation. -->
- [x] 1.4 Add focused Cloud tests for environment isolation, non-XHS/unknown binding rejection, DTO allowlisting, lifecycle separation, immediate cancellation, cancellation-in-progress, and version conflict.
  <!-- aidcp-cloud 9745558: focused 59/59; full 2742 total, 2734 passed and 8 skipped; acceptance 64/64; typecheck passed. -->

## 2. Edge customer HTTP bridge

- [x] 2.1 Add Electron main handlers that resolve local envId to the real envKey and call the fixed customer publish-queue read/cancel routes while keeping tokens and accountId out of renderer input.
  <!-- aidcp-edge 1a92d54: main owns customer-auth path/token/envKey resolution and cancel forwards only version. -->
- [x] 2.2 Expose narrow preload methods for queue read and versioned cancellation, and add IPC security tests for allowed fields, path construction, and invalid input rejection.
  <!-- aidcp-edge 1a92d54: named IPC bridge plus publish-queue-ipc-security contract coverage. -->

## 3. Edge publish queue experience

- [x] 3.1 Extend the in-app content workspace with an XHS-only publish queue page, environment/request-epoch isolation, loading/error/cache states, active/recent separation, and existing draft-review navigation.
  <!-- aidcp-edge 1a92d54: environment-scoped state, stale-response epochs, bounded polling/focus refresh, and draft handoff. -->
- [x] 3.2 Replace the XHS single-record home dock with a compact “发布进度” summary that prioritizes waiting approval, links to the full queue, and retains honest submitted/published semantics.
  <!-- aidcp-edge 1a92d54: waiting approval expands first; system-only work stays compact; submitted remains platform-confirming. -->
- [x] 3.3 Add per-task cancellation confirmation, single-row pending state, immediate cancelled receipt, cancellation-in-progress state, version-conflict refresh, and failure preservation without optimistic removal.
  <!-- aidcp-edge 1a92d54: exact task/version confirmation, no optimistic removal, safe-stop copy, and conflict refresh without retrying the write. -->
- [x] 3.4 Add responsive queue styles that reuse the existing blue/teal rounded-card language, avoid horizontal overflow, and preserve reduced-motion behavior.
  <!-- aidcp-edge 1a92d54: responsive card/stage/dialog styling with narrow single-column layout and reduced-motion override. -->
- [x] 3.5 Add focused renderer behavior tests for XHS gating, environment switching, stale response rejection, queue rendering, draft handoff, cancellation targeting, and truthful error/terminal states.
  <!-- aidcp-edge 1a92d54: focused post-review 96/96; full 2078/2078; acceptance 28/28; syntax checks and typecheck passed. -->

## 4. Validation and isolated handoff

- [x] 4.1 Install physical dependencies in each code worktree and run focused Cloud tests followed by Cloud typecheck.
  <!-- Physical node_modules in aidcp-cloud worktree; no dependency symlink. Validation evidence is recorded in 1.4. -->
- [x] 4.2 Run focused Edge renderer/IPC tests, syntax checks, and Edge typecheck without building an installer.
  <!-- Physical node_modules in aidcp-edge worktree; no dependency symlink or installer build. Validation evidence is recorded in 3.5. -->
- [x] 4.3 Run `openspec validate client-xhs-publish-queue --strict`, record validation/commit evidence in this checklist, and commit each feature branch without merging, deploying, packaging, or changing canonical checkout branches.
  <!-- Strict validation passed; code commits are aidcp-cloud 9745558 and aidcp-edge 1a92d54. Control evidence is committed on codex/client-xhs-publish-queue. No merge, deploy, package, or canonical branch switch was performed. -->
