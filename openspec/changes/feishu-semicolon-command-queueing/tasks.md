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

- [x] 5.1 Commit and push cloud/control feature branches, rebase onto current default branches, rerun required validation, and fast-forward land serially
<!-- repos: aidcp-cloud 8bde267 on master; aidcp 77b8a81 on main; feature branches pushed; validation stayed green -->
- [x] 5.2 Run `scripts/deploy-target dev --check`, inspect/backup the live cloud runtime and `.env`, deploy the clean `aidcp-cloud/master` snapshot, and restart only `aidcp-cloud.service`
- [x] 5.3 Verify dev service state, listeners, health, Feishu readiness, PostgreSQL, and deployed artifact hashes; roll back on any failed gate
<!-- dev deploy: cloud master 8bde267; backups: /opt/aidcp/backups/cloud.code.20260719-174127.tar.gz + cloud.env.20260719-174127; service active; 8787/8090 listening; health ok; PG aidcp=1; Feishu WS ready; five changed source hashes match -->
<!-- deployment deviation: rsync --delete removed 15 in-tree .env.bak.* files; all were immediately restored from the pre-deploy tar, current .env was never touched, and future syncs must exclude .env.bak.* -->

## 6. Event-driven real-environment acceptance

- [x] 6.1 Start the `Tianxing Bai` AdsPower environment directly without desktop-client startup or screen control, and attach protocol/event/log observation
<!-- real env: AdsPower k1ei3dbi -> dynamic CDP 56893 -> identity 61591753702668 / Tianxing Bai -> dev edge ads-k1ei3dbi; Electron was not started; AIDCP_FB_BROWSE_AUTO=off; profile stopped cleanly after observation -->
- [ ] 6.2 Submit the requested two-command batch and verify two independent tasks, complete flag propagation, one active Edge lease, equal-priority FIFO queueing, and zero wait-budget consumption
<!-- partial: production batch created publish task 03a15c6a... and facebook_group_comment 6bf4118d... with stable :command:1/:command:2 refs; comment constraints preserved force/joinGroup/manualSingle/injectContact. Blocker: ol and dev share PG, so ol old runtime claimed both rows; ol log proves publish-145 generation/card and comment recorded old deferred:edge_offline twice, exhausting 2 attempts before the dev Edge could receive it. No one-lease/FIFO/zero-budget live conclusion is claimed. -->
- [ ] 6.3 Complete normal approvals and verify the queued sibling automatically continues with no duplicate publish/comment; record any irreversible/manual boundary honestly
<!-- blocked by cross-environment claim ownership. Safety cleanup: publish task cancelled, candidate 145 moved pending_approval -> needs_review, comment task already failed without a platform write; post-run risk write counters for comment/publish/join_group were 0. Completing this needs explicit authority to isolate/pause ol claiming or a separate environment-affinity change. -->
