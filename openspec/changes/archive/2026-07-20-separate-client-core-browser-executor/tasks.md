## 1. Admission and contract inventory

- [x] 1.1 Run `./scripts/task-preflight`, create/reuse matching isolated worktrees for `aidcp-cloud` and `aidcp-edge`, and record starting SHAs plus any unrelated dirty state without modifying canonical checkouts.
  <!-- 2026-07-20: preflight passed. Created isolated worktrees from origin/master: aidcp-cloud=5b31064f2098332d46702f7cf88220dc3d48fa12, aidcp-edge=0a0b6c55f600076bac3289c681992db13bc251e7. Canonical sibling checkouts were clean. Preserved unrelated untracked control-repo paths: openspec/changes/group-admin-console-navigation/, openspec/changes/recover-stale-delegated-executions/, output/, tmp/. -->
- [x] 1.2 Inventory every Electron IPC action, Cloud→Edge command and Edge-local platform API operation that currently checks `handle.child`, browser/CDP, auth projection, `queueStartEnv`, restart-all or slot state; record its target category and transport in the change notes.
  <!-- Inventory and classifications recorded in implementation-notes.md from current aidcp-edge/cloud default heads. -->
- [x] 1.3 Reconcile this change with the active `browser-slot-scheduling` and completed-unarchived `browser-slot-cloud-presence` artifacts so their queue/control-only wording cannot reintroduce browser gating; preserve browser-slot scheduling exclusively for executor acquisition.
  <!-- Both browser-slot-cloud-presence repo commits are ancestors of current master. This change reuses its core/wake chain and leaves browser-slot FIFO, memory admission, leases and safety gates unchanged; browser-slot-scheduling residuals remain independently tracked. -->
- [x] 1.4 Define the cross-repo protocol/type delta, optional `client_core_browser_executor_v1` capability and compatibility matrix before touching the protocol/command-routing single-writer hotspot.
  <!-- No new MessageType. Additive optional hello/welcome capability plus customer-auth HTTP routes; legacy WS paths remain. Full compatibility matrix is in implementation-notes.md. -->

## 2. Cloud customer-auth and shared domain operations

- [x] 2.1 Add a reusable Cloud resolver that authenticates the customer, verifies `envKey` ownership and resolves the current authoritative account binding with stable, non-leaking rejection codes.
- [x] 2.2 Add narrow customer-auth handlers for persona status/generate/confirm that accept `envKey` rather than client-authoritative `accountId` and reuse existing validation, role, idempotency, persistence and accounting domain methods.
- [x] 2.3 Add narrow customer-auth handlers for pending-draft image removal that reuse the existing row-lock/CAS single-writer method and preserve every ownership, decision, status, version, member and last-image gate.
- [x] 2.4 Add narrow customer-auth handlers for approve/reject that reuse existing approval signature, live-version, idempotency and audit logic and return an accepted/pending-execution receipt distinct from platform-published success.
- [x] 2.5 Keep the legacy Edge WS persona/edit/approval transports operational behind compatibility handling and add parity tests proving both transports call the same domain methods and produce the same gates/audit semantics.
- [x] 2.6 Expose authoritative per-environment persona binding state through the customer-auth environment state/roster contract without depending on an Edge hello or browser session.
  <!-- aidcp-cloud f57bfb7: customer-auth resolver/routes reuse AccountPersonaService, draftImageRemove and clientPublishApproval; legacy WS handlers call the same domain methods. Ownership/binding/parity/receipt tests are in client-auth-server, handler and publish suites. -->

## 3. Protocol classification and capability negotiation

- [x] 3.1 Implement the centralized operation registry with exactly one of `local`, `cloud`, `platform_api`, `browser_lifecycle` or `page_automation` plus declared transport and identity requirements for every inventoried action.
- [x] 3.2 Make unregistered renderer actions and Cloud→Edge commands fail closed as `operation_unclassified`, with bounded diagnostic logging and protocol-drift tests that enumerate the complete registry.
- [x] 3.3 Add optional `client_core_browser_executor_v1` negotiation across Cloud/Edge protocol mirrors, hello handling, Cloud command mapping and Edge active-command routing while preserving old-client behavior.
- [x] 3.4 Synchronize changed protocol v2 types and command metadata across both repos and `docs/protocol.md`, then run focused protocol round-trip, command-count and unauthorized-routing suites.
  <!-- aidcp-edge 857d332 / aidcp-cloud f57bfb7: additive capability is echoed only when offered. Context-isolated preload exposes named operations only; unknown client classifications return null and unknown Cloud active commands log/reject operation_unclassified. Protocol acceptance passed Edge 25/25 and Cloud 59/59 before integration. -->

