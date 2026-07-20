## 1. Admission and current-path inventory

- [x] 1.1 Record preflight result, starting SHAs, canonical checkout cleanliness and isolated control/Edge/Cloud worktrees; preserve unrelated files and install physical dependencies in each changed app worktree.
  <!-- 2026-07-20: ./scripts/task-preflight passed. Canonical aidcp main, aidcp-edge master and aidcp-cloud master matched origin; existing control untracked output/ and tmp/ were preserved. Isolated codex/separate-client-data-plane-automation-engine worktrees start at aidcp=739f8e1, edge=857d332, cloud=f57bfb7. Edge/Cloud each completed npm ci --prefer-offline with a physical non-linked node_modules. -->
- [x] 1.2 Inventory renderer IPC, Electron HTTP, Edge stdin/stdout, automation WebSocket and Cloud handlers; classify every operation as local, cloud_data, automation_control, platform_api_automation, browser_lifecycle or page_automation.
  <!-- Inventory recorded in implementation-notes.md from Edge preload/main/operation-registry and Cloud client-auth/handler. It identifies login-time bootstrap, current pause/close semantics, HTTP data routes, API-only automation and page commands. -->
- [x] 1.3 Record compatibility behavior for legacy `client_core_browser_executor_v1` clients and new `client_data_plane_automation_engine_v1` clients before changing protocol hotspots.
  <!-- Capability matrix and downgrade rules recorded in implementation-notes.md before protocol edits. New fields remain optional; old clients retain v1 adapters and core/Cloud projection. -->

## 2. Cloud HTTP data plane and capability compatibility

- [x] 2.1 Confirm every client data-management action uses a narrow customer-auth HTTP endpoint and add any missing endpoint by reusing the existing ownership/binding, idempotency/CAS, domain and audit methods.
  <!-- Registry/inventory cover session, roster/provision/offboard, persona, publish drafts/approval, delegated/curated content, slow-start, risk and interaction workspaces. Existing client-auth endpoints cover all surfaces; no new domain writer was needed. -->
- [x] 2.2 Add `client_data_plane_automation_engine_v1` to Cloud/Edge capability negotiation and keep optional hello/welcome fields backward compatible.
  <!-- Edge offers legacy + new capabilities; Cloud echoes the new bit only when offered. Negotiation tests cover additive hello/welcome behavior. -->
- [x] 2.3 Separate Cloud command metadata into automation_control, cloud_data compatibility adapters, platform_api_automation, browser_lifecycle and page_automation; reject unclassified active commands.
  <!-- Matching Edge/Cloud registries classify every active automation message; Cloud rejects unclassified operations before push routing. -->
- [x] 2.4 Add Cloud parity and security tests proving HTTP works without an active Edge connection, legacy WS adapters retain identical domain gates, and accepted decisions remain distinct from platform success.
  <!-- Cloud client-auth/customer-api: 51/51 passed, including offline persona/drafts/approval/slow-start/risk and ownership fail-closed cases. Legacy handler suites remain green; approval keeps accepted_pending_execution distinct from platform success. -->
- [x] 2.5 Add an outbound boundary test proving Cloud/admin cannot push `cloud_data` over the automation WebSocket; a future data notification may only invalidate and trigger an HTTP refetch.
  <!-- Cloud registry rejects persona/publish data messages as outbound automation commands. UiSnapshot capability tests suppress persona/publish for new clients; Edge filters the same fields from legacy Cloud snapshots. -->

## 3. Edge client data plane and operation registry

- [x] 3.1 Rename the central operation categories/transports to cloud_data and platform_api_automation, keep browser requirements explicit, and update exhaustive protocol-drift tests.
  <!-- Edge registry tests cover every routed active command and Electron cloud_data surface; Cloud has matching outbound metadata. -->
- [x] 3.2 Route all AIDCP-owned data operations through Electron-main customer-auth HTTP without handle.child, automation WebSocket, browser/CDP or slot gates; keep renderer credentials redacted.
  <!-- Narrow IPC→clientAuthFetch adapters remain the only client data path. Security contracts forbid child/start/slot access; slow-start/risk reads now use HTTP regardless of engine link. -->
- [x] 3.3 Keep external platform API automation in the engine path without browser slots, and assert it cannot run while automation is stopped/paused except explicit minimal cleanup or reauthorization flows.
  <!-- interaction sync/reply/offboard are platform_api_automation + browser forbidden. Pause disconnects the ordinary engine; restricted cleanup and explicit reauthorization remain separate. -->
