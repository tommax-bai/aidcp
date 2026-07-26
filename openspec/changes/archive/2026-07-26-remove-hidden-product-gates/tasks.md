## 1. Cloud interaction authority

- [x] 1.1 Remove the automatic account allowlist from `InteractionSendOrchestrator`; add tests proving published scoped policy and safety gates are sufficient and stale allowlist values are inert.
- [x] 1.2 Remove the DM AI environment gate so published channel/rule configuration controls classification, polishing, review, and auto-send eligibility; update focused workflow tests.

## 2. Edge video-channel capability authority

- [x] 2.1 Remove local product authorization fields and environment parsing for interaction/account/channel/write gates while retaining scoped Cloud controls, identity, read evidence, endpoint circuits, lifecycle and test-only exact-target probes.
- [x] 2.2 Replace write-probe-approved capability admission with corresponding successful read-path evidence plus breaker health; update contract, probe, auth-session and runtime tests.
- [x] 2.3 Remove deprecated video-channel environment documentation/injection and prove stale local gate values do not change effective capabilities.

## 3. Content and Facebook automation authority

- [x] 3.1 Make `ContentScheduler` run on every valid deployment target, remove `AIDCP_CONTENT_SCHEDULE_AUTO` and legacy `AIDCP_PUBLISH_AUTO` trigger authority, and test default-off account actions.
- [x] 3.2 Remove Facebook comment auto/shadow/review environment authority; use scoped schedule/manual intent and structured approval policy, retaining validators, risk, quotas, idempotency and verification.
- [x] 3.3 Remove Facebook group-join auto/shadow environment authority; use scoped account automation configuration and existing schedule/risk/session/target gates.
- [x] 3.4 Remove `runtimeGate` environment declarations from the synchronized Cloud and Edge platform registries and update drift tests.
- [x] 3.5 Remove the comment-like global environment gate so configured quota/probability/risk controls are always authoritative; update role/store tests.
- [x] 3.6 Remove dev-only Facebook browse-mode injection and environment parsing while preserving platform/lifecycle/risk gating; update Electron/session tests.

## 4. Console and documentation

- [x] 4.1 Remove Console copy and source comments that instruct users to ask operations to enable hidden product gates.
- [x] 4.2 Update deployment and real-machine acceptance documentation to mark removed variables inert and describe the remaining visible/safety controls.

## 5. Validation and delivery

- [x] 5.1 Run focused Cloud interaction, workflow, scheduler, Facebook and registry tests; run safety acceptance/full tests and `npm run typecheck` as required.
  <!-- aidcp-cloud: focused suites passed after stale-gate expectation updates; npm test: 2,884 total, 2,876 passed, 8 skipped, 0 failed; test:acceptance: 68 passed; typecheck passed. -->
- [x] 5.2 Run focused Edge video-channel, Electron, Facebook session and registry tests; run safety acceptance/full tests and `npm run typecheck` as required.
  <!-- aidcp-edge: final targeted driver/reply run 27/27; npm test: 2,236/2,236; test:acceptance: 29/29; typecheck passed. -->
- [x] 5.3 Build/test Console and run `openspec validate remove-hidden-product-gates --strict`; record exact results and deviations.
  <!-- aidcp-console: 254 passed, 1 skipped, 0 failed; production build passed (3,725 modules). OpenSpec strict validation passed. No deviations. -->
- [x] 5.4 Commit each owning repo and control artifacts, fetch/rebase latest defaults, rerun affected validation, fast-forward integrate and push without disturbing unrelated work.
  <!-- Integrated and pushed: aidcp-cloud master 1d63b8f, aidcp-edge master 36df37d, aidcp-console master 883f673. Post-rebase Cloud typecheck + 111 focused tests, Edge typecheck + 27 focused tests, Console build, and OpenSpec strict validation passed. Existing Edge native/page-engine dirt and control work were preserved. -->
- [x] 5.5 Run dev deployment checks, back up and deploy eligible clean Cloud/Console revisions, then verify hashes, service/listeners/health, Feishu, PostgreSQL and bounded logs; do not claim Edge installed-client delivery without a new package.
  <!-- dev deployed 2026-07-22: preflight passed; backups cloud.bak.20260722-212656.tar.gz, console.bak.20260722-212656.tar.gz and .env.bak.20260722-212656 created. Retired env keys present on dev were removed after backup. Cloud 1d63b8f and Console 883f673 markers plus all changed Cloud/current Console artifact hashes matched local. aidcp-cloud.service active since 21:28:01 CST with NRestarts=0; 8787/8090/8091/8088/5432 listened; panel and client-auth health returned ok; public console returned 200; PostgreSQL SELECT 1 passed; Feishu bot identified as Dev.A and WSClient onReady logged; isales-scheduler remained active. ContentScheduler logged account configuration as the sole product authority. No real platform write was sent. Edge 36df37d is source-only: no installer was built or installed. -->
