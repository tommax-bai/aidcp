## 1. Isolated setup

- [x] 1.1 Create matching `aidcp-edge` and `aidcp-cloud` worktrees from current default branches and install physical dependencies with `npm ci --prefer-offline`.
  <!-- Edge/Cloud worktrees created from origin defaults at 87cd1ab/3820eef. Physical npm ci --prefer-offline passed in both worktrees; no shared node_modules links. -->

## 2. Xiaohongshu Native task convergence

- [x] 2.1 Allow coordinator-admitted Native commands carrying the current task ID to execute while the ordinary browse lane is quiesced, without weakening stale/no-task suppression.
  <!-- aidcp-edge browse-session now admits only task-owned Native envelopes while quiesced; EdgeTaskCoordinator remains the stale-owner authority. Focused coordinator/session tests passed 36/36. -->
- [x] 2.2 Emit correlated, schema-valid Native search terminals for pre-actuation failure and successful page-card results using the original Cloud envelope metadata.
  <!-- Search activityId/purpose/scope survive Native routing; results_ready/no_results and not_submitted/failed_after_submit terminals are emitted with honest phase metadata. -->
- [x] 2.3 Add focused Edge tests for owned-task admission, ordinary/stale command rejection, correlated `not_submitted`, and `results_ready`/`no_results` reporting.
  <!-- npx tsx --test test/native-page-engine/browse-session.test.ts test/execution/edge-task-coordinator.test.ts test/native-page-engine/direct-routing-contract.test.ts: 36 passed, 0 failed. npm run typecheck also passed. -->
- [x] 2.4 Repair the live Native Xiaohongshu AI-search path for textarea geometry, trusted CDP input/readback, matching `search_result_ai` reuse, and bounded result-card hydration.
  <!-- Live acceptance exposed textarea[name=aiSearchTextarea] and late result hydration. Rust now owns trusted pointer/key/text actuation; the encoded geometry resource preserves the release verifier boundary. Native router contract and Rust suites passed. -->

## 3. Facebook Reels transition convergence

- [x] 3.1 Return structured Reels transition state that distinguishes ready card, confirmed route with late card, and navigation failure.
  <!-- aidcp-edge FacebookReelsReader.enter returns ready/route_ready/failed and confirms a canonical facebook.com/reel route independently from first-card hydration. -->
- [x] 3.2 Preserve pending Reels ownership and recover the current card before any next-Reel movement or Feed navigation.
  <!-- FacebookBrowseSession commits listMode=reels on route_ready, reports reels_pending, and calls settleActive before next; no Feed reader path is reachable while pending. -->
- [x] 3.3 Add focused Edge tests for late first-card rendering, pending recovery, zero false views, and no Reels-to-home rollback.
  <!-- Facebook session focused suite passed including the late-hydration regression; reels-reader 28/28 passed; npm run typecheck passed. -->

## 4. Cloud fallback recovery

- [x] 4.1 Track Facebook fallback authorization as idle, pending, or confirmed and perform bounded recovery for `reels_pending`/mixed-version `no_target` terminals.
  <!-- aidcp-cloud keeps a three-state handshake, confirms only from non-empty Reels cards, and permits at most two actually-dispatched compatibility retries. -->
- [x] 4.2 Add focused Cloud tests for pending retry, card confirmation, terminal reset, idempotence, quota/admission suppression, and unchanged non-Facebook behavior.
  <!-- facebook-empty-feed-reels-fallback 7/7 passed; combined RoleDispatcher/Facebook Reels focused run passed 54/54; npm run typecheck passed. -->

## 5. Validation

- [x] 5.1 Run Edge focused tests, acceptance, full tests, and typecheck with concise evidence.
  <!-- Final post-hotfix evidence: focused Native TS 11/11; Rust 34 unit + 1 contract + 4 fake-CDP + 1 process-protocol passed; Reels reader 28/28 plus Facebook late-hydration regression passed; acceptance 29/29; serialized Edge full suite 2248/2248; typecheck, build:dist, Native release verifier, and production-dist verifier passed. -->
- [x] 5.2 Run Cloud focused tests, acceptance, full tests, and typecheck with concise evidence.
  <!-- Focused RoleDispatcher/Facebook run 54/54; acceptance 68/68; full suite 2876 passed, 0 failed, 8 gated skips; typecheck and diff-check passed. -->
- [x] 5.3 Run protocol-drift checks and `openspec validate repair-page-command-state-convergence --strict`.
  <!-- Edge/Cloud AC-PROTO remained at v2/91 messages with no Surface expansion. openspec validate repair-page-command-state-convergence --strict passed. -->

## 6. Integration and DEV delivery

- [x] 6.1 Commit isolated Edge/Cloud/control changes, fetch/rebase onto latest defaults, revalidate, fast-forward push default branches, and record final SHAs without force.
  <!-- Edge master fast-forwarded/pushed at 424ef375 (base convergence 86d9a88 + Native AI-search parity); Cloud master fast-forwarded/pushed at 3d12d21b. Control proposal started at 15948bc and its final evidence commit is integrated by this task. No force push. -->
- [x] 6.2 Validate the source-built production components against the exact live XHS and Facebook accounts from correlated logs without performing a write interaction.
  <!-- XHS k1e0ero8: coordinator-owned Native search activity live-search-activity-20260722 completed results_ready with 29 real cards. Facebook So La/k1es0359: production FacebookBrowseSession + FacebookReelsReader entered Reel 1024088900337945 and emitted one real reels page.cards; no like/follow/comment was invoked. The naturally late-card branch is deterministic-regression covered; this live sample hydrated within the initial settle budget. Both AdsPower profiles were confirmed stopped after probing. -->
- [x] 6.3 Deploy the clean Cloud default branch to DEV only after target preflight and backup, then verify service, listeners, health, PostgreSQL, Feishu, and unchanged unrelated services.
  <!-- DEV 121.89.85.150 deployed from clean Cloud master 3d12d21b after deploy-target check. Backups: /opt/aidcp/backups/cloud-20260722-205440.tgz and cloud-env-20260722-205440. Only aidcp-cloud.service restarted; service/listener/health/version/PostgreSQL/Feishu passed and unrelated isales PIDs were unchanged. -->
