## ADDED Requirements

### Requirement: Every unique presented ordinary Feed video records one view and one ordinary like decision

When Edge reports a Facebook ordinary-Feed batch containing exactly one strict primary video card with a canonical Facebook video identity, Cloud SHALL record one existing view interaction for that normalized identity before content selection and SHALL make at most one ordinary like decision for it in the active session. A later detail read or duplicate card report for the same identity MUST NOT record a second view or redraw. For an eligible decision with a non-empty caption and no obvious high-risk caption signal, Cloud SHALL select a like intent exactly when its injectable random value is strictly less than `0.25`; a value equal to or greater than `0.25` SHALL abstain.

#### Scenario: Safe presented video draws below threshold
- **WHEN** one strict ordinary-Feed video with a non-empty safe caption is presented and the injected random value is `0.249999`
- **THEN** Cloud records one view and sends one existing note-scoped like intent subject to the existing interaction gates

#### Scenario: Threshold value abstains but still records the view
- **WHEN** one eligible ordinary-Feed video is presented and the injected random value is exactly `0.25`
- **THEN** Cloud records one view, records a probability abstention, and sends no probability-selected like command

#### Scenario: Duplicate presentation is idempotent
- **WHEN** the same normalized video identity is reported again or later reaches `note.detail` in the same session
- **THEN** Cloud records no second presentation view and performs no second probability draw

#### Scenario: Missing or obvious-risk caption abstains safely
- **WHEN** a strict video has no non-empty caption or its caption matches the bounded obvious-risk text filter
- **THEN** Cloud records the real view but sends no probability-selected like command and does not permit a duplicate report to redraw

#### Scenario: Ambiguous video batch does not use the policy
- **WHEN** a Feed batch contains zero or multiple `isVideo` cards, lacks a canonical Facebook video identity, belongs to another platform, or is not `listKind:'feed'`
- **THEN** Cloud does not apply the ordinary-Feed video probability policy

### Requirement: Probability handling is the sole ordinary appraisal while mandatory interactions remain authoritative

After Cloud handles a Feed video through the presentation policy, the later ordinary interaction appraiser MUST NOT call its LLM or emit another ordinary like or collect intent for the same normalized identity. The existing mandatory-interaction branch SHALL execute before this skip and MAY still force its configured actions. A probability miss, safety abstention, blocked hit, or failed action MUST allow the existing browsing loop to continue.

#### Scenario: Probability miss is not followed by an LLM like
- **WHEN** the Feed-video probability draw abstains and the same video later reaches ordinary interaction appraisal
- **THEN** the appraiser skips without calling the LLM or emitting another ordinary interaction intent

#### Scenario: Mandatory rule survives the ordinary handled skip
- **WHEN** a handled Feed video later carries a confirmed mandatory interaction requiring like or comment
- **THEN** the mandatory branch emits the required intent before the ordinary handled skip is considered

#### Scenario: Blocked hit continues browsing
- **WHEN** a probability hit is blocked by budget, risk, cooldown, duplicate, dispatch, or Edge verification
- **THEN** Cloud does not claim a successful like and the session continues through the existing Feed browse loop

### Requirement: Only a same-video confirmed receipt counts as a successful like

A probability-selected Feed-video like SHALL remain an intent until Edge resolves the requested canonical identity to exactly one strict card, acts inside that card, and returns an existing positive selected-state witness for the same video. Risk accounting, successful-like budget, cooldown timestamps, and user-visible like activity MUST update only from the existing confirmed `ok:true` receipt.

#### Scenario: Exact video selected state is confirmed
- **WHEN** Edge clicks the one neutral like control inside the requested video card and rereads a same-card unlike/selected witness
- **THEN** Edge returns the existing confirmed success receipt and Cloud accounts for the like exactly once

#### Scenario: Target or verification is uncertain
- **WHEN** identity resolution is missing/ambiguous, the card moved, the selected state is unchanged, or verification is indeterminate
- **THEN** Edge returns the corresponding non-success outcome and Cloud records no successful like
