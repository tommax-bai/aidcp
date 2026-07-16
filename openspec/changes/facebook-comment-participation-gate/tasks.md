# Tasks — facebook-comment-participation-gate

> Hot paths (serialize, no parallel writer): edge `src/facebook/comment-executor.ts`, cloud `src/comment-agent/comment-scheduler.ts` outcome mapping.
> Part A (止血) is independently landable and must ship first.

## 1. aidcp-edge — Part A: pending-approval veto (stop the false-green)

- [ ] 1.1 Add a pure JS-string helper (or inline predicate) that detects a pending-admin-approval indicator on/near a comment node — phrase set: `待审核 / 待批准 / pending review / awaiting approval / needs admin approval / 需要管理员批准 / 通过后可见 / visible once approved` (superset of FB-help verbatim EN + high-confidence ZH; real-machine tuning tracked in §5).
- [ ] 1.2 In `buildAckVerifyJs` (`comment-executor.ts:876`, decision at `:900-903`): before returning `ackConfirmed:true`, veto when the matched own+text node (or immediate container) carries the pending-approval indicator.
- [ ] 1.3 In `buildScopedVerifyJs` (`comment-executor.ts:844`): apply the same pending-approval veto before returning `confirmed:true`.
- [ ] 1.4 Unit tests: pending-approval indicator vetoes confirmation even when a server id / ≥2 reaction buttons are present; a normal live comment (no pending badge) still confirms. Cover ZH + EN wording.

## 2. aidcp-edge — Part B: participation-gate detection + honest reason

- [ ] 2.1 Add `pending_group_approval` to `FacebookCommentStepReason` (`comment-executor.ts:61`) with a comment.
- [ ] 2.2 Add a precise `buildParticipationGateJs` probe: fire only on a **visible `role="dialog"` / participation surface** whose text carries participation-approval phrasing (`申请参与 / request to participate`, `参与问题 / participation questions`, `同意小组规则 / agree to the group rules`, `待审核 / pending review`). MUST NOT be a bare `document.body.innerText` scan for `回答问题 / Answer questions` (avoids the `:789-794` false positives). Keep the phrase source shared with a TS-testable assertion (mirror `FB_COMMENT_EDITOR_LABEL_RE` pattern).
- [ ] 2.3 Call the probe in the post-Enter confirmation segment (`comment-executor.ts:559-578`): after `inPlaceAckConfirm` + `reloadScopedConfirm` both fail, before returning `verification_ambiguous`, run the probe; on hit return `{ ok:false, reason:'pending_group_approval', submitted:false }`.
- [ ] 2.4 Optional pre-type guard: in the submit path before `dispatchKeystrokes`, if the participation-gate probe already sees a participation dialog, return `pending_group_approval` without typing the comment body (do not dump the marketing comment into the answer box).
- [ ] 2.5 Unit tests: probe fires on a participation-approval dialog; probe does NOT fire on (a) a bare body containing `回答问题`, (b) sidebar `Join` chrome, (c) an inline question-post reply box that is not inside a participation dialog.

## 3. aidcp-cloud — Part B: distinct honest outcome + card

- [ ] 3.1 Add `pending_group_approval` to `FacebookCommentOutcome` (`facebook-comment-audit-store.ts:16`) with a comment.
- [ ] 3.2 `mapFacebookSubmitOutcome` (`comment-scheduler.ts:333`): add `case 'pending_group_approval' → 'pending_group_approval'` (do NOT collapse into `verification_ambiguous` / `submit_failed`).
- [ ] 3.3 `commentOutcomeReason` (`comment-scheduler.ts:139`): add human text — "该群需管理员批准参与后才能评论（评论未上墙，待人工处理）".
- [ ] 3.4 Ensure the scheduler treats `pending_group_approval` as gated: NOT `reallySubmitted` (`comment-scheduler.ts:944` — no dedup-as-success), non-green card, no blind in-place retry (mirror `permission_gated` handling).
- [ ] 3.5 Unit tests: `pending_group_approval` maps to its own outcome, renders a non-success card with the human text, and is not counted as submitted/dedup.

## 4. Verification (both repos)

- [ ] 4.1 edge: `npm run test:acceptance` (AC-* red lines, esp. AC-PUB-* unaffected) → `npm test` → `npm run typecheck`.
- [ ] 4.2 cloud: `npm run test:acceptance` → `npm test` → `npm run typecheck`.
- [ ] 4.3 Land both to their default branches (rebase, ff), deploy `dev` per safety sequence, healthcheck.

## 5. Real-machine acceptance (decoupled — does NOT block §1–§4 landing/deploy)

- [ ] 5.1 Register a real-machine item in `docs/real-machine-acceptance-backlog.md`: on a tom-group test account, enter a public group with Participant Approval on, comment as a non-participant, capture live DOM (screenshot + innerText) of the participation dialog and the pending-review badge.
- [ ] 5.2 Lift the detector/veto phrase sets from "semantically high-confidence" to "verbatim-confirmed" using the captured Simplified-Chinese wording; confirm URL stays on `/groups/...` (not `/checkpoint`) to validate the group-scoped classification.
