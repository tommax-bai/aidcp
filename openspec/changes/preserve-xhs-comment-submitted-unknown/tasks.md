## 1. Cloud implementation

- [x] 1.1 Add an exact submitted-unknown reason classifier in `aidcp-cloud/src/comment-agent/edge-steps.ts` and map all three known post-dispatch reasons to the existing `submitted_unconfirmed` result.
- [x] 1.2 Extend `aidcp-cloud/test/comment-agent/edge-steps.test.ts` to cover the two newly recognized reasons and retain submitted-before/unknown-failure/preemption boundaries.
- [x] 1.3 Add a targeted-comment regression proving the normalized submitted-unknown result writes dedupe and does not become `post_failed`.

## 2. Validation

- [x] 2.1 Run focused Cloud comment-agent tests proving receipt normalization and downstream dedupe/no-retry behavior. <!-- aidcp-cloud worktree: npx tsx --test test/comment-agent/edge-steps.test.ts test/comment-agent/comment-task-runner.test.ts test/comment-agent/targeted-comment-runner.test.ts test/delegated-task/executors.test.ts; 56 pass, 0 fail -->
- [x] 2.2 Run Cloud acceptance tests, full tests, and typecheck. <!-- aidcp-cloud worktree: acceptance 184 pass; full 4091 pass / 11 skip / 0 fail; typecheck exit 0 -->
- [x] 2.3 Run `openspec validate preserve-xhs-comment-submitted-unknown --strict` and `openspec validate --all --strict`. <!-- control worktree: change valid; all 211 items pass, 0 fail -->

## 3. Delivery

- [ ] 3.1 Record repository SHAs, validation evidence, deployment state, and deviations in this task ledger.
- [ ] 3.2 Rebase onto current default branches, fast-forward integrate, and push control `main` plus Cloud `master` after all gates pass.
- [ ] 3.3 Deploy the clean Cloud default branch to DEV, then verify the documented service, listener, health, and bounded logs without executing real-account actions.

<!-- Delivery evidence (updated 2026-08-02):
- aidcp-cloud implementation worktree commit: 2875244.
- Validation: focused 56 pass; acceptance 184 pass; full 4091 pass / 11 skip / 0 fail; typecheck exit 0.
- OpenSpec: change strict valid; all strict 211 pass / 0 fail.
- Deployment: pending clean-default integration.
- Deviation: added a targeted-comment regression after read-only adversarial review exposed the delegated retry path; no scope expansion beyond Cloud classification and tests.
-->
