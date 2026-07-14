## ADDED Requirements

### Requirement: 人设绑定态为三态，未知绝不等同未绑

The `personaBound` signal on the `ui.snapshot` stream SHALL carry three states: `true` (cloud confirms bound), `false` (cloud confirms unbound), and **absent** (unknown — the cloud has not said yet). Cloud is the single writer of persona state and therefore SHALL send both `true` and `false`. Edge MUST NOT treat "unknown" as "unbound": no timer, grace window, or timeout may promote unknown into unbound.

#### Scenario: 云端确认未绑才算未绑
- **WHEN** cloud has determined the account has no persona
- **THEN** cloud sends `personaBound: false`, and edge may present the account as "未设置"

#### Scenario: 信号未到时保持未知
- **WHEN** the edge is logged in and connected but has not yet received a `personaBound` signal
- **THEN** edge presents the persona state as pending ("待启动"), never as "未设置", and no amount of elapsed time changes that

#### Scenario: 解绑即时可见
- **WHEN** a persona is bound or unbound (including "saving an empty persona = explicit unbind")
- **THEN** cloud repushes the new bound state to the account's online edge immediately, without waiting for the next handshake

#### Scenario: 绑定态不被慢快照拖住
- **WHEN** the hello snapshot requires slow database round-trips to assemble
- **THEN** the persona bound state — a zero-I/O in-memory read — is delivered ahead of them, not behind them

### Requirement: 人设向导只能由权威的「未绑」自动弹出

The desktop client SHALL auto-open the persona setup wizard only when the cloud has authoritatively reported `personaBound: false` for the currently selected environment. Absence of the signal MUST NOT trigger it. Any state reset (core respawn, cold-standby wake, environment removal and re-add) MUST at worst return the state to "unknown", which never prompts.

#### Scenario: 已设置人设的账号永不被误弹
- **WHEN** an account that has a persona restarts its core (e.g. cold-standby wake), transiently returning its bound state to unknown
- **THEN** the wizard does not open and no system notification is sent

#### Scenario: 真正未设置的账号照常被提醒
- **WHEN** cloud reports `personaBound: false` for a logged-in, connected account
- **THEN** the wizard opens once and one system notification is sent

#### Scenario: 系统误弹的窗在权威「已绑」到达时自动收起
- **WHEN** the wizard was opened automatically and an authoritative `personaBound: true` subsequently arrives for that environment
- **THEN** the client closes the auto-opened wizard; a wizard the user opened by hand is never closed for them
