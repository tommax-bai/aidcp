## 1. Contract and Evidence Freeze

- [ ] 1.1 Freeze `interaction_runtime_controls_v1`, optional welcome snapshot, `interaction.runtime.controls` payload, scope/version rules, old/new peer behavior and active-command routing in Edge/Cloud protocol definitions, schemas, fixtures and `docs/protocol.md`.
- [ ] 1.2 Capture the real authorized video-channel session without submitting a write, produce a secret-free structural manifest for comment/DM endpoints, and explicitly mark every observed/dispatched/accepted/confirmed evidence boundary.
- [ ] 1.3 Adversarially review the identity bootstrap, account-control downlink and capture manifest for cross-account application, stale-version rollback, missing-snapshot enablement, credential leakage and fake-success claims.

## 2. Cloud Account Controls

- [ ] 2.1 Expose a fail-closed account-scoped runtime-control provider from `InteractionStore`, projecting `writePaused`, the global write gate, offboard state and exact `accountId + envKey + version` into the negotiated welcome snapshot.
- [ ] 2.2 After a successful internal-API CAS/audit update, push `interaction.runtime.controls` only to the matching negotiated Edge; record delivered/deferred truth without claiming Edge application.
- [ ] 2.3 Cover provider failure, account/env mismatch, global-write-off, offboard pending, offline Edge, multiple/wrong Edge, old peer and reconnect convergence in Cloud protocol/integration tests.

## 3. Edge Identity and Control Consumption

- [ ] 3.1 Make a new video-channel runtime derive its logical account scope from the stable environment key when no explicit migration override exists, while preserving existing XHS/Facebook identity behavior.
- [ ] 3.2 Separate logical `accountId` from durable `finderIdentity` in first bind, encrypted-session restore, periodic identity verification, send verification and mismatch handling; add legacy binding compatibility tests.
- [ ] 3.3 Replace per-account environment-variable grants with the negotiated account-control snapshot plus local build/probe/circuit/kill gates; missing, malformed, stale or wrong-scope controls keep all capabilities false.
- [ ] 3.4 Consume both welcome and online control updates with monotonic version/scope checks, reconnect reset and complete active-command routing; report effective capabilities after each accepted change.

## 4. Capture-Calibrated API Adapter

- [ ] 4.1 Introduce explicit per-endpoint request descriptors for method, path, query, encoding, non-secret headers, cookie-jar class, retry safety and success parsing.
- [ ] 4.2 Calibrate comment list/reply and DM session/history/send descriptors only from the sanitized real-session manifest; keep any uncovered write endpoint disabled.
- [ ] 4.3 Add golden serialization and redaction tests proving requests match captured structure without persisting Cookie/token/finder/message values, and keep schema drift isolated per endpoint.

## 5. User Guidance and Customer Projection

- [ ] 5.1 Update the Electron InteractionWorkspace to explain first binding, pending browser-open request, bound public identity, challenge, reauth and wrong-account recovery from structured auth state.
- [ ] 5.2 Make customer-auth environment resolution use the authoritative `envKey -> interaction account` binding and distinguish stored Cloud controls from Edge-applied effective capabilities/version.
- [ ] 5.3 Cover account switching, login-required, pending request, identity mismatch, stale control version, offline Edge and successful bind in renderer/customer API tests without invoking a real write.

## 6. Validation, Integration and Dev Closeout

- [ ] 6.1 Run Edge targeted tests, acceptance, full tests and typecheck; run Cloud interaction/protocol tests, acceptance, full tests and typecheck; run secret/cookie/token scans on all new evidence and fixtures.
- [ ] 6.2 Rebase and integrate Cloud then Edge through clean matching worktrees/default branches, commit and push each repo without building an Edge installer.
- [ ] 6.3 Run `scripts/deploy-target dev --check`, back up and deploy the clean Cloud default branch to dev, then verify service state, ports, health, Feishu/PostgreSQL and runtime-control handshake/update evidence.
- [ ] 6.4 On the named dev video-channel environment, verify real first authorization, identity binding, read-only comment/DM capture and account-control convergence; execute no real write unless the user supplies an exact disposable target.
- [ ] 6.5 Update this task file, the prior `wechat-channels-interaction-management` remaining acceptance tasks and `docs/real-machine-acceptance-backlog.md` with exact commits/deployment/evidence, keeping unexecuted real writes and offboarding visibly open.
- [ ] 6.6 Run `openspec validate wechat-channels-real-runtime-closure --strict` and report mock, real read-only, gated write, dispatched, accepted and confirmed scopes separately.