- [x] 3.4 Introduce a structured Cloud target resolving customer-auth HTTP and automation WebSocket independently, including safe legacy setting migration and validation for custom targets.
  <!-- cloudTargetView exposes dataApiUrl + automationUrl. dev/ol use independent maps; custom UI validates HTTP and WS separately; legacy WS-only setting remains automation compatibility input. -->

## 4. On-demand automation engine lifecycle

- [x] 4.1 Stop customer login and roster refresh from bootstrapping ordinary per-environment Edge engines; retain only trusted environment handles and restricted cleanup recovery.
  <!-- Login/maintenance only enforce ownership and stop untrusted running engines. Contract proves no ordinary spawn/provider/slot path; restricted cleanup supervisor remains. -->
- [x] 4.2 Implement start as an on-demand engine launch plus automatic browser acquisition/attach/identity verification, with truthful starting/waiting_resource/ready stages.
  <!-- Explicit start sets automationIntent=enabled and enters the guarded start/browser/identity flow; lifecycleAxes separates starting/waiting_resource/ready/running. -->
- [x] 4.3 Implement pause as bounded task quiescence and pause reporting followed by ordinary engine disconnect/stop while preserving the client HTTP data plane and optionally the warm browser.
  <!-- Pause sends lifecycle.pause_and_exit and uses SIGTERM only if IPC delivery fails; queues/retries are cancelled. Browser is deliberately released with its owning engine so slot ownership remains truthful; resume reacquires it. -->
- [x] 4.4 Implement resume as automatic browser reuse or reacquisition followed by identity recheck and engine reconnect; no manual browser-open prerequisite.
  <!-- Completed pause resumes through queueStartEnv; resume during teardown waits for close then relaunches. Advanced manual-browser paused sessions can resume in place. -->
- [x] 4.5 Implement close as bounded engine shutdown plus CDP/provider/lease/slot release; distinguish intentional stop/pause from crash so the supervisor does not respawn.
  <!-- edge:close sends lifecycle.close + user_close; browser:close remains an executor-only advanced action. Exit classification includes automation intent and stop reason. -->
- [x] 4.6 Preserve bounded crash recovery only while automation intent is enabled and isolate browser/executor failures from customer session and HTTP operations.
  <!-- Respawn is guarded by automationIntent=enabled; pause/close/untrusted binding clear retry/queue state and never respawn. -->

## 5. Client state and readable controls

- [x] 5.1 Replace new-client coreState/cloudState primary projection with customer session, automationState, browserState and diagnostic-only engineLinkState; keep legacy fields only behind compatibility projection.
  <!-- statusOf adds clientSessionState/engineLinkState and automation-first projection. Renderer no longer displays core/cloud axes; old fields remain compatibility diagnostics. -->
- [x] 5.2 Distinguish ready/waiting-task from running and expose waiting_resource, pausing, stopping and actionable browser blocked/error reasons without fake success.
  <!-- ready follows engine link, running requires loopStage; waiting_resource/pausing/stopping and browser blocked/closing/error are explicit. -->
- [x] 5.3 Update environment rows, health details and primary controls to start/pause/resume/close automation; keep manual browser open only for login, reauthorization, captcha and inspection.
  <!-- Primary FAB is start/pause/resume; secondary closes automation while active/paused. When stopped it is “打开浏览器（登录/检查）”. -->
- [x] 5.4 Remove client-core/Cloud-connected/browser-required gates and wording from persona, drafts, approval, configuration and other cloud_data surfaces.
  <!-- Persona uses customer session + HTTP/roster binding; slow-start/risk always pull via HTTP. User-visible health/settings/lifecycle wording is client/data/automation-first. -->

## 6. Protocol, tests and documentation

- [x] 6.1 Synchronize Edge/Cloud protocol types, capabilities, command classification and `docs/protocol.md`; run round-trip, command-count, target-routing and unauthorized-command acceptance tests.
  <!-- Edge/Cloud share client_data_plane_automation_engine_v1 and matching automation registries. Target guard proves unclassified/data-only outbound frames are rejected and mixed ui.snapshot is sanitized; docs/protocol.md records the capability and data-pull boundary. -->
- [x] 6.2 Add Edge lifecycle integration tests for login without engine spawn, HTTP with WS offline, start/ready/run, pause disconnect, resume auto-browser, close release and intentional-no-respawn behavior.
  <!-- Core lifecycle and Electron contract suites cover login without spawn, pause_and_exit, manual-browser paused wake, resume relaunch, close, and intent-gated respawn. Persona/publish/slow-start/risk IPC suites prove customer HTTP remains usable without a child or WS. -->
