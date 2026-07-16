# Tasks — facebook-comment-participation-gate

> Hot paths (serialize, no parallel writer): edge `src/facebook/comment-executor.ts`, cloud `src/comment-agent/comment-scheduler.ts` outcome mapping.
> Part A (止血) is independently landable and must ship first.
> Landed: edge master `a6fb282`, cloud master `21e44e5`. Cloud deployed dev 2026-07-16 (healthcheck green: active + 8787/8090 + Feishu 长连接 + PG select 1). Edge lands to master; the local desktop client picks it up on next master restart — packaging not done (per default, user-triggered).

## 1. aidcp-edge — Part A: pending-approval veto (stop the false-green)

- [x] 1.1 Add a pure JS-string helper (or inline predicate) that detects a pending-admin-approval indicator on/near a comment node — phrase set: `待审核 / 待批准 / pending review / awaiting approval / needs admin approval / 需要管理员批准 / 通过后可见 / visible once approved` (superset of FB-help verbatim EN + high-confidence ZH; real-machine tuning tracked in §5). <!-- aidcp-edge a6fb282 FB_PENDING_APPROVAL_RE + fbNodePendingApproval + isFacebookPendingApprovalText -->
- [x] 1.2 In `buildAckVerifyJs` (`comment-executor.ts`): before returning `ackConfirmed:true`, veto when the matched own+text node carries the pending-approval indicator; surface `pendingApproval`. <!-- aidcp-edge a6fb282 -->
- [x] 1.3 In `buildScopedVerifyJs` (`comment-executor.ts`): apply the same pending-approval veto before returning `confirmed:true`. <!-- aidcp-edge a6fb282 -->
- [x] 1.4 Unit tests: pending-approval indicator vetoes confirmation even with server id / ≥2 reaction buttons; a normal live comment still confirms. ZH + EN wording. <!-- aidcp-edge a6fb282 3 ack + 2 scoped + assert tests, 1508 全绿 -->

## 2. aidcp-edge — Part B: participation-gate detection + honest reason

- [x] 2.1 Add `pending_group_approval` to `FacebookCommentStepReason`. <!-- aidcp-edge a6fb282 -->
- [x] 2.2 Add precise `buildParticipationGateJs`: fire only on a **visible `role="dialog"`** whose text carries participation-approval phrasing (`FB_PARTICIPATION_GATE_RE`); NOT a body-text scan for `回答问题/Answer questions` (avoids the documented sidebar-Join / question-post-reply false positives). Shared `.source` with TS assert `isFacebookParticipationGateText`. <!-- aidcp-edge a6fb282 -->
- [x] 2.3 Call the probe in the post-Enter confirmation segment: after both confirm paths fail (incl. `ack.pendingApproval`), before `verification_ambiguous`, return `{ ok:false, reason:'pending_group_approval', submitted:false }` (no reload/retry). <!-- aidcp-edge a6fb282 -->
- [x] 2.4 Pre-type guard: after focus, before typing, if the participation-gate probe sees a dialog, return `pending_group_approval` without typing the body into the answer box. <!-- aidcp-edge a6fb282 -->
- [x] 2.5 Unit tests: probe fires on a participation dialog (ZH + EN); does NOT fire on a bare body `回答问题`, sidebar Join chrome, or an inline question-post reply box. <!-- aidcp-edge a6fb282 3 gate tests + assert -->

## 3. aidcp-cloud — Part B: distinct honest outcome + card

- [x] 3.1 Add `pending_group_approval` to `FacebookCommentOutcome`. <!-- aidcp-cloud 21e44e5 -->
- [x] 3.2 `mapFacebookSubmitOutcome`: `case 'pending_group_approval' → 'pending_group_approval'` (never collapse into `verification_ambiguous`/`submit_failed`). <!-- aidcp-cloud 21e44e5 -->
- [x] 3.3 `commentOutcomeReason`: human text 「该群需管理员批准参与后才能评论（评论未上墙，待人工处理）」. <!-- aidcp-cloud 21e44e5 -->
- [x] 3.4 Scheduler treats it as gated: NOT `reallySubmitted` (already excluded — no dedup-as-success), warning card (never green), no blind retry; risk-record & delegated-success both gate on `'commented'` only (verified, no false-green). <!-- aidcp-cloud 21e44e5 audit() propagates to terminal last.outcome -->
- [x] 3.5 Unit tests: `pending_group_approval` → human text; `joinCommentReceipt` → warning (never green). <!-- aidcp-cloud 21e44e5 2 tests, 2273 全绿 -->

## 4. Verification (both repos)

- [x] 4.1 edge: `test:acceptance` (AC-PUB unaffected) + `npm test` (1508) + `typecheck` all green. <!-- aidcp-edge a6fb282 -->
- [x] 4.2 cloud: `test:acceptance` (54) + `npm test` (2273) + `typecheck` all green. <!-- aidcp-cloud 21e44e5 -->
- [x] 4.3 Land both to master (ff), deploy `dev` (cloud) per safety sequence, healthcheck. <!-- edge a6fb282 + cloud 21e44e5 landed; cloud deployed dev 2026-07-16 (backup cloud.bak.20260716-161340) healthcheck green -->

## 5. Real-machine acceptance (decoupled — registered in backlog 簇 88; does NOT block landing/deploy)

- [ ] 5.1 On a tom-group test account, enter a public group with Participant Approval on, comment as a non-participant, capture live DOM (screenshot + innerText) of the participation dialog and the pending-review badge. <!-- registered docs/real-machine-acceptance-backlog.md 簇 88 -->
- [ ] 5.2 Lift the detector/veto phrase sets from "semantically high-confidence" to "verbatim-confirmed"; confirm URL stays on `/groups/...` (not `/checkpoint`). <!-- registered 簇 88 -->
