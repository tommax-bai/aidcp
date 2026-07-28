## MODIFIED Requirements

### Requirement: Facebook comment success is confirmed only by server-ack-gated signals

Facebook comment publish-success SHALL be confirmed only from signals that appear after the server accepts the write, scoped to the just-posted comment node identified by the account's own stable numeric identity AND the submitted text fragment. The accepted ack-gated signals are: a **server-assigned comment permalink id** (not a client-side placeholder id) on that node, OR **named reaction/reply affordances** (a like control AND a reply control, identified by their accessible label or text) present on that node. The system MUST NOT confirm success on a bare optimistically-rendered comment, a whole-page text match, or a client-placeholder comment id, because those appear before the server accepts the write.

**"Server-assigned" is a provenance judgement, not a single encoding.** Facebook issues the confirmed comment id in more than one shape, and the shape varies by rendering surface. Real-machine evidence (2026-07-28, Vietnamese group feed, in-place first-post comment): at Enter+73 ms the node carried the client placeholder `client:46fd0dfd-…`; at **Enter+4.29 s** the same node carried the **purely numeric** id `1531497545657803`, which survived a page reload. Other surfaces carry the base64 `comment:` form (`Y29tbWVudD…`). The system SHALL therefore accept any comment id that the platform did not mark as a client placeholder, and MUST NOT require one specific encoding — requiring only the base64 form makes an in-place confirmed comment permanently unconfirmable on surfaces that issue numeric ids, which is a false-failure with the same operational cost as a false-green (the target is de-duplicated and burned while reported as not posted).

Client-placeholder rejection remains mandatory: an id carrying the platform's client-placeholder marker (`client` prefix) MUST NOT confirm.

**A bare count of interactive controls on the node MUST NOT be used as the affordance signal.** Real-machine evidence (2026-07-17): a platform-**rejected** comment row renders as `… 16小时 已拒绝 查看反馈` and carries exactly two interactive controls ("编辑或删除此项" + "查看反馈"), so a `控件数 >= 2` proxy confirms a comment the platform refused — a silent false-green. The affordance signal SHALL therefore identify the like and reply controls specifically, not count controls.

Additionally, the system MUST NOT confirm success when the scoped own+text comment node (or its immediate container) carries a **pending-admin-approval indicator** — a "pending review / awaiting approval / 待审核 / 待批准 / needs admin approval / visible once approved" badge — **even if** that node also carries a server-assigned comment id or reaction/reply affordances. In group participant-approval flows Facebook renders the author's own contribution with a real comment id and interaction controls while it is still queued for a human admin and not live to anyone else; treating that as posted would be a silent false-green. A pending-approval indicator vetoes confirmation.

The system MUST NOT use **visual styling** (opacity, colour, background) to distinguish comment states. Real-machine evidence (2026-07-17): a rejected row and a live row are byte-identical in computed style (`opacity: 1`, `color: rgb(28, 30, 33)` for both); styling carries no signal here.

#### Scenario: Optimistic client-placeholder id does not confirm
- **WHEN** immediately after submit the own+text comment node carries only a client-placeholder comment id and no reaction/reply affordances
- **THEN** the system does not report success and keeps verifying

#### Scenario: Server-assigned id confirms
- **WHEN** the own+text comment node carries a server-assigned comment permalink id
- **THEN** the system reports `ok` (server-confirmed) without requiring a page reload

#### Scenario: Numeric server-assigned id confirms
- **WHEN** the own+text comment node carries a comment permalink id that is a plain numeric platform id and carries no client-placeholder marker
- **THEN** the system reports `ok` (server-confirmed), the same as for the base64 `comment:` form

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
