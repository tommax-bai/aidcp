## 1. Session 00 - Contract and OpenSpec freeze

- [x] 1.1 Freeze `wechat_channels`, account/env ownership, browser sidecar, connector boundary and effective capability semantics.
- [x] 1.2 Freeze the seven WS v2 message types, capability negotiation, required payload fields, enums, errors and old/new peer compatibility.
- [x] 1.3 Freeze thread/message/batch/cursor/reply job/send attempt/config tables, unique keys, CAS versions and exact reply idempotency key.
- [x] 1.4 Freeze reply job/send attempt state machines, deterministic/AI stages, all-send gates, auto-only gates and ambiguous fail-closed behavior.
- [x] 1.5 Freeze customer-auth/internal API paths, success/error envelopes, pagination, permissions and immutable config publishing.
- [x] 1.6 Freeze renderer shell/workspace boundaries, credential locality, identity isolation, log redaction, retention defaults and non-destructive acceptance boundary.
- [x] 1.7 Publish strict JSON schemas and synthetic WS/customer/internal/AI fixtures, including one confirmed comment walkthrough and one ambiguous DM walkthrough.
- [x] 1.8 Validate the OpenSpec change strictly, validate every fixture against its schema, scan for message-name aliases and review compatibility evidence.

<!-- Session 00 evidence: aidcp contract commit a6780030b735f6c30b46d552423a0331f27ad48e; `openspec validate wechat-channels-interaction-management --strict` passed; 7 draft 2020-12 schemas and 36 synthetic fixtures passed; message alias scan was clean; docs/spec-only, so no Edge/Cloud/Console implementation or deployment was performed. -->

## 2. Session 01 - Edge driver and interaction connector

- [x] 2.1 Extend Edge `PlatformId`, registry, environment configuration and capability declaration for `wechat_channels` without changing existing XHS/Facebook behavior.
- [x] 2.2 Implement the separate browser driver and `InteractionConnector`, with account-bound encrypted session storage, identity mismatch fail-closed behavior and browser reopen lifecycle.
- [x] 2.3 Implement comment and DM incremental sync with stable external IDs, paging, tombstones, replayable batches and checkpoint advancement only after a matching accepted/duplicate ack.
- [x] 2.4 Implement text comment/DM send with persisted idempotency, command expiry, platform verification and honest confirmed/failed/ambiguous results; keep image send disabled.
- [x] 2.5 Wire all seven WS types, payload validators and active-command routing atomically; gate them behind negotiated `interaction_inbox_v1`.
- [x] 2.6 Add per-capability probes, endpoint/account flags, schema-change circuit breaking and read-only/gated black-box tests that never submit to an unapproved real target.

<!-- Session 01 evidence: aidcp-edge branch/worktree `wechat-channels-edge-adapter` was rebased onto origin/master cb9aeba; implementation commit cdc3ffc and delegated-action registry follow-up 777b30f. The follow-up declares every outbound delegated action unsupported for the inbound-only wechat_channels v1 adapter, avoiding both the latest master type drift and false capability advertising. `npm test` passed 1393/1393, `npm run test:acceptance` passed 20/20, `npm run typecheck` and `npm run build:dist` passed. Frozen Session 00 WS fixtures were accepted by the Edge validators and `check-jsonschema --schemafile ws-v2.schema.json ../fixtures/ws/*.json` passed before the rebase; the rebased full protocol/adapter suite remains green. Tests used synthetic/mock data only; no real QR scan, identity binding, browser cold-stop, Connector online validation, real-account read, or write was performed, and all write probes remain gated. No Edge installer, Cloud/Console/Electron UI change, deployment, or dev publish was performed; integration and real-account acceptance remain Session 05 work. -->

## 3. Session 02 - Cloud inbox, workflow and APIs

- [ ] 3.1 Allocate the next migration ID from current Cloud `master`, create the additive interaction/config/audit tables and enforce all frozen unique keys and account/env scope indexes.
- [ ] 3.2 Implement transactional sync batch ingestion, duplicate ack replay and authoritative cursor advancement without reusing outbound `interaction_feed`.
- [ ] 3.3 Implement unique reply jobs, monotonic CAS, send attempts, state transitions, ambiguous verification and no automatic ambiguous retry.
- [ ] 3.4 Implement deterministic rule/template rendering, immutable published config snapshots, the three strict AI roles and their fail-closed fallbacks.
- [ ] 3.5 Implement all-send/auto-only gates, `dm_reply` fallback quotas of zero, single-account send serialization and confirmed-only `RiskController.record`.
- [ ] 3.6 Implement customer-auth and internal APIs exactly as frozen, including JWT domains, enabled-user/env scope checks, permissions, opaque pagination, preview and audit.
- [ ] 3.7 Implement runtime controls, kill switches, retention/purge jobs, redacted logs and metrics with all real write flags defaulting off.

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

## 6. Session 05 - Integration and real-account acceptance

- [ ] 6.1 Integrate the control contract, Cloud, Edge connector, Console and Electron branches serially, resolving only contract/integration defects and rerunning the required repo validations.
- [ ] 6.2 Verify old/new peer capability skew, restart/replay/cursor behavior, account/env isolation, CAS conflicts, kill switches, schema-change circuit breaking and retention/purge behavior with mocks first.
- [ ] 6.3 On a named dev account, run read-only authentication, identity, comment and DM sync acceptance before enabling any write capability.
- [ ] 6.4 Run comment/DM real writes only against operator-approved disposable targets, verify confirmed and ambiguous evidence boundaries, and record any gated/manual backlog honestly.
- [ ] 6.5 Update validation/deployment evidence, preserve unresolved compliance gates, deploy only through the documented dev path and do not archive until all required tasks are actually complete.
