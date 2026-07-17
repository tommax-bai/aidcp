## MODIFIED Requirements

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

## REMOVED Requirements

### Requirement: In-place watch is the fast primary and bounded reload verify is the authoritative fallback

**Reason**: Real-machine evidence (2026-07-17) retired the reload fallback on three independent grounds. (a) It produced a **false negative** on-probe — the reload verify reported the just-posted comment absent while both probe comments were in fact live (CDP re-check plus direct human observation); this is the origin of the operator-facing 「提交后无法确认评论已上墙」 card that motivated the investigation. (b) Its scoped verify confirmed on own-identity + text alone, without any ack-gated signal, so it would confirm a **platform-rejected** comment as success. (c) Reloading **destroys evidence** — it clears the pending-approval badge and the participation-approval dialog, blinding the very recognizers that classify a non-live comment. The requirement's stated purpose (defeating slow-render false negatives) is fully served by the bounded in-place poll, which now absorbs the reload leg's budget.

**Migration**: Replaced by "In-place watch is the sole confirmation path; the edge MUST NOT reload to verify". The in-place window takes over the reload leg's budget so the **total post-submit budget is unchanged** and stays within the cloud comment step timeout; no timeout constant changes. Behaviour that previously reached success only via the reload leg now reaches it via the longer in-place poll; behaviour that previously false-greened a rejected comment via the reload leg now reports the dedicated rejected outcome.

## ADDED Requirements

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
