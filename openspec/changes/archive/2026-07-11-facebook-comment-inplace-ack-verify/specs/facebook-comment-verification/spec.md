## ADDED Requirements

### Requirement: Facebook comment success is confirmed only by server-ack-gated signals

Facebook comment publish-success SHALL be confirmed only from signals that appear after the server accepts the write, scoped to the just-posted comment node identified by the account's own stable numeric identity AND the submitted text fragment. The accepted ack-gated signals are: a **server-assigned comment permalink id** (not a client-side placeholder id) on that node, OR **reaction/reply affordances present** on that node. The system MUST NOT confirm success on a bare optimistically-rendered comment, a whole-page text match, or a client-placeholder comment id, because those appear before the server accepts the write.

#### Scenario: Optimistic client-placeholder id does not confirm
- **WHEN** immediately after submit the own+text comment node carries only a client-placeholder comment id and no reaction/reply affordances
- **THEN** the system does not report success and keeps verifying

#### Scenario: Server-assigned id confirms
- **WHEN** the own+text comment node carries a server-assigned comment permalink id
- **THEN** the system reports `ok` (server-confirmed) without requiring a page reload

#### Scenario: Reaction/reply affordances confirm
- **WHEN** the own+text comment node has gained reaction/reply affordances
- **THEN** the system reports `ok` (server-confirmed)

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

#### Scenario: Neither path confirms
- **WHEN** both the in-place watch and the bounded reload verify fail to find the own+text comment
- **THEN** the edge returns `verification_ambiguous` (submitted, not confirmed) and the target is de-duplicated to prevent a duplicate re-post