- [x] 6.3 Add slot/CDP tests proving cloud_data never acquires a browser, platform_api_automation requires an enabled engine but no page lease, and page_automation retains all safety gates.
  <!-- Exhaustive Edge/Cloud registry tests require customer_auth_http+browser forbidden for cloud_data, automation_ws+browser forbidden for platform_api_automation, and browser required for page_automation; unknown operations fail closed. -->
- [x] 6.4 Run focused Edge/Cloud tests, required acceptance suites, full tests for protocol/publish/risk-adjacent paths and both repositories' typecheck; retain bounded evidence.
  <!-- Final worktree validation: Edge acceptance + full test suite + typecheck passed; Cloud acceptance + full test suite + typecheck passed. Focused transport/data-plane suites passed 36/36; focused lifecycle/renderer regressions passed after updating legacy UI expectations. Facebook publish timing test was rerun three consecutive times after one full-suite concurrency flake and passed each time; the final full Edge suite passed. -->

## 7. Integration, rollout and closure

- [x] 7.1 Record implementation commits, test evidence, compatibility deviations and any real-machine residuals in this task file; validate the OpenSpec change strictly.
  <!-- Implementation commits: aidcp-edge master 5013b9d, aidcp-cloud master da7df17, control architecture/docs c78c8e9. Strict OpenSpec validation passed before and after integration. Compatibility deviation: the current pause implementation releases the engine-owned browser/CDP/slot instead of retaining a warm browser; resume reacquires automatically. Real-machine residual: no packaged desktop client was built or launched, so desktop lifecycle evidence is source/test level only. -->
- [x] 7.2 Rebase/fetch and integrate clean feature commits into Edge/Cloud default branches without overwriting concurrent work, then push the exact default-branch commits.
  <!-- All feature commits were rebased repeatedly as concurrent defaults advanced, then integrated with --ff-only. Pushed exact defaults: aidcp-edge master 5013b9d and aidcp-cloud master da7df17; control main retained concurrent changes and carried the architecture commit c78c8e9. Canonical control output/ and tmp/ remained untouched. -->
- [x] 7.3 Read deployment documentation, run `scripts/deploy-target dev --check`, deploy Cloud additive changes to dev from an eligible clean default checkout and verify service/listener/health without touching unrelated services.
  <!-- Target dev=121.89.85.150 passed deploy-target --check. Remote backup timestamp 20260720-153740; the first rsync lacked the key and failed before restart, then explicit keyed rsync succeeded and source guards were verified. Only aidcp-cloud.service was restarted. Final deploy marker da7df17; service active, 8787/8090/5432 listening, /api/health ok, PostgreSQL accepting, and Feishu WS ready. No isales service/path was touched. -->
- [x] 7.4 Verify dev behavior for data management with engine/browser absent and source-level desktop lifecycle tests; do not build or publish a desktop installer unless separately requested.
  <!-- Dev public health returned ok. A no-token request to /capi/environments/no-such-env/persona returned HTTP 401 missing_token directly from the customer HTTP boundary, not an engine/browser prerequisite. Authenticated offline behavior is covered by Cloud customer-auth integration tests; no live customer credential was used. Edge lifecycle/renderer suites cover stopped/paused engine and closed-browser HTTP access. No desktop installer was built or published. -->

## 8. Client lifecycle wording follow-up

- [x] 8.1 Simplify the visible lifecycle controls to `浏览器` and `启动`/`暂停`/`恢复`/`关闭`, retain truthful browser open/close accessibility hints, and update focused renderer tests.
  <!-- Edge primary controls now use the requested compact labels; the browser button keeps its existing open/close behavior and exposes the current action through aria-label/title. The batch action is `全部启动`. Focused renderer/fleet tests passed 127/127 and Edge typecheck passed. -->
- [x] 8.2 Remove redundant client/automation prefixes from compact status labels while preserving specific browser/account labels and explanatory failure details; update focused health, fleet and renderer tests.
  <!-- Health and fleet labels now use compact context-aware wording: 已就绪/处理中/连接中/重连中/运行中/已暂停/启动中/暂停中/关闭中/异常. Browser/account/action-required labels and diagnostic details retain their subjects. Focused health/fleet/companion/renderer suites passed 250/250 and Edge typecheck passed. -->

## 9. Client home HTTP single source

