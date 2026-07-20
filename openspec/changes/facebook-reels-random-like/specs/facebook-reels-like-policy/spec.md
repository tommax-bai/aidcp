## ADDED Requirements

### Requirement: Every unique active Facebook Reel receives one ordinary like draw

When Edge reports exactly one active Facebook Reel through `page.cards` with `listKind:'reels'` and a canonical Facebook `/reel/<id>` identity, Cloud SHALL make at most one ordinary like decision for that identity in the active session. For an eligible decision with remaining like budget, Cloud SHALL select a like intent exactly when its injectable random value is strictly less than `0.25`. A value equal to or greater than `0.25` SHALL abstain without sending a like command. Duplicate reports of the same normalized Reel identity MUST NOT redraw.

#### Scenario: Draw below the threshold selects a like intent
- **WHEN** a unique canonical active Reel is reported and the injected random value is `0.249999`
- **THEN** Cloud sends one existing note-scoped like command for that Reel, subject to the existing risk, cooldown, duplicate, and dispatch gates

#### Scenario: Threshold value abstains
- **WHEN** a unique canonical active Reel is reported and the injected random value is exactly `0.25`
- **THEN** Cloud records an ordinary Reel probability abstention and sends no like command for that decision

#### Scenario: Duplicate report does not redraw
- **WHEN** the same normalized Reel identity is reported more than once in one active session
- **THEN** Cloud performs only the first decision and sends at most one probability-selected like intent

#### Scenario: Invalid Reel batch fails closed
- **WHEN** the list is not marked `reels`, contains zero or multiple cards, belongs to another platform, or lacks a canonical Facebook Reel identity
- **THEN** Cloud does not apply the Reel probability policy and sends no probability-selected like command

### Requirement: Reel probability is the sole ordinary interaction appraisal for the handled Reel

After Cloud has handled a Reel through the probability policy, the later ordinary interaction appraiser MUST NOT call its LLM or emit another ordinary like or collect intent for that Reel. It SHALL emit an observable skip that preserves the existing browsing-loop completion. An explicit mandatory interaction rule SHALL be evaluated before this skip and MAY still force its required like.

#### Scenario: Miss is not followed by an LLM-selected like
- **WHEN** the Reel probability draw abstains and the same Reel later reaches ordinary interaction appraisal
- **THEN** the appraiser skips without calling the LLM or emitting an ordinary interaction intent

#### Scenario: Mandatory like overrides ordinary Reel handling
- **WHEN** a handled Reel later carries a confirmed mandatory interaction rule requiring like
- **THEN** the appraiser emits the mandatory like intent without applying the ordinary-handled skip

### Requirement: Only platform-confirmed Reel likes count as success

A probability-selected like SHALL remain an intent until Edge executes the existing note-scoped Reel action and returns a same-Reel positive selected-state witness. Risk accounting, session budget consumption, cooldown timestamps, and user-visible successful activity MUST update only from the existing confirmed `ok:true` receipt. A blocked draw, suppressed dispatch, stale target, ambiguous target, already-liked state, shadow execution, unchanged state, or indeterminate verification MUST NOT be reported or counted as a successful like.

#### Scenario: Probability hit is blocked before dispatch
- **WHEN** the draw selects like but an existing risk, budget, cooldown, or duplicate-action gate rejects it
- **THEN** Cloud sends no like command and neither records nor displays a successful like

#### Scenario: Edge cannot confirm the selected state
- **WHEN** Cloud sends the probability-selected like command but Edge returns a non-success result
- **THEN** Cloud does not consume successful-like budget or record a confirmed like for that Reel

#### Scenario: Edge confirms the same Reel is liked
- **WHEN** Edge returns `ok:true` with the existing same-Reel observation witness
- **THEN** Cloud uses the existing action receipt path to account for and display the confirmed like exactly once
