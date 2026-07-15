## 1. Session 00 - Contract and OpenSpec freeze

- [x] 1.1 Freeze `wechat_channels`, account/env ownership, browser sidecar, connector boundary and effective capability semantics.
- [x] 1.2 Freeze the seven WS v2 message types, capability negotiation, required payload fields, enums, errors and old/new peer compatibility.
- [x] 1.3 Freeze thread/message/batch/cursor/reply job/send attempt/config tables, unique keys, CAS versions and exact reply idempotency key.
- [x] 1.4 Freeze reply job/send attempt state machines, deterministic/AI stages, all-send gates, auto-only gates and ambiguous fail-closed behavior.
- [x] 1.5 Freeze customer-auth/internal API paths, success/error envelopes, pagination, permissions and immutable config publishing.
- [x] 1.6 Freeze renderer shell/workspace boundaries, credential locality, identity isolation, log redaction, retention defaults and non-destructive acceptance boundary.
- [x] 1.7 Publish strict JSON schemas and synthetic WS/customer/internal/AI fixtures, including one confirmed comment walkthrough and one ambiguous DM walkthrough.
- [x] 1.8 Validate the OpenSpec change strictly, validate every fixture against its schema, scan for message-name aliases and review compatibility evidence.
- [x] 1.9 Freeze durable reply-result acknowledgement and recovery semantics, including the exact message type, payload, correlation, duplicate/rejection behavior, compatibility negotiation, schemas and fixtures.
- [x] 1.10 Freeze the explicit offboarding contract for environment unbind/delete and customer termination: exact event/command/ack names, durable state, scope and reason fields, idempotency, ordering, retry/reconnect behavior, tombstone/purge deadlines, redacted audit shape, compatibility negotiation, schemas and fixtures.

<!-- Session 00 evidence: aidcp contract commit a6780030b735f6c30b46d552423a0331f27ad48e; `openspec validate wechat-channels-interaction-management --strict` passed; 7 draft 2020-12 schemas and 36 synthetic fixtures passed; message alias scan was clean; docs/spec-only, so no Edge/Cloud/Console implementation or deployment was performed. -->

<!-- Session 00 recovery/offboarding closure: the frozen v1 extension now contains 89 WS v2 message types and 44 fixtures. `interaction_reply_recovery_v1` freezes exact result ack plus verification-only reconciliation; `interaction_offboarding_v1` freezes revoke-first command/result/ack, the welcome reconnect barrier, durable retries and <=30-day purge. All seven metaschemas and all WS/customer/internal/AI/walkthrough fixtures passed `check-jsonschema`; `openspec validate wechat-channels-interaction-management --strict` passed. -->

## 2. Session 01 - Edge driver and interaction connector

- [x] 2.1 Extend Edge `PlatformId`, registry, environment configuration and capability declaration for `wechat_channels` without changing existing XHS/Facebook behavior.
- [x] 2.2 Implement the separate browser driver and `InteractionConnector`, with account-bound encrypted session storage, identity mismatch fail-closed behavior and browser reopen lifecycle.
- [x] 2.3 Implement comment and DM incremental sync with stable external IDs, paging, tombstones, replayable batches and checkpoint advancement only after a matching accepted/duplicate ack.
- [x] 2.4 Implement text comment/DM send with persisted idempotency, command expiry, platform verification and honest confirmed/failed/ambiguous results; keep image send disabled.
- [x] 2.5 Wire all seven WS types, payload validators and active-command routing atomically; gate them behind negotiated `interaction_inbox_v1`.
- [x] 2.6 Add per-capability probes, endpoint/account flags, schema-change circuit breaking and read-only/gated black-box tests that never submit to an unapproved real target.
- [x] 2.7 After 1.9, implement an Edge durable result outbox, resend unacknowledged results after restart/reconnect and clear only a scope-matching durable Cloud acknowledgement.
- [x] 2.8 After 1.10, implement the Edge offboarding consumer so it durably claims a scope-bound command, stops new sync/write and drains in-flight work, clears the encrypted session, closes the sidecar, persists/retries the acknowledgement after restart/reconnect, and never maps ordinary pause/close/standby to credential deletion.

<!-- Session 01 evidence: aidcp-edge branch/worktree `wechat-channels-edge-adapter` was rebased onto origin/master cb9aeba; implementation commit cdc3ffc and delegated-action registry follow-up 777b30f. The follow-up declares every outbound delegated action unsupported for the inbound-only wechat_channels v1 adapter, avoiding both the latest master type drift and false capability advertising. `npm test` passed 1393/1393, `npm run test:acceptance` passed 20/20, `npm run typecheck` and `npm run build:dist` passed. Frozen Session 00 WS fixtures were accepted by the Edge validators and `check-jsonschema --schemafile ws-v2.schema.json ../fixtures/ws/*.json` passed before the rebase; the rebased full protocol/adapter suite remains green. Tests used synthetic/mock data only; no real QR scan, identity binding, browser cold-stop, Connector online validation, real-account read, or write was performed, and all write probes remain gated. No Edge installer, Cloud/Console/Electron UI change, deployment, or dev publish was performed; integration and real-account acceptance remain Session 05 work. -->

