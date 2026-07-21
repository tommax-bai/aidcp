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
  <!-- aidcp-cloud be56a86: approval maps to 发布确认 with 待你确认 / 已确认; pending dispatch maps to 等待发布 without changing lifecycle evidence. -->
- [x] 6.2 Rebuild the desktop and narrow-screen progress rail so connectors run only between adjacent node edges, never through labels, with no leading/trailing fragment or false click affordance.
  <!-- aidcp-edge e41aa59: centered desktop nodes with edge-to-edge outgoing segments, vertical narrow-screen segments, no leading/trailing pseudo-element, no hover/cursor affordance, and role/listitem accessibility. -->
- [x] 6.3 Add focused Cloud projection and Edge renderer/static-style regressions, then run the proportionate full, acceptance, syntax, and typecheck gates serially.
  <!-- After current-default rebases: Cloud focused 2/2, acceptance 64/64, full 2767 total (2759 passed, 8 skipped), typecheck passed. Edge focused queue/IPC/companion 96/96, acceptance 28/28, full 2127/2127, four Electron syntax checks and typecheck passed. Browser-rendered data URL was blocked by the browser security policy, so no visual-browser result is claimed; DOM/accessibility and exact CSS connector geometry regressions passed. -->
- [x] 6.4 Rebase onto current defaults, fast-forward merge and push all three repositories, deploy the committed Cloud source to `dev` with backup and runtime checks, and record final evidence without packaging Edge or touching `ol`.
  <!-- origin/master refs: aidcp-cloud be56a86 and aidcp-edge e41aa59, both ff-only after incorporating concurrent default changes. dev 121.89.85.150 backups: /opt/aidcp/backups/cloud-20260721-073124Z.tgz and cloud-env-20260721-073124Z.bak; local/remote changed-source hash matched; AIDCP_DEPLOY_ENV=dev; service active/running with NRestarts=0; 8787/8090/8091 listening; internal/public panel and customer-auth health passed; unauthenticated queue probe returned 401; PostgreSQL select 1 and Feishu WS ready; isales services remained running. No Edge installer was built and ol was not touched. -->

## 7. Home publish-card item switching

- [x] 7.1 Add a stable, environment-scoped carousel projection for waiting active, other active, queued tasks, and recent fallback; preserve a surviving selection across refresh and reset it on removal or environment/platform change.
  <!-- aidcp-edge 38cfeec: stable kind+id selection, explicit waiting/active/task/recent ordering, refresh preservation, and environment/platform/removal reset. -->
- [x] 7.2 Add native left/right edge buttons, wrap-around switching, position feedback, target-title accessibility, restrained hover/focus styling, single-item hiding, responsive spacing, and reduced-motion behavior.
  <!-- aidcp-edge 38cfeec: native edge buttons with target-title labels, cyclic navigation, live title, position feedback, narrow spacing, and reduced-motion coverage. Browser visual check at 900px and geometry check at 420px confirmed both edge placement and no horizontal overflow; a real right-arrow click moved 1/3 to 2/3. -->
- [x] 7.3 Add focused renderer and static-style regressions for priority order, click/keyboard switching, wrap-around, refresh identity preservation, disappearance fallback, environment reset, and hidden-control focus safety; run required Edge acceptance/full/syntax/typecheck gates.
  <!-- aidcp-edge 38cfeec: focused companion 75/75, acceptance 28/28, full 2139/2139, four Electron syntax checks, typecheck, and diff check passed. Native button semantics cover Enter/Space without custom double-activation handlers. -->
- [x] 7.4 Rebase onto the latest defaults, fast-forward merge and push aidcp-edge plus control OpenSpec refs, record final evidence, and do not build an installer or touch Cloud/ol.
  <!-- origin/master aidcp-edge 38cfeec and origin/main control behavior artifacts through 756d170 were integrated by ff-only after fresh fetch/rebase and validation. This checklist closeout follows as a second ff-only control commit. No Edge installer was built; Cloud, dev runtime, and ol were not touched. -->

## 8. Home pending-publish card visual redesign

- [x] 8.1 Replace the enlarged legacy single-post composition with an XHS-only summary shell and queue-style current-item card; remove the unproven decorative thumbnail while preserving loading/error/empty and non-XHS fallbacks.
  <!-- aidcp-edge 25ef6f5: XHS-only queue-surface shell and nested current-item card remove the decorative thumbnail; legacy snapshot, empty, and non-XHS paths explicitly clear the new surface. -->
- [x] 8.2 Add queue-style status badges, per-stage state text, native primary/secondary actions, selected-item-only review visibility, restrained pager/count hierarchy, and responsive no-overflow layouts without changing carousel or queue truth.
  <!-- aidcp-edge 25ef6f5: selected-item heading and state chip, truthful stage summaries, native scoped action buttons, selected waiting-only review entry, quiet edge controls, and 430px vertical stage layout. -->
- [x] 8.3 Add focused renderer/static regressions for hierarchy, stage truth, selected-item actions, native-button semantics, fallback isolation, responsive behavior, and existing carousel flows; complete browser visual checks plus required Edge gates.
  <!-- Post-rebase aidcp-edge evidence: focused companion 77/77, full 2156/2156, acceptance 28/28, four Electron syntax checks, typecheck, and diff check passed. Browser checks at 900x650 and 420x700 verified queue-card hierarchy, no decorative thumbnail, native button equality, bidirectional carousel selection, selected-only review visibility, vertical narrow stages, and no horizontal overflow. -->
- [x] 8.4 Rebase onto latest defaults, fast-forward merge and push aidcp-edge plus control refs, record final evidence, and do not package Edge or touch Cloud/ol.
  <!-- origin/master aidcp-edge 25ef6f5 and origin/main control behavior artifacts through e027128 were integrated by ff-only after current-default rebases and deciding reruns. This checklist closeout follows as a second ff-only control commit. No Edge installer was built; Cloud, dev runtime, and ol were not touched. -->

## 9. Home card priority order

- [x] 9.1 Move the complete daily progress semantic section before the publish card in source order while preserving both cards' ids, controls, state bindings, and activity-stream placement.
  <!-- aidcp-edge 9a474e8: the complete daily-summary block now precedes pub-card in source/DOM order; both semantic sections and all existing ids remain intact, with the activity stream after both. -->
- [x] 9.2 Add DOM-order regression coverage, complete focused/full Edge gates, and visually verify desktop plus narrow layouts with both cards visible.
  <!-- aidcp-edge 9a474e8: focused companion 77/77, full 2156/2156, acceptance 28/28, four Electron syntax checks, typecheck, and diff check passed. Browser checks at 900x800 and 420x900 verified daily-summary -> pub-card -> activity order, 14px card spacing, preserved responsive layout, and no horizontal overflow. -->
- [ ] 9.3 Rebase onto latest defaults, fast-forward merge and push aidcp-edge plus control refs, record final evidence, and do not package Edge or touch Cloud/ol.
