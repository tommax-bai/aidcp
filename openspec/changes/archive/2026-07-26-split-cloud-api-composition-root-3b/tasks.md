## 1. Admission and baselines

- [x] 1.1 Create isolated `codex/split-cloud-api-composition-root-3b` worktrees for control, Cloud, kernel, transport, API, automation, content, and Edge; keep canonical checkouts and unrelated changes untouched.
  <!-- Seven initial matching worktrees were created from current defaults: control 1c88d18, cloud 3d28b48, kernel f7bceaf, transport b754bc8, api 72858c9, automation 7c7848f, edge 62b979c. The approval-internal-auth audit then made content a genuine changed transport consumer, so an eighth worktree was added from content c023f70. Each implementation worktree received an independent physical node_modules directory and none was symlinked; package pins and lockfiles were updated in their owning repositories. Canonical control's unrelated output/pdf and tmp/pdfs files remain untouched. -->
- [x] 1.2 Record the 3a source, package pin, migration, focused-test, and split-sync baselines before changing the fact source.
  <!-- 3a evidence remains cloud 5b35d0a, kernel f7bceaf, transport b754bc8, api 72858c9, automation 7c7848f, content c023f70. Current Cloud baseline 3d28b48 passes acceptance 123/123 and boundary census with 0 forbidden/unwaived edges. Pins remain kernel f7bceaf / transport b754bc8; migrations api 53 and automation 43 including 0079. Read-only sync sees api 105/105, automation 203/203, kernel 90/90, transport 33/33 with only their expected composition roots; it also truthfully reports unrelated current fb-publish-fill-deadline content prompt/test drift, which this change will not overwrite. -->

## 2. Restricted recovery command and result

- [x] 2.1 Extend kernel and transport risk-command contracts with restricted-only submit/result methods, version and target validation, and the `processing|applied|refused|failed|unknown` result union.
- [x] 2.2 Add an additive automation-owner migration and store methods for account-scoped recovery results without changing existing signal/quota result compatibility.
- [x] 2.3 Make the automation consumer persist the actual `recoverRestricted()` write-after result, resume matching Edge instances only after `normal`, and record refusal or resume failure honestly.
- [x] 2.4 Add API-owner customer recovery submission and authenticated same-environment result polling with bounded quick completion, 200/202 mapping, and cross-account/target non-disclosure.
  <!-- Cloud fact source now submits/polls a dedicated account+target-scoped recovery command; migration 0080 is additive; the automation handler records true applied/refused/failed outcomes and only applied+normal resumes Edge. Customer POST/GET preserve 200/202/409/503/404 and never expose accountId. -->
- [x] 2.5 Update Edge main/renderer recovery flow to retain restricted state through 202 polling and clear it only on matching write-after `normal`.
  <!-- aidcp-edge c5c2baf: added scoped recovery-result IPC plus bounded envKey+commandId polling; 202 stays pending, only matching applied+normal clears restricted, and every delayed success/rejection rechecks the current envKey+commandId before mutating UI state. Focused Electron tests 87/87, full suite 2381/2381, typecheck and diff-check pass. Integrated and pushed to master; source only, no installer built or installed-client acceptance claimed. -->
- [x] 2.6 Cover controller races, HTTP route/client parity, target/account isolation, 200/202/error mapping, real resumed-edge counts, and stale UI responses with focused tests.
  <!-- Cloud final 3b focused slice passes 148/148 and includes startup backlog ordering, NULL/invalid resume stages, stable public errors and target/env/account isolation; Edge recovery/renderer focused slice passes 87/87. -->

## 3. Publish approval authority and trigger

