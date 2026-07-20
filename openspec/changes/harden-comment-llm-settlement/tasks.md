## 1. Text LLM hard settlement

- [x] 1.1 Refactor `QwenClient.chat()` so `timeoutMs` races the full HTTP/body Promise, rejects with a stable timeout error even when fetch ignores Abort, and consumes late settlement without duplicate completion.
- [x] 1.2 Add safe call-start metadata plus terminal stage/request-id/timeout metadata while preserving existing token accounting and excluding prompts, response bodies, and secrets.

## 2. Comment-lane deadlines

- [x] 2.1 Add an optional per-role LLM timeout to `BaseRole` and inject a sanitized `AIDCP_COMMENT_LLM_TIMEOUT_MS` value (default 30s) into comment appraisal, composition, and de-AI rewrite roles only.
- [x] 2.2 Make comment composition stop retrying transport/timeout failures while retaining bounded retries for returned invalid content; preserve de-AI fallback and honest skip semantics.
- [x] 2.3 Reduce the default non-renewing comment-subline deadline from 15 minutes to 5 minutes without changing valid env overrides, single settlement, or late-event tombstones.

## 3. Regression coverage

- [x] 3.1 Add Qwen client regressions for fetch that ignores Abort and never settles, headers followed by a never-settling body, stable stages/request ID, one failed terminal record, and no late duplicate/unhandled rejection.
- [x] 3.2 Add BaseRole/comment-lane regressions proving the 30s per-call override reaches all three comment LLM roles, a composer timeout does not retry, and the normal content/language retry path remains.
- [x] 3.3 Run focused Qwen, comment-lane, and RoleDispatcher tests plus `npm run typecheck`; record exact results.
  <!-- PASS (aidcp-cloud): `node --import tsx --test test/qwen-hard-deadline.test.ts test/qwen-per-call-opts.test.ts test/qwen-provider.test.ts test/qwen-token-usage.test.ts test/agents/comment-lane.test.ts test/integration/role-dispatcher.test.ts` (72/72); `npm run typecheck`. -->

## 4. Full validation and integration

- [x] 4.1 Run Cloud `npm run test:acceptance`, full `npm test`, and `npm run typecheck` from the isolated worktree.
  <!-- PASS (aidcp-cloud): acceptance 62/62 with 1 gated E2E skipped; full 2705 passed, 8 gated skips, 0 failed; final typecheck passed. -->
- [x] 4.2 Update this task record with repo, commit SHA, validation results, deployment result, and deviations; run `openspec validate harden-comment-llm-settlement --strict`.
  <!-- PASS: aidcp-cloud commit `892a9a32f5448ed183e6d76be9ed53d750da3ab6`; focused 72/72, acceptance 62/62 with 1 gated E2E skip, full 2705 passed with 8 gated skips and 0 failures, final typecheck passed. OpenSpec strict validation passed. No protocol, schema, Edge, model-selection, or global 180s timeout changes; no deviations from the design. -->
- [x] 4.3 Commit and push the Cloud feature branch, rebase/fast-forward it into `origin/master` without force, then commit and push the control-repo OpenSpec artifacts.
  <!-- PASS: aidcp-cloud feature `codex/harden-comment-llm-settlement` pushed at `892a9a3` and fast-forwarded to `origin/master`; control artifacts committed at `6157206`, feature branch pushed, and this completion-record commit is fast-forwarded to `origin/main`. No force push. -->

## 5. Dev deployment and live verification

- [x] 5.1 Re-check the named `dev` target, back up Cloud runtime/env, deploy only from the clean canonical Cloud `master`, and restart only `aidcp-cloud.service`.
  <!-- PASS (dev 121.89.85.150): `scripts/deploy-target dev --check`; runtime backup `/opt/aidcp/cloud.bak.20260720-103505Z.tar.gz`; env backup `/opt/aidcp/cloud/.env.bak.20260720-103505Z`; deployed clean canonical master at `892a9a3`; restarted only `aidcp-cloud.service`. -->
- [x] 5.2 Verify service state, listeners, health endpoints, PostgreSQL, Feishu readiness, successful same-model probe, and a no-response local probe that settles at the hard deadline; do not trigger a real platform comment or claim one occurred.
  <!-- PASS: service active with NRestarts=0; listeners 8787/8090/8091; panel and client-auth health returned `{ok:true}`; PostgreSQL `SELECT 1` returned 1; Feishu emitted `WSClient onReady` and `ws client ready`; five deployed source hashes matched. `doubao-seed-character-260628` probe succeeded in 516ms with `body_parsed`, request ID, and one terminal record. Injected never-settling fetch failed once with `LlmTimeoutError` at 302ms (`request_started`, timedOut=true). No browser action or real platform comment was triggered. -->
