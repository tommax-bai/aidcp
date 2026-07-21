## 1. Cloud customer queue contract

- [x] 1.1 Add minimum-disclosure customer publish-queue DTO mapping for queued tasks, active lifecycle, recent terminal results, four-stage progress, and truthful summary counts.
  <!-- aidcp-cloud ab0e72f: whitelist projection, account/XHS filtering, four-stage lifecycle compression, and honest submitted semantics. -->
- [x] 1.2 Add the environment-owned XHS `GET /environments/:envKey/publish-queue` route with exact ownership/platform checks and no internal account or snapshot disclosure.
  <!-- aidcp-cloud ab0e72f: customer-auth environment binding is resolved before the account-scoped read; response omits accountId and internal lifecycle evidence. -->
- [x] 1.3 Add the exact-environment `POST /environments/:envKey/publish-queue/tasks/:taskId/cancel` route with publish-family/status guards, required version CAS, and truthful immediate-versus-safe-stop receipts.
  <!-- aidcp-cloud ab0e72f: task/account/action/status guards precede DelegatedTaskService versioned cancellation. -->
- [x] 1.4 Add focused Cloud tests for environment isolation, non-XHS/unknown binding rejection, DTO allowlisting, lifecycle separation, immediate cancellation, cancellation-in-progress, and version conflict.
  <!-- aidcp-cloud ab0e72f: post-rebase full 2750 total, 2742 passed and 8 skipped; acceptance 64/64; typecheck passed. -->

## 2. Edge customer HTTP bridge

- [x] 2.1 Add Electron main handlers that resolve local envId to the real envKey and call the fixed customer publish-queue read/cancel routes while keeping tokens and accountId out of renderer input.
  <!-- aidcp-edge 289713b: main owns customer-auth path/token/envKey resolution and cancel forwards only version. -->
- [x] 2.2 Expose narrow preload methods for queue read and versioned cancellation, and add IPC security tests for allowed fields, path construction, and invalid input rejection.
  <!-- aidcp-edge 289713b: named IPC bridge plus publish-queue-ipc-security contract coverage. -->

## 3. Edge publish queue experience

- [x] 3.1 Extend the in-app content workspace with an XHS-only publish queue page, environment/request-epoch isolation, loading/error/cache states, active/recent separation, and existing draft-review navigation.
  <!-- aidcp-edge 289713b: environment-scoped state, stale-response epochs, bounded polling/focus refresh, and draft handoff. -->
- [x] 3.2 Replace the XHS single-record home dock with a compact “发布进度” summary that prioritizes waiting approval, links to the full queue, and retains honest submitted/published semantics.
  <!-- aidcp-edge 289713b: waiting approval expands first; system-only work stays compact; submitted remains platform-confirming. -->
- [x] 3.3 Add per-task cancellation confirmation, single-row pending state, immediate cancelled receipt, cancellation-in-progress state, version-conflict refresh, and failure preservation without optimistic removal.
  <!-- aidcp-edge 289713b: exact task/version confirmation, no optimistic removal, safe-stop copy, and conflict refresh without retrying the write. -->
- [x] 3.4 Add responsive queue styles that reuse the existing blue/teal rounded-card language, avoid horizontal overflow, and preserve reduced-motion behavior.
  <!-- aidcp-edge 289713b: responsive card/stage/dialog styling with narrow single-column layout and reduced-motion override. -->
- [x] 3.5 Add focused renderer behavior tests for XHS gating, environment switching, stale response rejection, queue rendering, draft handoff, cancellation targeting, and truthful error/terminal states.
  <!-- aidcp-edge 289713b: final 0.3.24 baseline focused integration set 222/222; full 2091/2091; acceptance 28/28; syntax checks and typecheck passed. -->

## 4. Validation and isolated handoff

- [x] 4.1 Install physical dependencies in each code worktree and run focused Cloud tests followed by Cloud typecheck.
  <!-- Physical node_modules in aidcp-cloud worktree; no dependency symlink. Validation evidence is recorded in 1.4. -->
