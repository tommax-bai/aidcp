## ADDED Requirements

### Requirement: Facebook submit postconditions SHALL distinguish obstruction from disappearance

Before Native dispatches a Facebook login or 2FA submit action, the exact target MUST remain visible, unique, and topmost. After that action has been dispatched, the bounded postcondition verifier MUST NOT treat the still-present target becoming temporarily non-topmost as proof that the observed signal disappeared. It SHALL observe at a 200 ms cadence for at most 35 polls without replaying input until the bound document changes, the exact signal is structurally gone, or the 7-second receipt budget expires. Ambiguity or budget exhaustion MUST remain an unconfirmed receipt and MUST NOT authorize another action.

#### Scenario: Pre-action cover still blocks login submission
- **WHEN** the Facebook login submit control is covered before Native dispatches input
- **THEN** Native reports no actionable login submit signal and performs no click

#### Scenario: Post-click loading cover is transitional evidence
- **WHEN** Native has dispatched the bound login submit action and the same submit control remains structurally present but becomes non-topmost under a loading cover
- **THEN** the postcondition remains unsatisfied and does not report the signal gone
- **AND** Native continues only the existing bounded postcondition observation without replaying the click

#### Scenario: Navigation confirms the submitted login action
- **WHEN** a temporarily covered login submit control is followed by a bound document or route transition to the supported Facebook 2FA page
- **THEN** Native confirms the original action from the document transition
- **AND** the coordinator discards the old observation and obtains a fresh 2FA probe before any further input

#### Scenario: Unchanged target after the receipt budget is not replayed
- **WHEN** the loading cover clears or the bounded receipt budget ends without document movement or structural signal disappearance
- **THEN** Native does not confirm the action and the coordinator MUST NOT replay the consumed signal id

#### Scenario: TOTP submit uses the same post-action distinction
- **WHEN** an already-dispatched Facebook 2FA submit control becomes temporarily non-topmost while the bound document is unchanged
- **THEN** that cover does not prove the 2FA submit signal disappeared
- **AND** Native preserves the same bounded, no-replay, fail-closed receipt behavior
