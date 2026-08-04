## ADDED Requirements

### Requirement: Facebook suspension appeal entry is one bounded operator handoff

For a proven fresh managed Facebook start, the reconciler SHALL treat the observed account-suspension appeal entry as one independent `suspension_appeal_start` signal and `facebook_auth_start_suspension_appeal` action. The signal MUST require Facebook origin, a numeric checkpoint route with the canonical Facebook next destination, the observed suspension and appeal instruction structure, and exactly one visible enabled topmost control whose accessible label is `Appeal`. The action SHALL fresh-revalidate the target-bound signal id, use Native CDP pointer movement and press/release, and MUST NOT be replayed after any committed or ambiguous receipt.

The action is confirmed only after bounded polling proves that the original suspension entry is gone and a distinct, complete, non-loading Facebook checkpoint step is present. Confirmation means only that the appeal entry advanced. Edge SHALL then retain the owned browser as `facebook_suspension_appeal_step_required`, block runnable account identity/Cloud startup, and perform no later appeal input or submission.

#### Scenario: Loaded suspension entry has one actionable Appeal clone
- **WHEN** the exact observed suspension checkpoint is complete and its DOM contains a hidden disabled `Appeal` clone plus one visible enabled topmost `Appeal` control
- **THEN** Native binds only the visible enabled topmost control and emits one suspension-appeal signal
- **AND** the hidden clone does not make the actionable target ambiguous

#### Scenario: Appeal entry advances after trusted input
- **WHEN** action-time revalidation returns the same target-bound signal and Native CDP pointer input activates it
- **THEN** Edge polls through bounded loading and confirms only after the original suspension entry is gone and a distinct complete non-loading Facebook checkpoint step is present
- **AND** it reports `facebook_suspension_appeal_step_required`, retains the browser/CDP, and does not establish a runnable account

#### Scenario: Loading or button mutation is not success
- **WHEN** the `Appeal` control disappears, becomes disabled, is covered, or the page shows only loading after the pointer press
- **THEN** Native continues bounded postcondition polling without treating those intermediate changes as success
- **AND** timeout or unreadable/unsupported destination returns an honest ambiguous result with no click replay

#### Scenario: Exact page or target contract is absent
- **WHEN** the origin, numeric checkpoint route, canonical next destination, suspension content, accessible label, visibility, enabled state, uniqueness, or top-hit check does not match
- **THEN** Edge dispatches no pointer input and reports the checkpoint as unsupported or blocked

#### Scenario: Later appeal steps remain operator owned
- **WHEN** a confirmed entry action reaches a later checkpoint step
- **THEN** Edge performs no option selection, text entry, confirmation, verification, or appeal submission
- **AND** a later unsupported checkpoint remains a deferred manual state only in the context of the confirmed appeal-entry handoff, while CAPTCHA and other failures still fail closed

#### Scenario: Operator clears the checkpoint
- **WHEN** the retained browser later reaches a supported authenticated non-checkpoint page after operator handling
- **THEN** the normal fresh auth probe and stable identity gate may resume
- **AND** account/Cloud startup still requires canonical identity readback rather than the earlier Appeal action receipt
