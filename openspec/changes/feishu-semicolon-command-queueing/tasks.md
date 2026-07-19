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
- [x] 3.6 Persist exact manual `/publish` human lease priority across approval/redispatch while leaving ordinary approved candidates automatic
<!-- repo: aidcp-cloud; commit: 8bde267; validation: delegated parser/service/store/worker/executor focused group 160/160; deviation: none -->
<!-- priority follow-up: aidcp-cloud c874d3e; exact manual marker is frozen before approval and reconstructed by dispatcher; ordinary approved candidates remain automatic; persistence failure returns needs_review and sends no approval card; focused 77/77, acceptance 59/59, full suite exit 0, typecheck pass -->

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
<!-- priority follow-up deploy: cloud master c874d3e; backups: /opt/aidcp/backups/cloud.code.20260719-185219.tar.gz + cloud.env.20260719-185219; sync omitted --delete and excluded .env/.env.*; service active; 8787/8090 listening; health ok; PostgreSQL ready; Feishu WS ready; five changed source hashes match -->

## 6. Event-driven real-environment acceptance

- [x] 6.1 Start the `Tianxing Bai` AdsPower environment directly without desktop-client startup or screen control, and attach protocol/event/log observation
<!-- real env: AdsPower k1ei3dbi -> dynamic CDP 55227 -> identity 61591753702668 / Tianxing Bai -> dev edge ads-k1ei3dbi; Electron was not started; AIDCP_FB_BROWSE_AUTO=off; SIGINT invoked the Edge-owned V2 stop and the read-only active endpoint returned Inactive -->
- [x] 6.2 Submit the requested two-command batch and verify two independent tasks, complete flag propagation, one active Edge lease, equal-priority FIFO queueing, and zero wait-budget consumption
<!-- partial: production batch created publish task 03a15c6a... and facebook_group_comment 6bf4118d... with stable :command:1/:command:2 refs; comment constraints preserved force/joinGroup/manualSingle/injectContact. Blocker: ol and dev share PG, so ol old runtime claimed both rows; ol log proves publish-145 generation/card and comment recorded old deferred:edge_offline twice, exhausting 2 attempts before the dev Edge could receive it. No one-lease/FIFO/zero-budget live conclusion is claimed. -->
<!-- second probe with ol temporarily stopped: first batch comment c033ede5... completed a real join+contact comment despite saturated quotas; publish b56b73ad... failed honestly on missing writing_language. After setting Tianxing Bai writing_language=vi through the existing persona API, batch 981fe744... + 6f29dc52... generated candidate 148 while comment held the lease. API approval queued publish behind comment, but persisted priority was missing: Edge saw publish=automatic, then a later human comment retry preempted it before submit. Candidate 148 failed without a platform publish. This exposed task 3.6; no FIFO success is claimed until the fix is deployed and re-probed. -->
<!-- final probe after c874d3e deploy, with ol temporarily stopped by explicit operator authority: source codex-real-acceptance-1784458383236 split into publish 271ba0a5... (:command:1) and comment b2df3894... (:command:2); flags were force/joinGroup/manualSingle/injectContact and both started at zero counters. Comment held human comment_prepare; approved candidate 149 entered as human and queued. After comment release, publish acquired; the next human group_join queued without preemption, then continued after publish release. Publish used one real attempt and no wait failure/skipped budget; comment's two counted attempts were actual approval-boundary outcomes, not lease waits. -->
- [x] 6.3 Drive both children through their human-approval/platform boundaries, verify the queued sibling continues with no duplicate platform write, and record accepted/rejected outcomes honestly
<!-- final outcomes: publish task 271ba0a5... completed 1/1; candidate 149 reached platform-confirmed published with postId pfbid06CTcjEJD8EJrubJHDtRapjjtEMkCgJVFLb16HoiMFjc4Uc7zAr3XnX16xhXxuLQVl. Comment b2df3894... continued after publish and ended honestly at max_attempts after two approval_rejected_or_timeout outcomes (0 platform comment writes in this probe). Earlier c033ede5... supplied the real --join + --contact evidence: quota override worked, contact was appended/read back as 9 characters, and one platform comment was confirmed. No child admission or queued state was reported as completion. Tianxing Bai persona writing_language remains vi; test joins/comments/publish are irreversible. OL was restored active/healthy after acceptance; three temporary remote acceptance scripts were deleted. -->
