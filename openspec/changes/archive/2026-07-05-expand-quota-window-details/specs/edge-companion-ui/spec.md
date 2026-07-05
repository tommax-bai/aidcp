## MODIFIED Requirements

### Requirement: Electron Daily Summary Shows Multi-Window Quota Status

The Electron companion SHALL show quota status for each cloud-supplied quota window: current session, minute, hour, and day, while keeping the collapsed daily summary focused on today's account totals.

#### Scenario: Daily card is collapsed by default

- **WHEN** Electron has received account-scoped daily usage with quota windows
- **THEN** the collapsed card renders the day-window totals for view, like, collect, comment, follow, and publish
- **AND** it does not render session, minute, or hour action details until the user expands the card

#### Scenario: User expands the daily card

- **WHEN** the user clicks the daily usage card or its disclosure control
- **THEN** Electron renders quota detail for each supplied window: session, minute, hour, and day
- **AND** each window detail lists view, like, collect, comment, follow, and publish as separate action rows when totals are available
- **AND** each action row shows its supplied total and supplied cap when a cap exists

#### Scenario: Cloud supplies all quota windows

- **WHEN** `ui.snapshot.dailyUsage.windows` includes `session`, `minute`, `hour`, and `day`
- **THEN** Electron renders those windows as peer detail groups in the expanded area
- **AND** it marks saturated actions distinctly from near-limit actions without relying on a single worst-action summary as the only visible data

#### Scenario: Any window reaches its cap

- **WHEN** any supplied window's `saturated` list is non-empty, or any supplied action total is greater than or equal to that window's supplied cap
- **THEN** Electron's aggregate quota status presents a limit-reached state and identifies the saturated window labels
- **AND** the affected action rows are styled as saturated without changing global risk, captcha, or engine health states

#### Scenario: Session quota is not active

- **WHEN** the session window is supplied with `active: false`
- **THEN** Electron MAY show the configured single-session cap as inactive context, but MUST NOT imply that an active session is currently consuming that budget

#### Scenario: Window quota metadata is missing

- **WHEN** a window is missing, or an action total has no supplied cap
- **THEN** Electron MUST NOT fabricate caps, percentages, or limit-reached states for that action or window

#### Scenario: Rolling quota window snapshot expires

- **WHEN** a minute or hour window includes timing metadata and the local clock has passed the supplied expiry time without a fresher cloud snapshot
- **THEN** Electron MUST stop presenting that stale window as saturated
- **AND** it MAY keep rendering the window as waiting for refresh until a new cloud snapshot or local event updates it

### Requirement: Windowed Usage Snapshot Remains Backward Compatible

Cloud and edge SHALL preserve the existing `ui.snapshot.dailyUsage` daily aliases while adding optional windowed quota data.

#### Scenario: New cloud sends windowed usage to an old edge

- **WHEN** cloud includes `ui.snapshot.dailyUsage.windows`
- **THEN** the existing `dailyUsage.totals`, `dailyUsage.quotas`, and `dailyUsage.saturated` fields still describe the day window
- **AND** an older edge can ignore `windows` without losing the existing daily summary behavior

#### Scenario: New edge receives old daily-only usage

- **WHEN** Electron receives `ui.snapshot.dailyUsage` without `windows`
- **THEN** it SHALL continue to render daily totals and daily quota saturation as before
- **AND** it SHALL omit the expanded multi-window detail rather than inventing minute, hour, or session state

#### Scenario: Session window includes uncapped actions

- **WHEN** cloud can determine current-session totals for actions that do not have a single-session cap, such as view or publish
- **THEN** it MAY include those action totals in `windows.session.totals`
- **AND** it MUST omit quotas for uncapped session actions rather than copying caps from another window

#### Scenario: Cloud sends rolling-window timing metadata

- **WHEN** cloud sends minute, hour, or day quota-window status
- **THEN** it SHOULD include `startedAt`, `windowMs`, and `expiresAt` metadata for that window when the values are known
- **AND** older edges can ignore those fields without changing daily alias behavior
