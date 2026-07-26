## ADDED Requirements

### Requirement: Selected Facebook environment shows an explicit compact restricted recovery row

The Electron companion SHALL render authoritative risk state in the selected environment's context. A selected Facebook environment in `restricted` SHALL be labeled `账号受限` in the title health result, risk detail, and environment rail, and SHALL show one compact row below the existing “今日进展” controls containing only one `解除受限` action button, one `?` help trigger, and inline failure feedback when needed. The UI MUST NOT duplicate the status label inside this row, add a large recovery card, or show the action for `normal`, `warned`, `frozen`, non-Facebook, or unknown risk state.

For a live environment the displayed state SHALL follow the live Cloud snapshot. For a stopped or disconnected environment the client SHALL obtain a fresh customer-auth environment-scoped risk read; it MUST NOT trust a locally initialized `normal` fallback, merge state across environments, or turn a failed read into a normal display.

When the effective state is `restricted`, that state SHALL override the generic `session=resting` presence fallback. The companion MUST NOT describe a risk-triggered pause as a completed browse round or promise the normal automatic-resume countdown.

#### Scenario: Stopped restricted Facebook environment remains visibly restricted
- **WHEN** the selected Facebook environment is stopped and its environment-scoped Cloud read returns `restricted`
- **THEN** the companion shows `账号受限` and the compact recovery row for that environment
- **AND** switching to another environment does not carry the state or button across

#### Scenario: Other states and platforms do not show the action
- **WHEN** the selected environment is not Facebook or its authoritative state is `normal`, `warned`, `frozen`, or unknown
- **THEN** the compact recovery row is hidden

#### Scenario: Risk-triggered standby is not presented as completed work
- **WHEN** the selected environment is `restricted`, its session projection is `resting`, and browse progress is still below quota
- **THEN** the presence headline says automatic operation is paused because the account is restricted
- **AND** it does not say the round completed or show the normal auto-resume countdown

#### Scenario: Restricted wording is explicit
- **WHEN** an environment is `restricted`
- **THEN** health, risk detail, and rail use `账号受限`
- **AND** they MUST NOT weaken the state to `节奏已调整` or `已调整节奏`

### Requirement: Recovery interaction reports Cloud write-after truth

Clicking `解除受限` SHALL first show a compact application-owned modal, not a native browser/system confirmation. The modal SHALL identify the selected environment, ask the customer to verify Facebook is usable, and state that the action only resumes AIDCP automation rather than proving Facebook's own block is cleared. After confirmation, the renderer SHALL call a named preload/main IPC with only the selected environment key. While pending, the same button SHALL be disabled; success SHALL consume the Cloud write-after status immediately, while failure SHALL leave `账号受限` visible and show an inline failure message. The renderer MUST NOT locally clear the state before Cloud confirms it and MUST reject a response whose `envKey` does not match the request.

The `?` help panel SHALL explain that Facebook security checks, captcha evidence, or explicit throttle signals can pause automation; the customer should first confirm the account works; and a still-present platform block can stop work again. The UI MUST NOT claim that pressing the button solved the Facebook checkpoint or captcha itself.

#### Scenario: Confirmed recovery updates only the current environment
- **WHEN** the customer confirms recovery and Cloud returns the same `envKey` with write-after `normal`
- **THEN** the button enters a pending state until the response, then the restricted row disappears for that environment
- **AND** other environments remain unchanged

#### Scenario: Cancel does not call Cloud
- **WHEN** the customer clicks `暂不解除`, closes the modal, or presses Escape
- **THEN** no recovery IPC is sent and the restricted row remains unchanged

#### Scenario: Confirmation stays scoped to the environment shown
- **WHEN** the selected environment or its authoritative risk state changes while the modal is open
- **THEN** confirming the stale modal sends no recovery IPC
- **AND** the UI re-renders from the current environment's truth

#### Scenario: Recovery failure remains honest
- **WHEN** Cloud rejects the request or cannot be reached
- **THEN** the environment remains visibly `账号受限`, the button becomes usable again, and an inline error is shown