<!-- Session 06 P1 follow-up: aidcp-edge commit c4dcf79 adds account/idempotency-key in-process single-flight, an atomic persisted claimed/executing/completed state machine, same-critical-section attempt binding, restart-safe verification without platform resend, v1 state migration, and barrier concurrency tests. `npm test` passed 1398/1398, `npm run test:acceptance` passed 20/20, `npm run typecheck` and `npm run build:dist` passed. The separate result-recovery P1 remains open: frozen v1 has no Cloud-to-Edge reply-result acknowledgement, so Edge cannot implement ack-only outbox cleanup without Session 00 changing the contract. Merge, real writes and automatic mode remain blocked until 1.9, 2.7 and 3.8 are complete. -->

<!-- Session 01 recovery/offboarding closure: aidcp-edge commit 49028a4 adds the v3 durable result/offboard outboxes, exact scope-matching ack cleanup, reconnect replay, verification-only reconciliation, connector drain-before-clear ordering, encrypted-session clear and sidecar close, plus the fail-closed welcome barrier. After rebasing onto current master, typecheck/build passed, the full suite passed 1479/1479, and acceptance passed 22/22, including disconnect/restart/unconfirmed Cloud ack, no blind write resend, concurrent duplicate offboard, and offline cleanup recovery. All private read/write flags remain off by default; no real platform write or installer build was performed. -->

## 3. Session 02 - Cloud inbox, workflow and APIs

- [x] 3.1 Allocate the next migration ID from current Cloud `master`, create the additive interaction/config/audit tables and enforce all frozen unique keys and account/env scope indexes.
- [x] 3.2 Implement transactional sync batch ingestion, duplicate ack replay and authoritative cursor advancement without reusing outbound `interaction_feed`.
- [x] 3.3 Implement unique reply jobs, monotonic CAS, send attempts, state transitions, ambiguous verification and no automatic ambiguous retry.
- [x] 3.4 Implement deterministic rule/template rendering, immutable published config snapshots, the three strict AI roles and their fail-closed fallbacks.
- [x] 3.5 Implement all-send/auto-only gates, `dm_reply` fallback quotas of zero, single-account send serialization and confirmed-only `RiskController.record`.
- [x] 3.6 Implement customer-auth and internal APIs exactly as frozen, including JWT domains, enabled-user/env scope checks, permissions, opaque pagination, preview and audit.
- [x] 3.7 Implement runtime controls, kill switches, retention/purge jobs, redacted logs and metrics with all real write flags defaulting off.
- [x] 3.8 After 1.9, durably acknowledge reply results and reconcile recoverable attempts on Cloud startup and Edge reconnect by replaying the same attempt/idempotency identity without blind platform resend.
- [x] 3.9 After 1.10, implement Cloud offboarding orchestration for unbind/delete/customer termination: revoke access and stop dispatch first, persist and retry the Edge cleanup command, tombstone only after a scope-matching Edge acknowledgement, schedule scope purge within 30 days, and retain only body-free audit events.

<!-- Session 02 evidence: aidcp-cloud implementation commit c9de73c833715d2a4590b609a691c4885280d974 was fast-forwarded to and pushed on `master`, then deployed to `dev` (121.89.85.150) from a clean snapshot. Migration `0039_interaction_inbox.sql` applied transactionally after Cloud, `.env`, and PostgreSQL schema backups (`cloud-session02-20260715-184142*`); all 15 domain tables, reply-job uniqueness, active job/account attempt indexes, and the widened `dm_reply` risk constraint were verified. Local full tests, PostgreSQL interaction integration, typecheck, build, exact frozen-fixture comparison, and all five contract schema validations passed; ECS typecheck also passed after sync. Post-restart evidence: `aidcp-cloud.service` active with `NRestarts=0`, listeners 8787/8090/8091/8088 present, panel/public health both `{"ok":true}`, PostgreSQL healthy, interaction domain ready, customer-auth/panel unauthenticated probes returned 401, and Feishu `WSClient onReady` was observed. The global interaction write flag, auto allowlist, DM AI, per-channel runtime writes, and `dm_reply` quota overrides remain off/empty; no real Video Channels login, read, or write was performed, so real-account acceptance remains Session 05. -->

<!-- Session 02 P0/P1 closure: aidcp-cloud commits 874ec19 and 15e05a5 remove customer self-attach, enforce globally unique authoritative env ownership, hold enabled-user + owner + account-binding locks through every customer interaction operation, add exact result acknowledgements/reconciliation, deterministic claim gates and human review for every AI-polished reply, and implement revoke-first offboarding/tombstone/purge with body-free audit. After rebasing onto current master, typecheck/build passed and the full suite passed 2238/2243 with five explicit gated tests; isolated PostgreSQL integration passed 5/5 including two-user isolation, unbind/termination, offline retry, tombstone/purge, races and mock Edge E2E. Migration 0041 remains additive and required before the new binary starts. -->

