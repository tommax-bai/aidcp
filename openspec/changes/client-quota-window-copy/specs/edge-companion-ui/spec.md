## MODIFIED Requirements

### Requirement: Electron Daily Summary Shows Multi-Window Quota Status
The Electron companion SHALL show plan progress for each cloud-supplied quota window: current session, minute, hour, and day, while keeping the collapsed daily summary focused on today's account totals. Expanded labels SHALL identify those scopes as “本轮计划”, “近 1 分钟”, “近 1 小时”, and “今日计划”. The client MUST NOT describe the session as a rolling “近 N 分钟” window. Expanded detail SHALL preserve exact supplied totals and caps while presenting a cap as a secondary “最多 N” boundary rather than a slash-form completion target.

#### Scenario: Daily card is collapsed by default

- **WHEN** Electron has received account-scoped daily usage with quota windows
- **THEN** the collapsed card renders the day-window totals for exactly the actions the cloud supplied for that account
- **AND** it does not render session, minute, or hour action details until the user expands the card

#### Scenario: User expands the daily progress card

- **WHEN** the user clicks the daily progress card or its disclosure control
- **THEN** Electron renders plan detail labeled “本轮计划”, “近 1 分钟”, “近 1 小时”, and “今日计划” for the supplied session, minute, hour, and day windows respectively
- **AND** each window detail lists as separate action rows exactly those actions for which that window supplies a total or a cap, and no others
- **AND** each capped action row shows its supplied total followed by secondary “最多 N” wording
- **AND** an uncapped action row shows its supplied total without `/-`, a fabricated cap, or cap progress styling

#### Scenario: Active session has trustworthy timing

- **WHEN** the session window is active and supplies finite `startedAt` and future `expiresAt` timestamps
- **THEN** the “本轮计划” group shows the remaining round time in its state area
- **AND** its metadata shows the local start time and expected end time
- **AND** the client derives both displays from the supplied timestamps rather than hard-coding the configured round duration

#### Scenario: Cloud supplies all quota windows

- **WHEN** `ui.snapshot.dailyUsage.windows` includes `session`, `minute`, `hour`, and `day`
- **THEN** Electron renders those windows as peer detail groups ordered session, minute, hour, and day
- **AND** the groups use a 2×2 grid at the normal companion width and a one-column grid at the existing narrow breakpoint
- **AND** it marks completed actions distinctly from near-complete actions without relying on a single worst-action summary as the only visible data

#### Scenario: Any window completes its plan

- **WHEN** any supplied window's `saturated` list is non-empty, or any supplied action total is greater than or equal to that window's supplied cap
- **THEN** Electron's aggregate progress status identifies completed action plans
- **AND** the affected action rows use green completion styling without changing global risk, captcha, or engine health states
- **AND** an available future `releaseAt` is described as the time the action will continue, not as quota release

#### Scenario: Session plan is not active

- **WHEN** the session window is supplied with `active: false`
- **THEN** Electron MAY show the configured single-session plan as waiting to start, but MUST NOT imply that an active session is currently consuming that plan
- **AND** it MUST NOT fabricate remaining time or an expected end time

#### Scenario: Window quota metadata is missing

- **WHEN** a window is missing, or an action total has no supplied cap
- **THEN** Electron MUST NOT fabricate caps, percentages, or plan-completed states for that action or window

#### Scenario: Rolling quota window snapshot expires

- **WHEN** a minute or hour window includes timing metadata and the local clock has passed the supplied expiry time without a fresher cloud snapshot
- **THEN** Electron MUST stop presenting that stale window as completed
- **AND** it MAY keep rendering the window as preparing the next round until a new cloud snapshot or local event updates it
