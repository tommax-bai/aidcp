## 1. Contract and worktree setup

- [x] 1.1 Create isolated `codex/first-class-search-activity` worktrees for aidcp-cloud, aidcp-edge, and aidcp-console with physical dependencies <!-- aidcp-cloud/edge: npm ci --prefer-offline; aidcp-console: npm install --prefer-offline --no-package-lock because the repo has no lockfile -->
- [x] 1.2 Extend `docs/protocol.md` with search activity correlation, purpose/scope, actuation outcomes, capability negotiation, and compatibility rules <!-- additive wire fields, capability negotiation, legacy boundary, and fact semantics documented -->

## 2. Cloud risk model and persistence

- [x] 2.1 Add `search` to `RiskAction` and every exhaustive quota/default/slow-start mapping while keeping `InteractionAction` unchanged <!-- cloud: risk enums, 5/10/20 daily, 1/min, 4/hour, XHS/FB slow-start maps -->
- [x] 2.2 Add a forward PG migration and startup DDL support for `action='search'`, including quota configuration defaults and time-window query compatibility <!-- cloud: migrations/0055_first_class_search_activity.sql + startup constraint repair -->
- [x] 2.3 Add focused risk/quota/store tests for defaults, restricted-state zeroing, slow-start clamps, persistence, and dashboard aggregation <!-- focused Cloud risk/migration/panel tests pass; full evidence recorded in section 6 -->

## 3. Cloud search lifecycle

- [x] 3.1 Extend Cloud protocol types and capability negotiation for `search_activity_receipt_v1`, activity IDs, purpose/scope, actuation outcome, and visible result count <!-- capability is echoed only for declaring Edge connections -->
- [x] 3.2 Add the account risk pre-gate and bounded pending-activity state to autonomous search dispatch while preserving attempt budget and keyword limiter semantics <!-- risk -> keyword limiter -> session budget; attempts recorded only after real downlink -->
- [x] 3.3 Route valid one-shot `actuated=true` search completions through a dedicated internal search fact into `RiskController.record('search')`, without polluting interaction feeds <!-- actual downlink registry rejects unknown/duplicate/contradictory receipts -->
- [x] 3.4 Delay concept `markSearched` until an actuated receipt on capable Edge connections, preserve explicit legacy behavior for old Edge, and keep skipped/unsubmitted searches honest <!-- capable pending map bounded and session-cleared; legacy path explicitly retained -->
- [x] 3.5 Annotate autonomous, comment-task, and operator search commands with correct purpose/scope/activity IDs and add focused dispatcher/event tests <!-- current autonomous and task producers annotated; protocol/operator shape reserved for explicit operator commands -->

## 4. Edge execution receipts

- [x] 4.1 Extend Edge protocol types and advertise `search_activity_receipt_v1` as a build capability on every assembly path <!-- centralized EDGE_BUILD_CAPABILITIES merge covers all hello assembly paths -->
- [x] 4.2 Instrument XHS search submission and visible-card counting, then emit exactly one honest terminal receipt for results, no results, post-submit failure, or pre-submit failure <!-- Enter keyDown is actuation boundary; visible cards are deduplicated before count -->
- [x] 4.3 Instrument Facebook global search navigation and result verification with the same terminal receipt semantics <!-- explicit search commands force a correlated Page.navigate even on the same query -->
- [x] 4.4 Instrument Facebook container search submission and zero-result handling with the same terminal receipt semantics <!-- successful Page.navigate is the actuation boundary; empty candidates are no_results -->
- [x] 4.5 Add focused XHS and Facebook tests proving `actuated` boundaries, result counts, exact-once receipts, and compatibility defaults <!-- 22 focused Edge tests pass; full evidence recorded in section 6 -->

## 5. Console visibility

- [x] 5.1 Add `search` to Console risk-action enums, labels, ordering, quota tables, account activity totals, and unknown-value fallbacks <!-- search appears in global metric, account totals, and quota ordering; unknown fallback preserved -->
- [x] 5.2 Rename the mixed session section from “单场互动预算” to “单场行为预算” without changing its numeric contract <!-- searches numeric field remains unchanged -->
- [x] 5.3 Extend Cloud/Console live-enum drift and dashboard rendering tests for search usage, limits, and saturation <!-- focused Cloud panel and Console rendering/drift tests pass -->

## 6. Validation and integration

