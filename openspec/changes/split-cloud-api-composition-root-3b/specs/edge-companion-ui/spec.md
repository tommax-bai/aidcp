## MODIFIED Requirements

### Requirement: Recovery interaction reports Cloud write-after truth

Clicking `解除受限` SHALL first show a compact application-owned modal, not a native browser/system confirmation. The modal SHALL identify the selected environment, ask the customer to verify Facebook is usable, and state that the action only resumes AIDCP automation rather than proving Facebook's own block is cleared. After confirmation, the renderer SHALL call a named preload/main IPC with only the selected environment key. The client MUST NOT send an account identifier, risk signal selector, target status, audit reason, or command outcome.

While the initial request is pending, the same button SHALL be disabled. A `200` response SHALL be treated as success only when it contains the same `envKey` and automation's write-after `normal` state. A `202` response SHALL keep the environment visibly `restricted`, retain a pending state scoped to the exact `envKey + commandId`, and poll that command through the customer-auth environment-scoped result boundary. The client MUST NOT resubmit recovery merely because the initial response was `202`, locally clear `restricted`, synthesize `normal`, or claim that Edge resumed before Cloud returns an `applied` receipt.

While polling, `processing` SHALL keep the action disabled and preserve the last authoritative risk state. Only an `applied` result for the same selected environment and command, carrying write-after `normal`, SHALL clear the restricted presentation and consume the real resumed-edge count. A response for another environment or command MUST be discarded. Switching environments MUST NOT carry a pending command, result, status, or failure message into the newly selected environment.

`refused`, `failed`, and `unknown` SHALL have distinct customer-readable failure states. None of them may clear `restricted` locally or display recovery success. A terminal non-applied result or transport failure SHALL stop the pending presentation and make the action usable again when the environment's latest authoritative state still permits recovery; any subsequent status change SHALL come from a fresh Cloud risk-state response, not from inference based on the command outcome.

The `?` help panel SHALL explain that Facebook security checks, captcha evidence, or explicit throttle signals can pause automation; the customer should first confirm the account works; and a still-present platform block can stop work again. The UI MUST NOT claim that pressing the button solved the Facebook checkpoint or captcha itself.

#### Scenario: Confirmed recovery updates only the current environment
- **WHEN** the customer confirms recovery and Cloud returns `200` for the same `envKey` with automation's write-after `normal`
- **THEN** the button remains pending until that response and the restricted row then disappears for that environment
- **AND** other environments remain unchanged

#### Scenario: Accepted asynchronous recovery remains visibly pending
- **WHEN** the initial recovery request returns `202` with the same `envKey`, a `commandId`, and `processing`
- **THEN** the client keeps `账号受限` visible, keeps the recovery action disabled, and polls that exact command through the same environment
- **AND** it does not issue another recovery submission or present acceptance as success

#### Scenario: Polling completes with applied write-after truth
- **WHEN** polling later returns `applied` for the same environment and command with write-after `normal`
- **THEN** the client consumes that authoritative state, ends pending, removes the restricted row, and may display the returned real resumed-edge count
- **AND** it does not derive success from elapsed time, a local timer, or an earlier `202`

#### Scenario: Processing does not clear restricted state
- **WHEN** a recovery result poll continues to return `processing`
- **THEN** the selected environment remains visibly `账号受限` and the action remains pending
- **AND** the client does not replace the last authoritative state with `normal`, an empty state, or a generic success

#### Scenario: Refused, failed, and unknown remain distinct
- **WHEN** the result endpoint returns `refused`, `failed`, or `unknown`
- **THEN** the client ends the pending presentation and shows outcome-specific inline feedback rather than one generic success or endless processing state
- **AND** it does not locally clear `restricted` or claim that Edge resumed

#### Scenario: A stale result cannot update another environment
- **WHEN** the selected environment changes or a response carries a different `envKey` or `commandId` while recovery is pending
- **THEN** the renderer discards that response for the current view and does not change the current environment's risk state, button, or message

#### Scenario: Cancel does not call Cloud
- **WHEN** the customer clicks `暂不解除`, closes the modal, or presses Escape
- **THEN** no recovery IPC is sent and the restricted row remains unchanged

#### Scenario: Confirmation stays scoped to the environment shown
- **WHEN** the selected environment or its authoritative risk state changes while the modal is open
- **THEN** confirming the stale modal sends no recovery IPC
- **AND** the UI re-renders from the current environment's truth

#### Scenario: Recovery transport failure remains honest
- **WHEN** Cloud cannot be reached during submission or result polling
- **THEN** the environment remains at its last authoritative risk state, the pending presentation ends, and the action becomes usable again when recovery is still permitted
- **AND** an inline failure is shown without claiming that recovery or Edge resume occurred
