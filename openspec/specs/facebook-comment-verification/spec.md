# facebook-comment-verification Specification

## Purpose
TBD - created by archiving change facebook-comment-inplace-ack-verify. Update Purpose after archive.
## Requirements
### Requirement: Facebook comment success is confirmed only by server-ack-gated signals

Facebook comment publish-success SHALL be confirmed only from signals that appear after the server accepts the write, scoped to the just-posted comment node identified by the account's own stable numeric identity AND the submitted text fragment. The accepted ack-gated signals are: a **server-assigned comment permalink id** (not a client-side placeholder id) on that node, OR **named reaction/reply affordances** (a like control AND a reply control, identified by their accessible label or text) present on that node. The system MUST NOT confirm success on a bare optimistically-rendered comment, a whole-page text match, or a client-placeholder comment id, because those appear before the server accepts the write.

**A bare count of interactive controls on the node MUST NOT be used as the affordance signal.** Real-machine evidence (2026-07-17): a platform-**rejected** comment row renders as `… 16小时 已拒绝 查看反馈` and carries exactly two interactive controls ("编辑或删除此项" + "查看反馈"), so a `控件数 >= 2` proxy confirms a comment the platform refused — a silent false-green. The affordance signal SHALL therefore identify the like and reply controls specifically, not count controls.

Additionally, the system MUST NOT confirm success when the scoped own+text comment node (or its immediate container) carries a **pending-admin-approval indicator** — a "pending review / awaiting approval / 待审核 / 待批准 / needs admin approval / visible once approved" badge — **even if** that node also carries a server-assigned comment id or reaction/reply affordances. In group participant-approval flows Facebook renders the author's own contribution with a real comment id and interaction controls while it is still queued for a human admin and not live to anyone else; treating that as posted would be a silent false-green. A pending-approval indicator vetoes confirmation.

The system MUST NOT use **visual styling** (opacity, colour, background) to distinguish comment states. Real-machine evidence (2026-07-17): a rejected row and a live row are byte-identical in computed style (`opacity: 1`, `color: rgb(28, 30, 33)` for both); styling carries no signal here.

#### Scenario: Optimistic client-placeholder id does not confirm
- **WHEN** immediately after submit the own+text comment node carries only a client-placeholder comment id and no reaction/reply affordances
- **THEN** the system does not report success and keeps verifying

#### Scenario: Server-assigned id confirms
- **WHEN** the own+text comment node carries a server-assigned comment permalink id
- **THEN** the system reports `ok` (server-confirmed) without requiring a page reload

#### Scenario: Named reaction/reply affordances confirm
- **WHEN** the own+text comment node has gained a named like control and a named reply control
- **THEN** the system reports `ok` (server-confirmed)

#### Scenario: Control count alone never confirms
- **WHEN** the own+text comment node carries two or more interactive controls, but they are not the named like and reply controls (for example an edit-or-delete control plus a view-feedback control)
- **THEN** the system does NOT report success

#### Scenario: Pending-approval badge vetoes confirmation
- **WHEN** the own+text comment node carries a server-assigned comment id or reaction/reply affordances but also carries a pending-admin-approval indicator
- **THEN** the system does NOT report success (the comment is queued for admin approval, not live)

#### Scenario: Styling is never a state signal
- **WHEN** the own+text comment node's opacity or colour differs from, or matches, a live comment row
- **THEN** that styling does not by itself confirm, veto, or classify the comment state

### Requirement: Unknown own numeric identity blocks submission

The edge MUST NOT submit a Facebook comment when the account's own stable numeric identity is unknown, because success cannot be identity-scoped without it. In that case the edge SHALL return an honest `identity_unknown` outcome and MUST NOT press submit.

#### Scenario: Missing own id refuses to submit
- **WHEN** the account's own stable numeric id is unknown at submit time
- **THEN** the edge returns `identity_unknown` and does not submit the comment

### Requirement: Post-submit error overlays are not treated as definitive failure

A post-submit error or permission overlay MUST NOT by itself be treated as a definitive comment failure, because such an overlay has been observed to appear while the comment actually succeeded. The ack-gated verification signals remain authoritative for the success/ambiguous decision.

#### Scenario: Misleading overlay does not force failure
- **WHEN** an error/permission overlay appears after submit but the ack-gated signals confirm the own+text comment
- **THEN** the edge reports success based on the verification signals, not failure based on the overlay

### Requirement: Unconfirmable submission is honestly ambiguous and de-duplicated

When the in-place watch cannot confirm the own+text comment within its bounded window, the edge SHALL report `verification_ambiguous` (submitted, not server-confirmed) rather than claim success or claim a clean hard failure. This outcome MUST continue to mark the target as de-duplicated so the same comment is not re-posted on a later run.

Exception 1: when the edge recognizes a group **participation-approval gate** (see "Participation-approval gate is recognized and reported as pending group approval"), it SHALL report `pending_group_approval` instead of `verification_ambiguous`. Unlike `verification_ambiguous`, `pending_group_approval` means the comment did not go live (it became a participation application), so it MUST NOT be counted as a real submission and MUST NOT be de-duplicated as posted; the same target may be legitimately attempted again after the account is approved.