- [x] 3.1 Extend approval authority store/API contracts with revision-CAS read, list, void, dispatching, consumed, release, and blocked-reason operations.
- [x] 3.2 Implement the API-owned versioned internal HTTP authority server and automation client with explicit not-found, conflict, target, unavailable, and unknown-result failures.
- [x] 3.3 Implement the API-to-automation short-ack trigger contract and route, separating `decision_recorded` from `human_reconfirm` and deduplicating only equivalent retries.
- [x] 3.4 Rewire approval outbox relay, manual reapproval, pending scan, and dispatcher progress to use the new ports while retaining the durable approval/outbox/scan recovery path.
- [x] 3.5 Prove revision CAS, first-write versus human-reconfirm semantics, trigger failure compensation, breaker behavior, and the absence of accepted-to-published status inflation with focused tests.
  <!-- Cloud fact source exposes seven versioned authority operations, a short-ack trigger receiver/client and an API-owned durable outbox relay. Dispatcher progress/void use expected revision; first writes rely on decision_recorded outbox, while authenticated already-decided approvals alone emit human_reconfirm. Cross-target collisions on the legacy global requestId key now fail closed without reusing another target's decision; replacing that key remains a separate contract migration. The final combined focused slice passes 148/148 and Cloud typecheck. -->

## 4. Panel event delivery

- [x] 4.1 Add kernel and transport contracts for versioned automation-to-API panel event delivery and an API-local fanout.
  <!-- Cloud fact source adds versioned deliveryId/target contract, HTTP route/client and API-local fanout; focused transport/fanout/WS tests are green. -->
- [x] 4.2 Make `PanelEventReplay` await its delivery sink so HTTP failure preserves the automation cursor, ordering, polling, LISTEN, and at-least-once replay.
  <!-- PanelEventReplay now awaits each sink delivery; response loss and rejection tests prove cursor hold, ordered retry and duplicate-at-least-once semantics. -->
- [x] 4.3 Implement API ingress and local WebSocket fanout, isolate individual subscriber failures, and register the route independently from config-mirror capabilities.
  <!-- API internal startup independently registers panel ingress; API-local fanout acknowledges no-subscriber delivery and isolates individual subscriber failures. -->
- [x] 4.4 Rewire the Cloud fact-source api/automation service-mode paths so API-mode panel delivery uses only API-local fanout and never reads the automation outbox, while automation mode owns replay and reaches API ingress through the HTTP port; preserve the extracted repositories' hand-written composition roots as reported 4a/4b gaps.
  <!-- composition-root-3b acceptance guards the source-mode wiring and proves that the API panel path has no automation outbox reader or EventBus. This is not boot proof for the extracted aidcp-api/aidcp-automation main files and does not claim those still-4a/4b-blocked processes have no foreign owner pools. -->
- [x] 4.5 Cover direct HTTP delivery, response loss/duplicate delivery, cursor hold-and-resume, no-subscriber acknowledgement, subscriber isolation, and authenticated WebSocket loopback.
  <!-- Panel transport/fanout/WS tests are included in the final 148/148 focused slice; source composition acceptance additionally guards API-local fanout and automation-owned relay wiring. -->

## 5. Shared-package synchronization

- [x] 5.1 Synchronize managed 3b fact-source members into kernel, transport, API, automation, and the changed content consumer without overwriting reported hand-written composition roots; update exact pins only in repositories that import changed shared packages.
  <!-- Integrated package/consumer SHAs: kernel 94fd279, transport f9a7276, api 4b6da8a, automation 483f9c3, content 4a32427. Transport pins kernel; API and content pin kernel/transport; automation pins kernel and keeps its managed local transport copy. Hand-written roots were not overwritten. -->
- [x] 5.2 Update `scripts/sync-split-repos` membership and migration expectations for every newly shared source, then record managed-source, pin, and migration drift separately from the expected reported hand-written-root differences.
  <!-- Final split-sync: kernel 91/91, transport 37/37, API 107/107 plus 53 migrations, automation 208/208 plus 44 migrations, content 83/83 plus 20 migrations; managed source and pins have zero drift. Expected non-zero residuals are API root + 5 legacy tests, automation root, and content 2 roots + 1 auth test. -->
- [x] 5.3 Run focused 3b tests and applicable build/typecheck gates in kernel, transport, API, automation, content, and Edge; for extracted API/automation record whole-repo composition-root blockers separately from strict 3b slices.
  <!-- kernel build/typecheck + 26/26; transport build/typecheck + 8/8 dist exports; API 79/79 + strict managed slice; automation 85/85 + strict managed slice; content 444/444 + typecheck/build; Edge 87/87 focused, 2381/2381 full + typecheck. API whole-root typecheck has 414 existing index/server errors; automation whole-root typecheck has 370 error lines and full tests have 26 existing root/fixture failures. No Edge installer or installed-client acceptance was run. -->

