## 1. Cloud timeout implementation

- [x] 1.1 Add a bounded optional corpus lookup in `CommentComposer`: default 3s, timeout/error fallback to empty references, stable timeout log, timer cleanup, and injectable timing for tests.
- [x] 1.2 Add a non-renewing `commentInflight` total deadline in `RoleDispatcher`: default 15min, one honest `comment_subline_timeout` terminal event, release hold/clock before emitting the terminal event.
- [x] 1.3 Add expired-note guards across comment appraisal/composition/cleanup/approval and dispatcher delivery so late events cannot re-arm the hold, send a comment, or report success.
- [x] 1.4 Wire sanitized `AIDCP_COMMENT_CORPUS_LOOKUP_TIMEOUT_MS` and `AIDCP_COMMENT_SUBLINE_TIMEOUT_MS` values through the production server assembly without changing LLM or approval defaults.
  <!-- Repo: aidcp-cloud; commit b98e358. -->

## 2. Regression coverage

- [x] 2.1 Add a `CommentComposer` regression where corpus retrieval never settles; assert composition continues after the short timeout with no references and no unhandled failure.
- [x] 2.2 Add dispatcher regressions for total timeout release, restored idle nudge, single terminal settlement, and late `comment.appraised` / `comment.approved` no-op.
- [x] 2.3 Run focused comment/dispatcher tests and record the exact passing commands.
  <!-- PASS: `node --import tsx --test test/agents/comment-lane.test.ts test/integration/role-dispatcher.test.ts` (50 tests); `npm run typecheck`. -->

## 3. Validation and integration

- [x] 3.1 Run `npm run test:acceptance`, full `npm test`, and `npm run typecheck` in the isolated Cloud worktree.
  <!-- PASS: acceptance 60/60 (1 gated E2E skipped); full 2674 passed, 8 gated skips, 0 failed; typecheck passed. -->
- [ ] 3.2 Update this task record with repo, commit SHA, validations, deployment result, and any deviation; run `openspec validate bound-comment-subline-timeouts --strict`.
- [x] 3.3 Commit and push the Cloud change, fast-forward it into `origin/master` without force, then commit and push the control-repo OpenSpec artifacts.
  <!-- Cloud b98e358 pushed to the feature branch and fast-forwarded to origin/master; this control commit records the active OpenSpec artifacts. -->

## 4. Dev deployment and live verification

- [ ] 4.1 Re-check the named `dev` target, back up the Cloud runtime/env, deploy only from the clean canonical Cloud `master`, and restart only `aidcp-cloud.service`.
- [ ] 4.2 Verify service state, listeners, health endpoints, PostgreSQL and Feishu readiness; inspect bounded post-restart logs without claiming a real timeout occurred unless observed.
