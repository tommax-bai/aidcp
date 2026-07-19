## 1. Feishu batch admission

- [x] 1.1 Add a bounded `;` / `；` command-boundary splitter that preserves semicolons inside ordinary arguments and keeps the single-command path unchanged
- [x] 1.2 Add concurrent per-child routing with stable message-id + child-index source references and independent error settlement
- [x] 1.3 Update the fast-ack receiver to deliver each non-silent child result/card independently without adding startup-success cards
- [x] 1.4 Add parser/router/receiver tests for the requested publish + `--join --contact --force` example, partial rejection, replay dedupe identity, and non-boundary semicolons
<!-- repo: aidcp-cloud; commit: 8bde267; validation: feishu command/receiver focused tests pass; deviation: none -->

## 2. Delegated comment flags

- [x] 2.1 Project persisted `injectContact`, join/group URL, and force constraints into `CommentScheduler.triggerManual`
- [x] 2.2 Add executor regression tests proving all three switches compose and that automatic/non-manual tasks do not gain manual-only overrides
<!-- repo: aidcp-cloud; commit: 8bde267; validation: delegated executor tests pass; deviation: join-comment terminal not_started conservatively retains the ledger after possible join -->

## 3. Pre-start resource queue accounting

- [x] 3.1 Add an explicit machine-readable deferred shape for `attemptStarted:false`; only proven zero-command lease-acquire failures may use it
- [x] 3.2 Add an atomic store operation that removes the provisional attempt and reverses its dispatch count without changing success/skipped/failure counts
- [x] 3.3 Update the worker to use non-attempt defer accounting while preserving dispatched-attempt reconciliation for preemption and ambiguous submission
- [x] 3.4 Add store/worker/executor tests proving repeated browser waits remain deferred with zero attempt/failure/skipped budget and later execute after release
- [x] 3.5 Add negative regressions proving post-start defer/unknown results retain the attempt ledger and structural failures still terminate honestly
<!-- repo: aidcp-cloud; commit: 8bde267; validation: delegated parser/service/store/worker/executor focused group 160/160; deviation: none -->

## 4. Validation

- [x] 4.1 Run focused Feishu, delegated parser/service/executor/worker/store tests and `git diff --check`
- [x] 4.2 Run `npm run test:acceptance`, full `npm test`, and `npm run typecheck` in the cloud worktree
- [x] 4.3 Run `openspec validate feishu-semicolon-command-queueing --strict` and record exact validation evidence/deviations in this task file
<!-- validation: focused 160/160; acceptance 59/59; full 2552 pass, 0 fail, 8 skipped; typecheck pass; OpenSpec strict valid -->

## 5. Integration and dev deployment

- [ ] 5.1 Commit and push cloud/control feature branches, rebase onto current default branches, rerun required validation, and fast-forward land serially
- [ ] 5.2 Run `scripts/deploy-target dev --check`, inspect/backup the live cloud runtime and `.env`, deploy the clean `aidcp-cloud/master` snapshot, and restart only `aidcp-cloud.service`
- [ ] 5.3 Verify dev service state, listeners, health, Feishu readiness, PostgreSQL, and deployed artifact hashes; roll back on any failed gate

## 6. Event-driven real-environment acceptance

- [ ] 6.1 Start the `Tianxing Bai` AdsPower environment directly without desktop-client startup or screen control, and attach protocol/event/log observation
- [ ] 6.2 Submit the requested two-command batch and verify two independent tasks, complete flag propagation, one active Edge lease, equal-priority FIFO queueing, and zero wait-budget consumption
- [ ] 6.3 Complete normal approvals and verify the queued sibling automatically continues with no duplicate publish/comment; record any irreversible/manual boundary honestly
