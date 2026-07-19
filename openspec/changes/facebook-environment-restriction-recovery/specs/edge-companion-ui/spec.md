## ADDED Requirements

### Requirement: Selected Facebook environment shows an explicit compact restricted recovery row

The Electron companion SHALL render authoritative risk state in the selected environment's context. A selected Facebook environment in `restricted` SHALL be labeled `账号受限` in the title health result, risk detail, and environment rail, and SHALL show one compact row below the existing “今日进展” controls containing only one `解除受限` action button, one `?` help trigger, and inline failure feedback when needed. The UI MUST NOT duplicate the status label inside this row, add a large recovery card, or show the action for `normal`, `warned`, `frozen`, non-Facebook, or unknown risk state.

For a live environment the displayed state SHALL follow the live Cloud snapshot. For a stopped or disconnected environment the client SHALL obtain a fresh customer-auth environment-scoped risk read; it MUST NOT trust a locally initialized `normal` fallback, merge state across environments, or turn a failed read into a normal display.

#### Scenario: Stopped restricted Facebook environment remains visibly restricted
- **WHEN** the selected Facebook environment is stopped and its environment-scoped Cloud read returns `restricted`
- **THEN** the companion shows `账号受限` and the compact recovery row for that environment
- **AND** switching to another environment does not carry the state or button across

#### Scenario: Other states and platforms do not show the action
- **WHEN** the selected environment is not Facebook or its authoritative state is `normal`, `warned`, `frozen`, or unknown
- **THEN** the compact recovery row is hidden

#### Scenario: Restricted wording is explicit
- **WHEN** an environment is `restricted`
- **THEN** health, risk detail, and rail use `账号受限`
- **AND** they MUST NOT weaken the state to `节奏已调整` or `已调整节奏`

### Requirement: Recovery interaction reports Cloud write-after truth

Clicking `解除受限` SHALL first show a confirmation that the customer must verify Facebook is usable and that the action affects only the current environment. After confirmation, the renderer SHALL call a named preload/main IPC with only the selected environment key. While pending, the same button SHALL be disabled; success SHALL consume the Cloud write-after status immediately, while failure SHALL leave `账号受限` visible and show an inline failure message. The renderer MUST NOT locally clear the state before Cloud confirms it and MUST reject a response whose `envKey` does not match the request.

The `?` help panel SHALL explain that Facebook security checks, captcha evidence, or explicit throttle signals can pause automation; the customer should first confirm the account works; and a still-present platform block can stop work again. The UI MUST NOT claim that pressing the button solved the Facebook checkpoint or captcha itself.

#### Scenario: Confirmed recovery updates only the current environment
- **WHEN** the customer confirms recovery and Cloud returns the same `envKey` with write-after `normal`
- **THEN** the button enters a pending state until the response, then the restricted row disappears for that environment
- **AND** other environments remain unchanged

#### Scenario: Cancel does not call Cloud
- **WHEN** the customer declines the confirmation
- **THEN** no recovery IPC is sent and the restricted row remains unchanged

#### Scenario: Recovery failure remains honest
- **WHEN** Cloud rejects the request or cannot be reached
- **THEN** the environment remains visibly `账号受限`, the button becomes usable again, and an inline error is shown