- [x] 6.1 Run focused Cloud acceptance/unit tests, the required full Cloud suite, and `npm run typecheck`; record exact evidence <!-- aidcp-cloud@ccc4e68152f616b92bce4ea76d1833df44f0c1bd; focused search/risk/panel suites pass; npm test: 2810 pass, 8 skipped, 0 fail, 52.23s on contention-free rerun; final post-rebase focused 88 pass; typecheck exit 0 -->
- [x] 6.2 Run focused Edge acceptance/unit tests, the required full Edge suite, and `npm run typecheck`; record exact evidence without building an installer <!-- aidcp-edge@7f1ee22ccb644121cd0bd964d8be8d1787680d3d; focused search suite: 22 pass before/after rebase; npm test: 2208 pass, 0 fail, 332.06s; typecheck exit 0; no installer build -->
- [x] 6.3 Run focused Console tests, its required full validation/build, and typecheck; record exact evidence <!-- aidcp-console@476647cc82e57a823ae061e8eb699d0591b7b4e1; focused: 14 pass, 1 skipped before/after rebase; contention-free npm test: 232 pass, 1 skipped, 0 fail, 53.68s; initial parallel run timed out under three-suite resource contention; final post-rebase production build: 3725 modules, 6.34s; typecheck exit 0 -->
- [x] 6.4 Run `openspec validate first-class-search-activity --strict` and update completed task evidence with repo commit SHAs and any deviations <!-- strict validation exit 0 before integration; commit SHAs appended during task 6.5 -->
- [x] 6.5 Rebase feature branches on current defaults, rerun affected checks, fast-forward integrate, and push aidcp-cloud/master, aidcp-edge/master, aidcp-console/master, and aidcp/main without overwriting unrelated changes <!-- feature commits aidcp-cloud@ccc4e68152f616b92bce4ea76d1833df44f0c1bd, aidcp-edge@7f1ee22ccb644121cd0bd964d8be8d1787680d3d, aidcp-console@476647cc82e57a823ae061e8eb699d0591b7b4e1, aidcp@da0d5c44714eabd1cce6e0983ff9875a154c8cd5 were rebased as required, revalidated, fast-forward integrated, and pushed; Cloud master advanced to 5f9d456044daccb266a90e0778c5364375316645 with a preserved concurrent migration-sequence fix; no force push -->

## 7. Dev deployment and runtime evidence

- [x] 7.1 Read deployment guidance, run `scripts/deploy-target dev --check`, back up dev, deploy clean integrated Cloud and Console revisions, and verify hashes/services/listeners/health/Feishu/PostgreSQL/logs as applicable <!-- target dev 121.89.85.150; backups /opt/aidcp/backups/cloud-20260722-155906.tar.gz, cloud.env-20260722-155906, console-20260722-155906.tar.gz, and database-20260722-155906.dump (488-entry pg_restore catalog including risk_counters/quota_config). Clean Cloud master 5f9d456 contained feature ccc4e68; rsync found the same source already synced by a concurrent dev deployment, and the 13 affected runtime files matched aggregate SHA-256 bae17864...d175a. Migration 0055 was then applied idempotently (0 prior search quota rows; inserted conservative 5/1/4, normal 10/1/4, aggressive 20/1/4) and only aidcp-cloud.service was restarted. Clean Console master 476647c deployed index-Ca0xo3XZ.js; index/JS/CSS SHA-256 matched local. Final service active, NRestarts=0, listeners 8787/8088/8090, local/public health and console routes HTTP 200, PostgreSQL select 1 plus search constraint/three quota rows verified, Feishu token/bot checks returned code 0 with Dev.A and WSClient onReady, no error-priority logs, and all four isales services remained active. OL was not contacted. -->
- [x] 7.2 Perform a bounded dev validation with a capable Edge if one is available: prove an actuated search increments once and an unsubmitted search does not; otherwise record the missing-client boundary without fabricating runtime proof <!-- authenticated read-only dashboard probe after deploy returned edgesOnline=0, accounts=36, searchTotal=0, and effective search quotas in the response. No online Edge existed, so no capable client or real platform search could be exercised; exactly-once/never-submitted behavior remains covered by the acceptance/unit suites and is not claimed as live-account proof. -->
- [x] 7.3 Confirm Edge source availability separately from installed-client/package availability and do not build or publish a desktop installer <!-- Edge source 7f1ee22ccb644121cd0bd964d8be8d1787680d3d is on origin/master; no desktop installer was built or published, so installed-client availability remains intentionally separate. -->
- [x] 7.4 Archive the OpenSpec change only after all required implementation, integration, deployment, and evidence tasks are complete <!-- all preceding implementation, validation, integration, dev deployment, runtime-boundary, and package-boundary tasks are complete; strict validation and archive follow in this closeout -->