## 4. Session 03 - Console reply settings

- [ ] 4.1 Add `wechat_channels` account recognition and an interaction reply settings workspace that consumes the frozen internal API schema.
- [ ] 4.2 Implement policy, templates, rules and two-channel profiles with draft/published versions, aggregate CAS and permission-aware loading/error/conflict states.
- [ ] 4.3 Implement deterministic preview and publish validation views without creating real jobs, WS messages or send attempts.
- [ ] 4.4 Show hard gates, audit version/actor/time and DM-content permission boundaries honestly; cancel and clear stale state on account switch.

## 5. Session 04 - Electron interaction workspace

- [ ] 5.1 Select the right-side `InteractionWorkspace` for `wechat_channels` while preserving the global title bar, left environment rail and existing XHS/Facebook workspaces.
- [ ] 5.2 Implement inbox/detail, pagination and local refresh from the frozen customer API; route calls through named preload IPC and the existing client-auth session only.
- [ ] 5.3 Implement edit/regenerate/ignore/escalate/approve/send with `expectedVersion`, environment response checks and stale-request cancellation.
- [ ] 5.4 Render active+closed, reauth/challenge, queued/sending/sent/failed/ambiguous states truthfully; accepted or dispatched must never appear as sent.
- [ ] 5.5 Cover 820x720, keyboard/focus, empty/loading/error/permission/version-conflict and synthetic fixture/screenshot states without invoking a real write.
- [x] 5.6 After 1.10, route explicit environment deletion/unbind through the frozen offboarding path and show pending/offline cleanup truthfully without treating local profile deletion or ordinary logout as a completed credential purge.
- [x] 5.7 Disable every interaction write control and enforce the same handler gate while Cloud connectivity is offline or cached data is stale; restore writes only after a successful current-environment refresh and cover the transition with a renderer fixture.

## 6. Session 05 - Integration and real-account acceptance

- [ ] 6.1 Integrate the control contract, Cloud, Edge connector, Console and Electron branches serially, resolving only contract/integration defects and rerunning the required repo validations.
- [ ] 6.2 Verify old/new peer capability skew, restart/replay/cursor behavior, account/env isolation, CAS conflicts, kill switches, schema-change circuit breaking and retention/purge behavior with mocks first.
- [ ] 6.3 On a named dev account, run read-only authentication, identity, comment and DM sync acceptance before enabling any write capability.
- [ ] 6.4 Run comment/DM real writes only against operator-approved disposable targets, verify confirmed and ambiguous evidence boundaries, and record any gated/manual backlog honestly.
- [ ] 6.5 Update validation/deployment evidence, preserve unresolved compliance gates, deploy only through the documented dev path and do not archive until all required tasks are actually complete.
- [ ] 6.6 Verify unbind, customer termination and Edge-offline deferred cleanup end to end, including exact ordering, duplicate/restart recovery, encrypted-session deletion evidence, body-free audit and completion of the Cloud scope purge within the configured deadline; block real-customer onboarding, ol and Session 05 completion until 1.10/2.8/3.9/5.6 are complete.

<!-- Session 06 P1 offboarding follow-up: the frozen 83-type WS contract has no offboard command/event/ack or offline-replay semantics. Edge already has a scope-bound encrypted-session `clear()` primitive, but no authorized runtime route composes connector stop/drain -> credential clear -> durable ack; generic lifecycle pause/close/standby must preserve the API-only session. Cloud scope replacement and customer disable revoke HTTP access but create no durable offboard record, do not notify an offline Edge, and the existing retention sweeper only applies the 180/90/365-day age rules rather than an unbind-relative 30-day scope purge. Session 04 environment deletion currently removes the browser profile without proving Edge credential cleanup or Cloud tombstoning. No new message name or partial runtime path was invented; 1.10 must freeze the cross-repo protocol before 2.8/3.9/5.6 implementation. The separate stale/offline write gate landed in the Session 04 worktree as aidcp-edge commit 1995721; the targeted renderer fixture passed 8/8, including button disabled state, handler gating and recovery only after a successful current-environment refresh. -->

<!-- Session 04 offboarding closure: aidcp-edge commit dc9dac6 removes Electron customer self-attach and refuses unassigned roster writes. Video Channels deletion now persists the Cloud 202 offboard cursor, keeps a cleanup-only Edge alive across restart, polls authoritative status, shows pending/offline truth, and physically deletes the local profile only after Cloud tombstone/purge. After rebasing onto the recovered Edge adapter, typecheck/build passed and the full Electron/Edge suite passed 1498/1498; no installer was built and no real credential/profile was deleted. -->
