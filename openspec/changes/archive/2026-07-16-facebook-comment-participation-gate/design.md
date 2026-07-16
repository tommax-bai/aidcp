## Context

Two research passes confirmed the user's report ("发布评论后弹出答题弹框") is Facebook group **Participant Approval / Participation Questions** (public groups) or **Limited Membership** (private groups): an admin-configured, one-time, per-group entry gate that surfaces at the first post/comment attempt. It is group-scoped, inline (URL stays on `/groups/<id>/...`, no `/checkpoint` navigation), and answering still waits for a human admin before the contribution goes live. It is NOT an account-level anti-bot checkpoint.

Current edge behavior (`aidcp-edge/src/facebook/comment-executor.ts`, verified file:line):
- The only membership/questionnaire recognition on the comment path runs at search-candidate time (`:375` → `permission_gated`) via a whole-page regex (`probes/page-structure.ts:235`, `/回答问题|Answer questions/`). By submit time that check is long past.
- The submit focus routine `buildFocusEditorJs` (`:796`) hardcodes `permissionGated:false` and deliberately does **not** call the membership helpers. The comment block at `:789-794` documents why: two real false positives — (1) sidebar/recommended-group "Join" chrome misreading a joined member as not-joined; (2) question-type posts whose reply box aria-label is "输入回答/Answer" (same wording as join questions) but which are legitimate reply boxes.
- Because of (2), `FB_COMMENT_EDITOR_LABEL_RE` (`:53`) whitelists "输入回答/Answer" as a valid comment editor, so a participation answer box would be typed into as if it were a comment box.
- The post-Enter confirmation predicates `buildAckVerifyJs` (`:876`, decision at `:900-903`: `hasServer || reactions>=2`) and `buildScopedVerifyJs` (`:844`) do not check for any pending-approval badge.

Cloud (`aidcp-cloud/src/comment-agent/`): `mapFacebookSubmitOutcome` (`comment-scheduler.ts:333`) maps only `verification_ambiguous / login_required / submit_failed`; `FacebookCommentOutcome` (`facebook-comment-audit-store.ts:16`) has no "pending group approval" state; `reallySubmitted` (`comment-scheduler.ts:944`) counts `verification_ambiguous` as submitted and writes dedup.

## Goals / Non-Goals

**Goals:**
- Never report a pending-admin-approval comment as posted (close the false-green red-line violation).
- Recognize a participation-approval gate at comment time and report it as a distinct honest outcome `pending_group_approval` (not posted), separate from `verification_ambiguous`.
- Do not type the marketing comment into a participation answer box.
- Surface a clear, non-green card that says the comment was not posted and needs human/admin action; do not blindly retry in place.

**Non-Goals:**
- Auto-answering participation questions. Answered ≠ posted (still waits for a human admin; leaks automation traces). Deferred to a separate proposal.
- Handling account-level anti-bot checkpoints / CAPTCHA (separate mechanism; different code path).
- Changing the join-flow questionnaire handling (that path already works for joining).

## Decisions

**D1 — Two separable parts; the honesty veto ships independently of detection.**
Part A (pending-approval veto in the confirm predicates) is a pure tightening: it only ever *refuses* to confirm, so it cannot resurrect the removed membership false positives, and it is valuable even if detection is imperfect. Part B (participation-gate detection → new outcome) carries false-positive and real-machine-wording risk. Splitting them lets Part A land as the stop-the-bleeding fix while Part B is tuned.
- Alternative considered: ship both atomically. Rejected — Part A is strictly safer and higher priority; coupling would delay the red-line fix behind Part B's real-machine tuning.

**D2 — Detect at the post-submit confirmation stage, after both confirm paths fail, before returning `verification_ambiguous`.**
This ordering is the false-positive defense: a legitimate question-post reply that actually posts is confirmed by ack/scoped verify first, so it never reaches the participation probe. Only a submission that produced no confirmed own+text comment is classified as a gate.
- Alternative considered: detect purely at focus time before typing. Rejected as the *sole* mechanism because it reintroduces the `:789-794` false positives. Kept as an *optional secondary* guard (D3) with a strict predicate.

**D3 — The detector keys on a visible `role="dialog"` / participation surface carrying participation-approval phrasing, not a bare body-text match.**
Required signal is participation-approval-specific co-occurrence (e.g. "申请参与 / Request to participate", "参与问题 / Participation questions", "同意小组规则 / Agree to the group rules", "待审核 / Pending review"), scoped to a dialog/interstitial rather than `document.body.innerText`. This is deliberately narrower than the removed `/回答问题|Answer questions/` body scan so it cannot fire on sidebar chrome or an inline question-post reply box.
- A strict pre-type variant (D2 secondary) may return `pending_group_approval` before typing when such a dialog is already present, so the comment body is never dumped into an answer field.

**D4 — `pending_group_approval` is `submitted:false` and is its own cloud outcome; treated like `permission_gated` at scheduling.**
The comment did not go live, so it must not be counted as `reallySubmitted` (no dedup-as-success) and must not be blindly retried in place. Cloud maps it to a distinct `FacebookCommentOutcome` with a non-green card. It is not dedup-marked as posted, mirroring how `permission_gated` gates a target without claiming success.
- Alternative considered: reuse `verification_ambiguous`. Rejected — that outcome is dedup-marked-as-submitted and reads as "probably posted", the opposite of the truth here.

**D5 — Stop whitelisting the participation answer box as a comment editor only where it matters.**
Because a legitimate question-post reply box shares the "输入回答/Answer" label, we cannot simply drop it from `FB_COMMENT_EDITOR_LABEL_RE`. Instead, the participation-gate detector (dialog-scoped) is what distinguishes "this Answer box is inside a participation-approval dialog" from "this Answer box is an inline legit reply box". The editor-label whitelist is left intact for legit reply boxes; the gate detector prevents typing when the box is inside a participation dialog.

## Risks / Trade-offs

- **[Chinese wording not verbatim-confirmed]** → Detector/veto ship with a superset of FB-help verbatim English + high-confidence Chinese phrases, and a real-machine acceptance item captures live DOM to lock exact Simplified-Chinese button/badge text. Stub-level landing does not wait on this.
- **[Re-introducing the removed membership false positives]** → Mitigated by D2 (detect only after confirmation fails) + D3 (dialog-scoped, participation-specific phrasing, never a body-text "Join"/"回答问题" scan). Part A cannot cause them at all (it only refuses to confirm).
- **[Missed gate → falls back to `verification_ambiguous`]** → Acceptable and honest: if the detector does not fire, behavior is today's honest "submitted, unconfirmed", not a false-green (Part A already prevents the false-green independently).
- **[Gate recurs every scheduled run until approved]** → Accepted for now: `pending_group_approval` is not retried in place within a run and is surfaced to a human; deprioritizing such groups is a later scheduling optimization, not a correctness issue.

## Migration Plan

1. Land Part A (edge confirm-predicate veto) — pure tightening, unit-tested; deploy dev.
2. Land Part B (edge detector + `pending_group_approval` reason; cloud outcome + mapping + card) — unit-tested stubs; deploy dev.
3. Real-machine capture on a tom-group account to confirm wording; tune phrase sets; record in `docs/real-machine-acceptance-backlog.md`.
Rollback: both parts are additive/tightening; reverting the edge/cloud commits restores prior behavior. No schema migration (audit outcome is a free-text TEXT column; the enum is a TS type only).

## Open Questions

- Exact Simplified-Chinese button/badge wording for participation-approval and the pending-review badge (pending real-machine capture).
- Whether, after N `pending_group_approval` results, the scheduler should deprioritize a gated group (later scheduling optimization; out of scope here).
