## 1. Cloud receipt accounting

- [x] 1.1 Add a narrow Facebook comment accounting predicate that treats `verification_ambiguous` as consumed while leaving every other `ok=false` comment outside the durable risk ledger.
  <!-- aidcp-cloud worktree: handler now whitelists verification_ambiguous and explicitly excludes pending_group_approval/comment_rejected even under contradictory ok values. -->
- [x] 1.2 Route the ambiguous receipt through the existing envelope-idempotent outbox and `interaction.occurred` path without changing its non-success terminal outcome.
  <!-- Reuses the scoped Edge receipt key (account/environment/original envelope timestamp+id/action); handler regression proves enqueue + interaction.occurred while the original action.completed remains ok=false. -->
- [x] 1.3 Consume one active automatic-session comment budget unit for `verification_ambiguous` while keeping mandatory outcome `unknown` and `comment.done.ok=false`.
  <!-- RoleDispatcher consumes one unit only while pendingComment exists; duplicate terminal receipts cannot consume twice. -->

## 2. Regression coverage

- [x] 2.1 Prove confirmed and ambiguous comments enqueue/emit exactly once, including replay idempotency at the durable accounting boundary.
  <!-- Focused tests: handler-comment-accounting + risk-counter-outbox; repeated ambiguous key leaves one row/counter and day.comment=1. -->
- [x] 2.2 Prove pre-submit failure, participation approval, and platform rejection do not increment comment accounting.
  <!-- Focused handler matrix covers pending_group_approval, comment_rejected, editor_not_found, and marker_not_accepted. -->
- [x] 2.3 Prove the active session count includes an ambiguous submission without reporting it as confirmed.
  <!-- mandatory-comment-outcome verifies session totals.comments=1, outcome=unknown, comment.done.ok=false after duplicate terminal delivery. -->

## 3. Validation and delivery

- [x] 3.1 Run focused Cloud protocol/risk/dispatcher tests and `npm run typecheck`.
  <!-- 2026-07-28: `npx tsx --test test/handler-comment-accounting.test.ts test/integration/mandatory-comment-outcome.test.ts test/risk-counter-outbox.test.ts` passed 19/19 in 2.7s; `npm run typecheck` exited 0. -->
- [x] 3.2 Run required comment/risk acceptance coverage, the Cloud full test suite, and final typecheck.
  <!-- Final rebased source state: `npm run test:acceptance` passed 162/162; `npm test` reported 3773 tests with 3762 passed, 11 conditional skips, and 0 failures; final `npm run typecheck` exited 0. -->
- [x] 3.3 Run `openspec validate count-ambiguous-facebook-comment-submissions --strict` and record repository SHAs, validation, and deviations.
  <!-- Strict validation passed. Delivered repositories: aidcp-cloud master 3229333 and control main artifact commit 381664a; Edge and Console are unchanged. There are no protocol, schema, dependency, quota, retry, or success-surface deviations. Authorized real-account acceptance remains the explicit post-delivery boundary. -->
- [x] 3.4 Rebase the Cloud feature branch on the latest default, rerun the landing gate, fast-forward integrate, commit/push the control artifacts, and push both default branches without force.
  <!-- Cloud rebased cleanly onto origin/master a3f3b80, then the standard landing gate passed acceptance 162/162, full 3762 passed with 11 skips/0 failures, and typecheck before fast-forward push to master 3229333. Control artifact commit 381664a was pushed to main with only this change directory staged; no force push was used. -->
- [x] 3.5 Run the DEV deployment preflight, deploy only the clean integrated Cloud default revision, and verify service, listeners, health, Feishu, PostgreSQL, and deployed SHA without performing an unauthorized Facebook write.
  <!-- DEV 2026-07-28: `scripts/deploy-target dev --check` resolved 121.89.85.150 and the designated key. Backups `cloud.bak.20260728-154530.tar.gz` and `.env.bak.20260728-154530` preceded an rsync from clean Cloud `master` 3229333 with `.env`/`node_modules`/`.git` excluded; no dependency or migration files changed, post-sync checksum dry-run was empty, and the two changed runtime source hashes matched locally and remotely. `npm run migrate status` reported checksum-consistent ledgers and 0 pending for content/automation/api before restarting only `aidcp-cloud.service`. The service is active with NRestarts=0; 8787/8090/8091/5432 listen; panel/client-auth health and PostgreSQL SELECT 1 pass; all three enforce-mode schema gates, the dev automation writer lock, RiskControllerRegistry, and Feishu WS ready were logged; bot info is Dev.A/active; the post-restart error journal is empty; all four isales services remained active. No Facebook write or real-account acceptance was performed. -->