Exception 2: when the edge recognizes a **platform rejection indicator** on the own+text comment row (see "Platform-rejected comments are an honest terminal outcome"), it SHALL report the rejected outcome instead of `verification_ambiguous`. The comment is known not to be live, so it MUST NOT be de-duplicated as posted.

#### Scenario: Neither confirmed nor classified is honestly ambiguous
- **WHEN** the in-place window expires without ack-gated signals, without a rejection indicator, and without a participation-approval gate
- **THEN** the edge reports `verification_ambiguous` and the target is de-duplicated so no duplicate is posted later

#### Scenario: Rejection is not collapsed into ambiguous
- **WHEN** the own+text comment row carries a platform rejection indicator
- **THEN** the edge reports the rejected outcome, not `verification_ambiguous`, and the target is not de-duplicated as posted

### Requirement: Participation-approval gate is recognized and reported as pending group approval

The edge SHALL recognize a Facebook group **participant-approval / participation-question** gate encountered at comment time and report it as a distinct honest outcome `pending_group_approval`. The gate is admin-configured and group-scoped: on the account's first contribution to such a group, Facebook interrupts the comment with a "request to participate + answer questions + agree to rules" flow instead of posting, and the contribution then waits for a human admin.

Recognition MUST key on a **visible participation-approval dialog/surface** whose text carries participation-approval phrasing (e.g. "request to participate / 申请参与", "participation questions / 参与问题", "agree to the group rules / 同意小组规则", "pending review / 待审核"). Recognition MUST NOT be a bare whole-page body-text scan for "回答问题 / Answer questions", because that wording also appears on unrelated sidebar/recommended-group chrome and on legitimate question-type post reply boxes; a bare scan would revive known false positives.

The edge MUST NOT type the comment body into a participation answer box: when a participation-approval dialog is present before typing, the edge SHALL return `pending_group_approval` without entering the comment text.

The cloud SHALL map `pending_group_approval` to its own comment outcome, distinct from `verification_ambiguous`, `submit_failed`, and `login_required`. The result card MUST state that the comment was not posted and that the group requires admin approval to participate, MUST NOT be colored as success, MUST NOT count as a real submission, and MUST NOT trigger a blind in-place retry.

Auto-answering participation questions is explicitly out of scope: a submitted answer still awaits a human admin (the comment does not post immediately), so an answered gate MUST NOT be treated as a posted comment.

#### Scenario: Participation dialog before typing is reported, not answered
- **WHEN** a participation-approval dialog is present when the edge is about to type the comment
- **THEN** the edge returns `pending_group_approval` and does NOT type the comment body into the answer box

#### Scenario: Legitimate question-post reply is unaffected
- **WHEN** the account replies on a question-type post whose reply box is labeled "输入回答/Answer" but which is not inside a participation-approval dialog, and the reply posts and is confirmed
- **THEN** the edge reports success normally and the participation-gate detector does not fire

#### Scenario: Cloud surfaces a non-green, honest card
- **WHEN** the edge returns `pending_group_approval`
- **THEN** the cloud records a distinct outcome and renders a non-success card stating the comment was not posted and the group needs admin approval to participate, without de-duplicating the target as posted

#### Scenario: Answered gate is never treated as posted
- **WHEN** a participation gate is encountered
- **THEN** the system MUST NOT report the comment as posted on the basis of any participation answer being submitted (answered ≠ posted)

### Requirement: In-place watch is the sole confirmation path; the edge MUST NOT reload to verify

After submitting, the edge SHALL confirm **only by watching the current page in place**, polling within a bounded window for the ack-gated signals, and MUST NOT reload the page as part of verification.

The in-place window SHALL absorb the budget previously spent on the retired reload leg, so the **total post-submit budget is unchanged**. The total post-submit budget MUST remain within the cloud comment step timeout, which covers humanized typing plus confirmation in a single allowance: exceeding it makes the cloud record a bare `timeout`, which does not mark de-duplication and therefore re-posts the same target next round as a platform-visible duplicate comment.

#### Scenario: Confirmation never reloads
- **WHEN** the edge is verifying a submitted comment, whether or not the ack-gated signals have appeared
- **THEN** the edge does not reload the page at any point during verification

#### Scenario: Slow render is absorbed by the in-place poll
- **WHEN** the ack-gated signals have not yet appeared early in the window
- **THEN** the edge keeps polling in place until they appear or the window expires, rather than reloading to re-check

#### Scenario: In-place window absorbs the retired reload budget
- **WHEN** the post-submit confirmation window is sized
- **THEN** it takes over the budget formerly spent on the reload leg, leaving the total post-submit budget unchanged and within the cloud step timeout