- [x] 4.2 Run focused Edge renderer/IPC tests, syntax checks, and Edge typecheck without building an installer.
  <!-- Physical node_modules in aidcp-edge worktree; no dependency symlink or installer build. Validation evidence is recorded in 3.5. -->
- [x] 4.3 Run `openspec validate client-xhs-publish-queue --strict`, record validation/commit evidence in this checklist, and commit each feature branch without merging, deploying, packaging, or changing canonical checkout branches.
  <!-- Initial isolated handoff passed strict validation; final rebased code refs are aidcp-cloud ab0e72f and aidcp-edge 289713b. No merge, deploy, package, or canonical branch switch had been performed at that phase boundary. -->

## 5. Authorized integration and dev delivery

- [x] 5.1 Fetch current default branches, rebase the feature branches where required, and rerun the required full, acceptance, syntax, and typecheck gates serially.
  <!-- Concurrent default-branch advances were incorporated before the deciding reruns. aidcp-cloud ab0e72f: full 2750 total, 2742 passed and 8 skipped; acceptance 64/64; typecheck passed. aidcp-edge 289713b: physical dependencies refreshed for the new lockfile, focused 222/222, full 2091/2091, acceptance 28/28, four Electron syntax checks and typecheck passed. -->
- [x] 5.2 Fast-forward merge and push aidcp-cloud and aidcp-edge default branches without rewriting concurrent history.
  <!-- origin/master refs: aidcp-cloud ab0e72f and aidcp-edge 289713b. Both were ff-only integrations after repeated fetch/rebase; no force push or concurrent-history rewrite. -->
- [x] 5.3 From the clean aidcp-cloud master checkout, back up the `dev` runtime, deploy committed Cloud sources, restart only `aidcp-cloud.service`, and verify service, listeners, HTTP health, PostgreSQL, and target identity.
  <!-- dev 121.89.85.150: backups /opt/aidcp/backups/cloud-20260721-041827Z.tgz and cloud-env-20260721-041827Z.bak; local/remote hashes matched; AIDCP_DEPLOY_ENV=dev; service active with NRestarts=0; 8787/8090/8091 listening; internal and public health passed; queue unauth probe 401; PostgreSQL select 1, Feishu WS ready, and both isales services remained active. -->
- [x] 5.4 Record final refs and deployment evidence, validate OpenSpec strictly, then fast-forward merge and push the control change to `main`; do not build an Edge installer or deploy `ol`.
  <!-- Control artifacts and rollout evidence were rebased onto current origin/main, strict validation passed, and ff-only integration was pushed through 912f255; this final checklist closeout is appended on the same branch. No Edge installer was built and ol was not touched. -->

## 6. Customer-facing stage polish

- [x] 6.1 Rename the customer approval stage to `发布确认` and add truthful stage-specific wording for waiting, completed, and not-yet-dispatched states.
  <!-- aidcp-cloud fbfc67d: approval maps to 发布确认 with 待你确认 / 已确认; pending dispatch maps to 等待发布 without changing lifecycle evidence. -->
- [x] 6.2 Rebuild the desktop and narrow-screen progress rail so connectors run only between adjacent node edges, never through labels, with no leading/trailing fragment or false click affordance.
  <!-- aidcp-edge 84013d0: centered desktop nodes with edge-to-edge outgoing segments, vertical narrow-screen segments, no leading/trailing pseudo-element, no hover/cursor affordance, and role/listitem accessibility. -->
- [x] 6.3 Add focused Cloud projection and Edge renderer/static-style regressions, then run the proportionate full, acceptance, syntax, and typecheck gates serially.
  <!-- Cloud focused 2/2, acceptance 64/64, full 2758 total (2750 passed, 8 skipped), typecheck passed. Edge focused queue/IPC 23/23 plus companion 73/73, acceptance 28/28, full 2127/2127, four Electron syntax checks and typecheck passed. Browser-rendered data URL was blocked by the browser security policy, so no visual-browser result is claimed; DOM/accessibility and exact CSS connector geometry regressions passed. -->
- [ ] 6.4 Rebase onto current defaults, fast-forward merge and push all three repositories, deploy the committed Cloud source to `dev` with backup and runtime checks, and record final evidence without packaging Edge or touching `ol`.