## 6. Cloud validation and DEV deployment

- [x] 6.1 Run Cloud focused and acceptance suites for risk honesty, publish authorization/resilience, event replay, transport parity, and cross-service ownership boundaries.
  <!-- aidcp-cloud 67941e4 after rebase: final focused 148/148; acceptance 127/127; boundary census 485/485 owned files and 0 cross-boundary edges. -->
- [x] 6.2 Run the Cloud full test suite and typecheck; fix every 3b regression and preserve any unrelated pre-existing failure as explicit evidence.
  <!-- aidcp-cloud 67941e4: full suite 3479 total / 3468 pass / 0 fail / 11 skip; npm run typecheck and git diff --check pass. The branch was fast-forward integrated and pushed to master. -->
- [x] 6.3 Rebase and fast-forward integrate each repository serially, rerun post-integration validation, and push the clean default branches.
  <!-- Clean default branches were pushed serially: cloud 67941e4, edge c5c2baf, kernel 94fd279, transport f9a7276, api 4b6da8a, automation 483f9c3, content 4a32427. Post-integration validations are recorded in 5.3, 6.1, and 6.2. -->
- [x] 6.4 Read the deployment guide, bind target `dev`, run `scripts/deploy-target dev --check`, back up required state, deploy the clean Cloud default branch to DEV monolith, and verify service/listener/health/Feishu/PostgreSQL evidence.
  <!-- Target dev passed preflight/check. Backups: cloud.bak.20260726-180453.tar.gz and .env.bak.20260726-180453. Deployed 67941e4; service active with NRestarts=0; 8787/8090 listen; panel and client-auth health pass; writer lock holders=1; RiskControllerRegistry and Feishu WSClient are ready. Migration 0080 was concurrently applied to the shared ledger by external ol release-20260726-ol-current, not by this DEV deployment; DEV verified matching checksum, owner status 20/44/53, zero missing objects, and passing schema gates. -->
- [x] 6.5 Confirm and record that DEV remains the existing monolith, with independent API/automation listeners and units not started and 8093/8094 closed; do not repeat the known 4b-blocked cutover or claim independent-process acceptance.
  <!-- Runtime has AIDCP_DEPLOY_ENV=dev and no AIDCP_SERVICE. aidcp-api/automation/content units are not-found/inactive and 8092/8093/8094 are closed. This is monolith acceptance only; no independent-process or three-process claim is made. -->

## 7. Documentation and closeout

- [x] 7.1 Update `docs/cloud-composition-root-trisection.md` §10 with source, package, deployment, runtime-topology, and remaining 4a/4b evidence kept as separate claims.
  <!-- Section 10.9 now separates fact-source, derived-package, Edge source-only, DEV monolith, external shared-ledger migration, and unverified independent-process claims. -->
- [x] 7.2 Add concise completion comments to this checklist with repository, commit SHA, validation, deployment, and deviations for every completed group.
  <!-- Completion evidence above records each repository SHA and validation boundary, intentional sync residuals, existing 4a/4b blockers, external migration attribution, DEV topology, and the unperformed Edge installer gate. -->
- [x] 7.3 Run `openspec validate split-cloud-api-composition-root-3b --strict`, `git diff --check`, final managed-member/pin/migration split-sync checks with reported hand-written-root residuals preserved, and confirm every canonical checkout is on its default branch with unrelated changes preserved.
  <!-- After rebasing onto control main 6137b1c, control artifacts are commit 360fcd5; strict validation and diff-check pass. Final read-only split-sync has zero managed-source/pin/migration drift and exits 1 only for the reported API/automation/content hand-written roots and non-managed tests. All seven implementation canonical checkouts are clean on master with HEAD equal to upstream; control remains on main and its unrelated output/pdf and tmp/pdfs files are preserved. -->
