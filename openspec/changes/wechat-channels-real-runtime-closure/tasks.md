## 1. Contract and Evidence Freeze

- [x] 1.1 Freeze `interaction_runtime_controls_v1`, optional welcome snapshot, `interaction.runtime.controls` payload, scope/version rules, old/new peer behavior and active-command routing in Edge/Cloud protocol definitions, schemas, fixtures and `docs/protocol.md`.
- [x] 1.2 Capture the real authorized video-channel session without submitting a write, produce a secret-free structural manifest for comment/DM endpoints, and explicitly mark every observed/dispatched/accepted/confirmed evidence boundary.
- [x] 1.3 Adversarially review the identity bootstrap, account-control downlink and capture manifest for cross-account application, stale-version rollback, missing-snapshot enablement, credential leakage and fake-success claims.

<!-- Evidence freeze (2026-07-16): the repository contains only a key/type manifest, no raw HAR or captured value. Review corrections renamed the comment call to commentPagePostList, page through currentPage rather than reusing lastBuff, extract only the matching post.commentList, reject unverified non-empty comments/DMs, reject same-version control mutation, and allow safety-control updates through the captcha pause gate. No platform write was dispatched. -->

## 2. Cloud Account Controls

- [x] 2.1 Expose a fail-closed account-scoped runtime-control provider from `InteractionStore`, projecting `writePaused`, the global write gate, offboard state and exact `accountId + envKey + version` into the negotiated welcome snapshot.
- [x] 2.2 After a successful internal-API CAS/audit update, push `interaction.runtime.controls` only to the matching negotiated Edge; record delivered/deferred truth without claiming Edge application.
- [x] 2.3 Cover provider failure, account/env mismatch, global-write-off, offboard pending, offline Edge, multiple/wrong Edge, old peer and reconnect convergence in Cloud protocol/integration tests.

<!-- Cloud implementation: aidcp-cloud master 42cd5f8. Migration 0042 records only the Edge-reported applied version; stored controls remain the authoritative CAS/audit state. -->

## 3. Edge Identity and Control Consumption

- [x] 3.1 Make a new video-channel runtime derive its logical account scope from the stable environment key when no explicit migration override exists, while preserving existing XHS/Facebook identity behavior.
- [x] 3.2 Separate logical `accountId` from durable `finderIdentity` in first bind, encrypted-session restore, periodic identity verification, send verification and mismatch handling; add legacy binding compatibility tests.
- [x] 3.3 Replace per-account environment-variable grants with the negotiated account-control snapshot plus local build/probe/circuit/kill gates; missing, malformed, stale or wrong-scope controls keep all capabilities false.
- [x] 3.4 Consume both welcome and online control updates with monotonic version/scope checks, reconnect reset and complete active-command routing; report effective capabilities after each accepted change.

## 4. Capture-Calibrated API Adapter

- [x] 4.1 Introduce explicit per-endpoint request descriptors for method, path, query, encoding, non-secret headers, cookie-jar class, retry safety and success parsing.
- [x] 4.2 Calibrate comment list/reply and DM session/history/send descriptors only from the sanitized real-session manifest; keep any uncovered write endpoint disabled.
- [x] 4.3 Add golden serialization and redaction tests proving requests match captured structure without persisting Cookie/token/finder/message values, and keep schema drift isolated per endpoint.

<!-- Edge implementation: aidcp-edge master d321042 (runtime closure dc6d507, capture correction a00ccc3 and Cloud-visible empty DM checkpoint d321042). Real auth evidence proved `_log_finder_uin` and `rawKeyBuff` are string fields that may be empty, while the remaining identity/query/header gates stay non-empty. Read coverage is deliberately limited to the captured empty result; commentCreate, dmSendText and dmNewMessages have no path and fail before fetch. No Edge installer was built or published. -->

## 5. User Guidance and Customer Projection

- [x] 5.1 Update the Electron InteractionWorkspace to explain first binding, pending browser-open request, bound public identity, challenge, reauth and wrong-account recovery from structured auth state.
- [x] 5.2 Make customer-auth environment resolution use the authoritative `envKey -> interaction account` binding and distinguish stored Cloud controls from Edge-applied effective capabilities/version.
- [x] 5.3 Cover account switching, login-required, pending request, identity mismatch, stale control version, offline Edge and successful bind in renderer/customer API tests without invoking a real write.

## 6. Validation, Integration and Dev Closeout

- [x] 6.1 Run Edge targeted tests, acceptance, full tests and typecheck; run Cloud interaction/protocol tests, acceptance, full tests and typecheck; run secret/cookie/token scans on all new evidence and fixtures.
- [x] 6.2 Rebase and integrate Cloud then Edge through clean matching worktrees/default branches, commit and push each repo without building an Edge installer.
- [x] 6.3 Run `scripts/deploy-target dev --check`, back up and deploy the clean Cloud default branch to dev, then verify service state, ports, health, Feishu/PostgreSQL and runtime-control handshake/update evidence.
- [x] 6.4 On the named dev video-channel environment, verify real first authorization, identity binding, read-only comment/DM capture and account-control convergence; execute no real write unless the user supplies an exact disposable target.
- [x] 6.5 Update this task file, the prior `wechat-channels-interaction-management` remaining acceptance tasks and `docs/real-machine-acceptance-backlog.md` with exact commits/deployment/evidence, keeping unexecuted real writes and offboarding visibly open.
- [x] 6.6 Run `openspec validate wechat-channels-real-runtime-closure --strict` and report mock, real read-only, gated write, dispatched, accepted and confirmed scopes separately.

<!-- Validation through Edge master d321042: root-cause auth/store tests passed 10/10, DM/sync targeted tests passed 6/6, Edge acceptance 22/22, full tests 1520/1520 and typecheck passed. Cloud master 42cd5f8 passed acceptance 54/54, full tests 2279 passed with five explicit skips, and typecheck. Secret scans found no captured credential values. -->

<!-- Dev deployment (2026-07-16): `scripts/deploy-target dev --check` selected dev. Clean Cloud master 42cd5f8 was backed up at `/opt/aidcp/backups/wechat-runtime-closure-20260716-164520`, migration 0042 applied, ECS typecheck passed and `aidcp-cloud.service` restarted healthy. To use the supported audited panel CAS, one existing panel actor received only `interaction.config.view/edit`; the pre-change env is `/opt/aidcp/backups/wechat-runtime-grants-20260716-170833.env`. After restart the service was active with NRestarts=0, ports 8787/8088/8090/8091 listened, all three real health routes, PostgreSQL SELECT 1, Feishu ready and interaction-domain ready passed, and the critical startup error scan was zero. No username, password, token or captured platform value was recorded. -->

<!-- Named-account real read-only acceptance (2026-07-16): result PASS_EMPTY_ONLY. Edge master d321042 first bound the real public identity, encrypted the authorized session and closed the browser; AdsPower was inactive at completion. The supported account CAS advanced controls 0 -> 1, reported delivered=1, and Edge reported applied version 1. Only commentsRead/dmRead are true; every reply/send/image write is false and writePaused remains true. With the browser closed, Cloud accepted one comment and one DM root-scope empty batch, retained one cursor per channel, persisted zero threads/messages and recorded zero send attempts. After two polling rounds each channel still had exactly one batch, and foreign-scope batches remained zero. Real evidence is therefore limited to empty comments and empty DM history/session-info. Non-empty comment/DM parsing, every platform write, ambiguous-write recovery, offboarding and packaged Edge remain unexecuted; no platform write was dispatched, accepted or confirmed. -->