## 4. Edge core and browser executor lifecycle

- [x] 4.1 Refactor each environment handle into independently observable core and browser-executor resources, including separate status, ownership, cleanup and restart policies.
- [x] 4.2 On successful customer login/roster refresh, bootstrap all owned, trustworthy environments as browserless cores with bounded concurrency, jittered backoff and per-environment circuit breaking; do not call AdsPower, CDP or the browser slot queue.
- [x] 4.3 Ensure customer logout, environment removal, ownership loss and binding conflict stop or restrict the affected core fail-closed without guessing identity or automatically opening a browser.
- [x] 4.4 Route `browser_lifecycle` and `page_automation` through on-demand executor acquisition: slot/memory grant, provider launch, CDP attach, real page identity recheck, account-change handling and page-task lease.
- [x] 4.5 Release browser lease/CDP/provider resources independently after stop or idle reclaim while keeping the core and Cloud transport online.
- [x] 4.6 Isolate browser/provider/CDP failure from the core process and add recovery paths that report executor/task failure without projecting core or Cloud offline.
  <!-- aidcp-edge 857d332: core bootstrap concurrency=3 with jittered exponential backoff and per-env circuit breaking; ownership/binding gates are fail-closed. CDP terminal/control failures now reset page work and enter browser standby in place while core/Cloud stay online. -->

## 5. Browser-independent recovery and Cloud switching

- [x] 5.1 Replace restart-all Cloud switching with an explicit per-core control-transport rebind that drains in-flight page work to a safe boundary, stops old-Cloud intake and connects the selected target without starting, stopping or reallocating browser slots.
- [x] 5.2 Track and expose each environment's actual Cloud, target Cloud and rebind failure independently; apply the Facebook browse mode only after successful rebind and preserve the prior browser open/closed state.
- [x] 5.3 Implement Cloud-issued short-lived, single-purpose offboard cleanup grants bound to `offboardId/envKey/accountId/edgeId`, including use-once validation and audit.
- [x] 5.4 Replace `queueStartEnv`-based offboard recovery with a restricted browserless cleanup core that can only receive and report its bound cleanup command and fails to manual handling on expired/mismatched grants.
  <!-- aidcp-edge 857d332 / aidcp-cloud f57bfb7: per-core rebind reports partial results and never touches provider/CDP/slots. HMAC cleanup grants are 10-minute, scope-bound, hash-stored, audited and atomically use-once; restricted cleanup runtime exposes only offboard command/ack. -->

## 6. Migrate browser-independent client operations

- [x] 6.1 Move persona status, generate and confirm IPC bridges to Electron-main customer-auth requests; keep tokens and authoritative account IDs out of renderer state and remove `handle.child`/browser/CDP/slot gates.
- [x] 6.2 Move pending-draft image deletion and approve/reject IPC bridges to Electron-main customer-auth requests, refresh from server-returned truth and keep accepted/queued/published outcomes distinct.
- [x] 6.3 Classify and migrate all identified `platform_api` operations to the browserless core path, adding an explicit browser-auth-recovery transition only for platform responses that truly require human login or verification.
- [x] 6.4 Remove incidental browser startup from local settings, notification, content-state and cleanup actions; add regression assertions that these paths never call provider, CDP, slot or page-lease APIs.
  <!-- aidcp-edge 857d332: named customer-auth IPCs retain token/account binding in Electron main; renderer settings projection redacts cleanup credentials and authoritative account IDs. WeChat API-only sync/reply/reconcile remain core-local; only explicit auth/browser-control transitions can acquire a browser. -->

## 7. Client state model and interaction copy

