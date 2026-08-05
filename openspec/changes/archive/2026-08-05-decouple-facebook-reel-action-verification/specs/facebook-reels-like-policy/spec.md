## MODIFIED Requirements

### Requirement: Only platform-confirmed Reel likes count as success

A probability-selected like SHALL remain an intent until Edge executes the existing note-scoped Reel action and returns a positive selected-state witness from a freshly resolved Like control on the same canonical Reel. Loss or replacement of the exact pre-click DOM node MUST NOT by itself be treated as loss of the Reel target when the same canonical Reel and its current Like state remain uniquely resolvable. Risk accounting, session budget consumption, cooldown timestamps, and user-visible successful activity MUST update only from the existing confirmed `ok:true` receipt. A blocked draw, suppressed dispatch, stale Reel, ambiguous Reel, already-liked state, shadow execution, unchanged state, or indeterminate verification MUST NOT be reported or counted as a successful like.

#### Scenario: Probability hit is blocked before dispatch
- **WHEN** the draw selects like but an existing risk, budget, cooldown, or duplicate-action gate rejects it
- **THEN** Cloud sends no like command and neither records nor displays a successful like

#### Scenario: Edge cannot confirm the selected state
- **WHEN** Cloud sends the probability-selected like command but Edge cannot freshly resolve a positive selected state on the same canonical Reel before the existing verification deadline
- **THEN** Cloud does not consume successful-like budget or record a confirmed like for that Reel

#### Scenario: Same Reel replaces the clicked Like node
- **WHEN** the one-time Like commit causes Facebook to replace the clicked DOM node while the same canonical Reel remains active
- **THEN** Edge freshly resolves the replacement Like control and confirms success only when that control exposes the positive selected state

#### Scenario: Edge confirms the same Reel is liked
- **WHEN** Edge returns `ok:true` with the existing same-Reel observation witness
- **THEN** Cloud uses the existing action receipt path to account for and display the confirmed like exactly once