- [x] 9.1 Add an environment-scoped customer-auth overview read returning authoritative daily usage, current publish state and last published summary without accepting or exposing `accountId`.
  <!-- GET /environments/:envKey/overview resolves the customer-owned persistent binding server-side and returns dailyUsage/currentPublishState/lastPublished + meta.asOf without accountId. -->
- [x] 9.2 Reuse the existing Cloud usage builder and publish stores, add ownership/offline/error tests, and keep submitted distinct from platform-confirmed published.
  <!-- Overview reuses buildTodayUsageForAccount and PublishLogStore. Tests cover stopped/offline access, ownership fail-closed, aggregation failure, and an in-flight-only query where submitted remains distinct from last confirmed published. -->
- [x] 9.3 Stop Cloud and Edge from carrying `dailyUsage` over automation `ui.snapshot` for new-capability clients while preserving legacy clients and the independent `browserStandby` wake chain.
  <!-- Capability-aware service and transport filters now retain only browserStandby for new clients; legacy clients keep the historical payload and the standby refresh chain schedules independently with null dailyUsage. -->
- [x] 9.4 Add a narrow Electron main/preload overview IPC that uses customer-auth HTTP without child, WS, browser, CDP or slot access.
  <!-- environment-overview:get resolves local envId to profileId in main and calls a fixed customer-auth endpoint; static security tests prove renderer cannot supply URL/token/accountId or cross into runtime/browser gates. -->
- [x] 9.5 Refresh the selected environment overview on selection, focus, expand, bounded polling and local automation-result invalidation; keep last confirmed data with freshness and do not fabricate initial zeroes.
  <!-- Renderer owns a per-environment HTTP cache with selection/focus/expand/60s polling and debounced 5s-minimum invalidation refresh. Initial failure renders unknown markers; refresh failure retains confirmed values with a cache label. -->
- [x] 9.6 Add focused Cloud/Edge boundary, renderer freshness and offline-engine tests; run required acceptance/full suites and both typechecks.
  <!-- Focused Cloud boundary/store tests passed 10/10 and Edge registry/IPC/renderer tests passed 10/10. Cloud acceptance 60/60 + full suite passed + typecheck passed; Edge acceptance 26/26 + full 2034/2034 + typecheck passed. One legacy zero-style assertion exposed a regression in the compatibility fallback; the fallback was corrected and both focused/full suites then passed. -->
- [x] 9.7 Synchronize protocol/docs, validate OpenSpec strictly, integrate/push clean default branches, deploy Cloud to dev and verify the HTTP endpoint boundary without building an Edge installer.
  <!-- Strict validation passed. After resolving concurrent XHS schedule conflicts by retaining both features, rebased full suites and typechecks passed. Integrated/pushed Cloud master 50052fe and Edge master 7c6730d. Dev target check passed; backup cloud.bak.20260720-181421.tar.gz + .env.bak.20260720-181421; deployed Cloud SHA 50052fe with matching source hashes. Only aidcp-cloud.service restarted. Service active; 8787/8090/8091/5432 listening; panel health ok; PostgreSQL accepting; Feishu WS onReady; Nginx /capi overview boundary returned 401 missing_token without a credential; four isales services remained active. No live customer credential was used, so authenticated offline content behavior remains integration-test evidence. No Edge installer was built. -->

## 10. Pending draft approval entry follow-up

- [x] 10.1 Reproduce and specify the regression where overview returns a pending summary but clears inline `publishPreview`, leaving the card without an approval entry. <!-- dev DB truth: Tmax #161 remains pending_approval; renderer link/open guards still required status.publishPreview even though customer-auth draft list/detail RPCs are available -->
- [x] 10.2 Make the publish card expose the draft entry for pending/reminded overview state when the named draft queue RPC is available, and open the HTTP-backed workspace without requiring inline preview data. <!-- Edge now derives entry availability from inline legacy preview OR pending/reminded + publishDraftList/Get; opening the workspace fetches HTTP list/detail and does not restore WS preview payloads -->
- [x] 10.3 Add a renderer regression covering the #161-shaped overview response with no inline preview, including list/detail fetch, visible approve/cancel actions and legacy behavior preservation. <!-- companion-ui 71/71 passed; exact #161 title/code verifies visible link, env-scoped list/detail calls, complete content and approve/cancel actions; existing inline-preview tests stayed green -->
- [ ] 10.4 Run focused/full relevant Edge tests, typecheck and strict OpenSpec validation; integrate/push the clean Edge/control commits and reload the source client without building an installer.