- [x] 7.1 Replace the combined environment-running projection with independent core, Cloud, automation and browser state axes in Electron IPC snapshots and renderer stores, clearing stale per-account projections on customer/environment changes.
- [x] 7.2 Replace the legacy “启动环境” intent with separate “开始/暂停自动化” and “打开/关闭浏览器” actions while showing the customer-login core bootstrap as normal online lifecycle.
- [x] 7.3 Update persona, draft, settings and environment-row gates/copy to name their real customer-auth, binding or Cloud prerequisite and remove non-automation “启动浏览器/等待槽位” guidance.
- [x] 7.4 Add honest UI states for page-task queued, decision accepted/pending execution, executor error, core reconnect, target-Cloud pending and per-environment rebind failure without collapsing them into success or offline.
  <!-- aidcp-edge 857d332: snapshots expose coreState/cloudState/automationState/browserState. Renderer actions/copy and approval receipts preserve paused vs closed, accepted vs published, executor error vs core offline, and actual vs target Cloud. UI/fleet/renderer suites cover these projections. -->

## 8. Validation, integration and rollout

- [x] 8.1 Add Cloud security/behavior tests for environment ownership, binding failure, cross-account drafts, idempotency/CAS/version gates, approval-receipt truthfulness, persona parity and restricted cleanup grants.
- [x] 8.2 Add Edge lifecycle tests covering customer-login auto-bootstrap, zero/full slots, AdsPower unavailable, CDP absent, browser crash, unknown operations, independent release and no implicit browser start.
- [x] 8.3 Add integration tests proving persona, draft edit, approval/reject, configuration and representative API-only operations work with browser closed while page automation still queues and performs page identity/lease checks.
- [x] 8.4 Add Cloud-switch and offboard recovery tests proving neither path starts a browser or changes slot ownership, including partial rebind failure and cleanup-grant mismatch.
- [x] 8.5 Run the required focused suites, protocol/risk/publish acceptance suites, full tests and typechecks in the owning `aidcp-cloud`/`aidcp-edge` worktrees; retain concise evidence and resolve all failures before integration.
  <!-- Post-rebase validation: aidcp-edge full 1961/1961, acceptance 25/25, typecheck/build pass; aidcp-cloud full 2650 pass + 8 gated skips, acceptance 59/59, typecheck pass. Focused customer-auth/publish/handler/cleanup and lifecycle/registry/bootstrap/UI/rebind/offboard suites also passed. -->
- [x] 8.6 Measure browser-closed multi-environment core memory, bootstrap concurrency and reconnect backoff at the supported environment ceiling; record acceptance thresholds/results and optimize rather than limiting cores by browser slots.
  <!-- Canonical aidcp-edge 857d332 on macOS arm64/Node 25.5.0: 12/12 cores completed hello, 0 browser processes; RSS total 1698.3 MiB, average 141.5 MiB, max 150.9 MiB, below 1920/160/180 thresholds. Bootstrap concurrency remains 3 and core count is not limited by browser slots. -->
- [x] 8.7 Rebase and fast-forward integrate each clean sibling branch serially, record commit SHAs/validation/deviations in this `tasks.md`, and push the default branches without packaging an Edge installer.
  <!-- Rebasing incorporated Edge upstream aac77e4 and Cloud upstream 1710f9c; conflicts retained both manual-alias sync and core bootstrap, and both alias/offboard imports. Fast-forward pushed aidcp-cloud master=f57bfb7 then aidcp-edge master=857d332. No Edge package built. -->
- [x] 8.8 Run `scripts/deploy-target dev --check`, deploy additive Cloud runtime changes to `dev`, verify service/listener/health/logs and then complete dev Edge source/runtime acceptance; record unavailable real-machine cases in `docs/real-machine-acceptance-backlog.md`.
  <!-- deploy-target dev check passed. Backups: /opt/aidcp/cloud.bak.20260720-052714Z.tar.gz and matching .env.bak. Applied additive migration 0049; four cleanup_grant columns verified. Dev service active since 2026-07-20 13:28:30 CST; 8787/8090/8091 listening, both health routes ok, PostgreSQL select 1, Feishu WS onReady, and isales-api/isales-scheduler remained active. Source hashes match canonical f57bfb7. Unavailable installed-client/real-platform cases are backlog cluster 109. -->
- [x] 8.9 Run `openspec validate separate-client-core-browser-executor --strict` after implementation evidence is recorded and archive only when every required code, compatibility, validation and dev rollout task is complete.
  <!-- openspec validate separate-client-core-browser-executor --strict passed after tasks 1.1-8.8 and dev rollout evidence were complete; archive eligibility confirmed with no incomplete implementation task. -->
