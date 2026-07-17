# facebook-comment-verification Specification

## Purpose
TBD - created by archiving change facebook-comment-inplace-ack-verify. Update Purpose after archive.
## Requirements
### Requirement: Facebook comment success is confirmed only by server-ack-gated signals

Facebook comment publish-success SHALL be confirmed only from signals that appear after the server accepts the write, scoped to the just-posted comment node identified by the account's own stable numeric identity AND the submitted text fragment. The accepted ack-gated signals are: a **server-assigned comment permalink id** (not a client-side placeholder id) on that node, OR **reaction/reply affordances present** on that node. The system MUST NOT confirm success on a bare optimistically-rendered comment, a whole-page text match, or a client-placeholder comment id, because those appear before the server accepts the write.

Additionally, the system MUST NOT confirm success when the scoped own+text comment node (or its immediate container) carries a **pending-admin-approval indicator** — a "pending review / awaiting approval / 待审核 / 待批准 / needs admin approval / visible once approved" badge — **even if** that node also carries a server-assigned comment id or reaction/reply affordances. In group participant-approval flows Facebook renders the author's own contribution with a real comment id and interaction controls while it is still queued for a human admin and not live to anyone else; treating that as posted would be a silent false-green. A pending-approval indicator vetoes confirmation.

#### Scenario: Optimistic client-placeholder id does not confirm
- **WHEN** immediately after submit the own+text comment node carries only a client-placeholder comment id and no reaction/reply affordances
- **THEN** the system does not report success and keeps verifying

#### Scenario: Server-assigned id confirms
- **WHEN** the own+text comment node carries a server-assigned comment permalink id
- **THEN** the system reports `ok` (server-confirmed) without requiring a page reload

#### Scenario: Reaction/reply affordances confirm
- **WHEN** the own+text comment node has gained reaction/reply affordances
- **THEN** the system reports `ok` (server-confirmed)

#### Scenario: Pending-approval badge vetoes confirmation
- **WHEN** the own+text comment node carries a server-assigned comment id or reaction/reply affordances but also carries a pending-admin-approval indicator
- **THEN** the system does NOT report success (the comment is queued for admin approval, not live)

### Requirement: In-place watch is the fast primary and bounded reload verify is the authoritative fallback

After submitting, the edge SHALL first watch the current page in place, without reloading, polling within a bounded window for the ack-gated signals. If the in-place watch confirms, it SHALL report success without reloading. If the in-place watch does not confirm within its window, the edge SHALL reload once and then poll the scoped verify within a bounded window (not a single check after a fixed wait), reporting success on the first match. A single one-shot check after a fixed reload wait is insufficient because a comment that is already live server-side can fail to re-render within that one window (a false negative).

#### Scenario: Fast path confirms without reload
- **WHEN** the ack-gated signals appear in place within the in-place window
- **THEN** the edge reports success and does not reload the page

#### Scenario: Fallback reload uses bounded polling
- **WHEN** the in-place watch does not confirm within its window
- **THEN** the edge reloads and re-checks the scoped verify repeatedly within a bounded window, confirming on the first match rather than after a single fixed wait

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

When neither the in-place watch nor the bounded reload verify can confirm the own+text comment, the edge SHALL report `verification_ambiguous` (submitted, not server-confirmed) rather than claim success or claim a clean hard failure. This outcome MUST continue to mark the target as de-duplicated so the same comment is not re-posted on a later run.

Exception: when — after both confirm paths fail — the edge recognizes a group **participation-approval gate** (see "Participation-approval gate is recognized and reported as pending group approval"), it SHALL report `pending_group_approval` instead of `verification_ambiguous`. Unlike `verification_ambiguous`, `pending_group_approval` means the comment did not go live (it became a participation application), so it MUST NOT be counted as a real submission and MUST NOT be de-duplicated as posted; the same target may be legitimately attempted again after the account is approved.

#### Scenario: Neither path confirms
- **WHEN** both the in-place watch and the bounded reload verify fail to find the own+text comment AND no participation-approval gate is recognized
- **THEN** the edge returns `verification_ambiguous` (submitted, not confirmed) and the target is de-duplicated to prevent a duplicate re-post

#### Scenario: Participation gate carves out of ambiguous
- **WHEN** both confirm paths fail AND a participation-approval gate is recognized
- **THEN** the edge returns `pending_group_approval` (not posted) rather than `verification_ambiguous`, and the target is NOT de-duplicated as posted

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

