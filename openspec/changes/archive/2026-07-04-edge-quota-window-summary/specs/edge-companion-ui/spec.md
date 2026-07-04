## ADDED Requirements

### Requirement: Electron Daily Summary Shows Multi-Window Quota Status

The Electron companion SHALL show quota status for each cloud-supplied quota window: current session, minute, hour, and day.

#### Scenario: Cloud supplies all quota windows

- **WHEN** `ui.snapshot.dailyUsage.windows` includes `session`, `minute`, `hour`, and `day`
- **THEN** Electron renders a compact quota-window strip with labels for single-session, minute, hour, and today
- **AND** each window shows the worst supplied usage ratio for its capped actions and marks saturated actions distinctly from near-limit actions

#### Scenario: Any window reaches its cap

- **WHEN** any supplied window's `saturated` list is non-empty, or any supplied action total is greater than or equal to that window's supplied cap
- **THEN** Electron's aggregate quota status presents a limit-reached state and identifies the saturated window labels
- **AND** the affected window chip is styled as saturated without changing global risk, captcha, or engine health states

#### Scenario: Session quota is not active

- **WHEN** the session window is supplied with `active: false`
- **THEN** Electron MAY show the configured single-session cap as inactive context, but MUST NOT imply that an active session is currently consuming that budget

#### Scenario: Window quota metadata is missing

- **WHEN** a window is missing, or a window has totals without quotas
- **THEN** Electron MUST NOT fabricate caps, percentages, or limit-reached states for that window

### Requirement: Windowed Usage Snapshot Remains Backward Compatible

Cloud and edge SHALL preserve the existing `ui.snapshot.dailyUsage` daily aliases while adding optional windowed quota data.

#### Scenario: New cloud sends windowed usage to an old edge

- **WHEN** cloud includes `ui.snapshot.dailyUsage.windows`
- **THEN** the existing `dailyUsage.totals`, `dailyUsage.quotas`, and `dailyUsage.saturated` fields still describe the day window
- **AND** an older edge can ignore `windows` without losing the existing daily summary behavior

#### Scenario: New edge receives old daily-only usage

- **WHEN** Electron receives `ui.snapshot.dailyUsage` without `windows`
- **THEN** it SHALL continue to render daily totals and daily quota saturation as before
- **AND** it SHALL omit the multi-window quota strip rather than inventing minute, hour, or session state
