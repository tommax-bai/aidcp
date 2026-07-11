## ADDED Requirements

### Requirement: Daily Usage Windows Expose Refresh And Release Timing

Cloud SHALL include optional timing hints on `ui.snapshot.dailyUsage.windows`
when it can compute them without guessing. `refreshAt` SHALL mean the epoch-ms
time when cloud plans or recommends the next usage-window snapshot refresh.
`releaseAt` SHALL mean the epoch-ms time when a saturated quota in that window
is expected to release according to cloud's sliding-window counter. Cloud MUST
omit either field when the value is unknown, non-finite, or not derived from
cloud-owned state.

These fields SHALL be optional and backward compatible. Existing
`dailyUsage.totals`, `dailyUsage.quotas`, `dailyUsage.saturated`, and
`dailyUsage.windows.*.expiresAt` semantics MUST remain unchanged.

#### Scenario: Cloud supplies next refresh time

- **WHEN** cloud sends a daily usage window and knows when it will next refresh that window snapshot
- **THEN** the window MAY include `refreshAt` as a finite epoch-ms timestamp
- **AND** older edges can ignore `refreshAt` without losing existing daily usage rendering

#### Scenario: Cloud supplies quota release time

- **WHEN** a supplied minute, hour, or day window is saturated and cloud can compute the sliding-window release time
- **THEN** the window MAY include `releaseAt` as a finite epoch-ms timestamp
- **AND** that value MUST NOT be derived from local client clocks or aggregate totals alone

#### Scenario: Timing is unknown

- **WHEN** cloud cannot compute refresh or release timing for a supplied window
- **THEN** cloud MUST omit the corresponding timing field
- **AND** clients MUST NOT fabricate a countdown, clock time, or recovery promise for that missing field

### Requirement: Electron Daily Summary Displays Window Timing Honestly

The Electron companion SHALL preserve the existing expanded daily usage window
layout and SHALL display cloud-supplied timing hints when present. If a window
is saturated and `releaseAt` is in the future, Electron SHOULD show the release
hint alongside the capped action context. If a window is stale or awaiting a
new snapshot and `refreshAt` is present, Electron SHALL show the planned refresh
time instead of only the generic `等待云端快照` copy. Electron MUST keep the
current fallback wording when timing is absent.

#### Scenario: Saturated window shows release hint

- **WHEN** Electron renders an expanded quota window with a future `releaseAt`
- **THEN** the window metadata identifies the capped action context and includes a human-readable release hint
- **AND** global risk, captcha, or engine health states are not changed by this display-only hint

#### Scenario: Waiting window shows planned refresh

- **WHEN** Electron renders a minute or hour window as waiting for refresh and the window has `refreshAt`
- **THEN** the metadata includes the planned refresh clock time or countdown
- **AND** if that time has already passed without a newer snapshot, Electron MUST still present the state as waiting rather than marking the quota usable

#### Scenario: Old snapshots still render

- **WHEN** Electron receives `ui.snapshot.dailyUsage.windows` without `refreshAt` or `releaseAt`
- **THEN** it SHALL render the existing window state, totals, quotas, and stale fallback text as before

### Requirement: Cloud Refreshes Online Daily Usage Snapshots Best-Effort

After sending account-scoped daily usage to an online edge, cloud SHALL schedule
a best-effort daily-usage-only `ui.snapshot` refresh for that same account and
edge when a finite future `refreshAt` is available. The scheduled refresh MUST
be targeted to the same edge, MUST NOT broadcast to unrelated edges, and MUST
stop retrying when the edge is no longer online or the targeted push is not
delivered.

#### Scenario: Online edge receives a scheduled usage refresh

- **WHEN** cloud has sent daily usage with a future `refreshAt` to an online edge
- **THEN** cloud SHALL attempt a targeted `ui.snapshot` containing fresh `dailyUsage` at or after that time
- **AND** the refreshed snapshot MAY schedule the next refresh using its new timing metadata

#### Scenario: Offline edge does not cause retry storm

- **WHEN** a scheduled daily usage refresh push reaches no edge
- **THEN** cloud MUST stop that scheduled refresh chain for the account-edge pair
- **AND** it MUST NOT broadcast the snapshot to other edges for the account