#### Scenario: Evidence survives for the non-live recognizers
- **WHEN** a submitted comment is held by a participation-approval gate or rendered with a pending-approval badge
- **THEN** the badge and dialog are still present for the recognizers to read, because no reload has cleared them

### Requirement: Platform-rejected comments are an honest terminal outcome

When the scoped own+text comment row carries a **platform rejection indicator** — a "已拒绝 / 查看反馈 / rejected / declined / see feedback" marker rendered in the row's metadata slot where a live comment shows its timestamp and like/reply controls — the edge SHALL report a **dedicated rejected outcome**, distinct from every other outcome.

Real-machine evidence (2026-07-17): a rejected row reads `Tianxing Bai … 16小时 已拒绝 查看反馈`, carries no server-format comment id, and carries the edit-or-delete plus view-feedback controls instead of like/reply. The rejection appears immediately after submission, inside the confirmation window — it is not a delayed state.

This outcome means **the comment is known not to be live**. Therefore it:
- MUST NOT be reported as success;
- MUST NOT be de-duplicated as posted (the platform refused the write; the target remains eligible for human handling);
- MUST NOT be collapsed into `verification_ambiguous`, whose semantics are "possibly posted" **and** which marks de-duplication — that would both misreport a certain failure as a maybe-success and permanently burn the target;
- MUST NOT be collapsed into `pending_group_approval`, whose semantics are "queued, may go live once an admin approves" — a rejection is terminal, and waiting or retrying on approval is meaningless.

The rejection indicator is a **text** signal used only to veto and classify; it MUST NOT be the sole basis for confirming success, and success SHALL continue to rest on the language-independent server-assigned id plus the named affordances. A missed rejection indicator SHALL fall back to the existing honest non-success paths (never to success).

The **in-row** rejection indicator is a distinct DOM artifact from the **post-submit error/permission overlay** covered by "Post-submit error overlays are not treated as definitive failure". The overlay has been observed to lie (appearing while the comment succeeded) and remains non-authoritative; the in-row indicator is authoritative for this outcome. The two MUST NOT be conflated.

#### Scenario: Rejected row reports the dedicated outcome
- **WHEN** the own+text comment row carries a platform rejection indicator in its metadata slot
- **THEN** the edge reports the dedicated rejected outcome, does not report success, and does not mark the target de-duplicated

#### Scenario: Rejected row is never confirmed by its controls
- **WHEN** a rejected row carries interactive controls (edit-or-delete, view-feedback) but no named like/reply controls and no server-assigned id
- **THEN** the edge does not report success

#### Scenario: Rejection is distinct from pending approval
- **WHEN** the row carries a rejection indicator rather than a pending-admin-approval badge
- **THEN** the edge reports the rejected outcome rather than `pending_group_approval`, and the target is not queued for a post-approval retry

#### Scenario: A missed rejection indicator degrades safely
- **WHEN** the platform renders a rejection in wording the recognizer does not match
- **THEN** the edge falls back to an honest non-success outcome and never reports success on that basis

#### Scenario: In-row rejection is not the misleading overlay
- **WHEN** a post-submit error overlay appears but the own+text row carries no rejection indicator and the ack-gated signals confirm
- **THEN** the edge reports success, because the overlay is not authoritative and the in-row indicator is absent

### Requirement: In-flight comments are recognized and never treated as terminal

When the scoped own+text comment row carries an **in-flight indicator** — a "发布中 / Posting / Sending" marker occupying the metadata slot where a live comment later shows its timestamp and like/reply controls — the edge SHALL treat the comment as **still in flight**: it MUST continue verifying within its window and MUST NOT report any terminal outcome while the indicator is present.

Real-machine evidence (2026-07-17, two consistent runs): the row renders optimistically ~31ms after submit as `… 发布中...` with zero interactive controls and unchanged styling; the server acknowledgement arrives at ~2.8s; within ~99ms of that acknowledgement the indicator disappears and the row shows its timestamp plus like and reply controls. The in-flight state is plain text — it carries no `aria-busy` attribute and no opacity change, so attribute- or style-based detection cannot see it.

This signal exists to give the system a diagnostic distinction it currently lacks: **"never submitted" versus "submitted but the outcome was never observed"**. When the window expires while the comment is still in flight, the edge SHALL report an honest non-success outcome and SHALL record that the comment was observed in flight, so the operator can tell that the write was actually dispatched.

#### Scenario: In-flight indicator keeps verification open
- **WHEN** the own+text comment row shows the in-flight indicator and no ack-gated signal has appeared
- **THEN** the edge keeps verifying within its window and reports no terminal outcome

#### Scenario: In-flight resolves to success on acknowledgement
- **WHEN** the in-flight indicator is replaced by a timestamp with named like and reply controls
- **THEN** the edge reports `ok` (server-confirmed)

#### Scenario: Expiring while in flight is honest and diagnosable
- **WHEN** the confirmation window expires while the row still shows the in-flight indicator
- **THEN** the edge reports an honest non-success outcome and records that the comment was observed in flight, distinguishing it from an attempt that never submitted

