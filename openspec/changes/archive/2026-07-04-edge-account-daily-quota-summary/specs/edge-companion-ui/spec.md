## ADDED Requirements

### Requirement: Electron Daily Summary Uses Account-Scoped Cloud Usage

The Electron companion SHALL prefer cloud-supplied account-scoped daily usage over locally accumulated log counters for the "today" summary when `ui.snapshot.dailyUsage` is available.

#### Scenario: Hello snapshot replaces local counters with account today totals

- **WHEN** cloud sends `ui.snapshot.dailyUsage` for the account bound to the edge
- **THEN** Electron renders the supplied account daily totals for view, like, collect, comment, follow, and publish instead of treating the local process's current-session deltas as authoritative

#### Scenario: Local counters remain a fallback before cloud usage arrives

- **WHEN** Electron has not yet received `ui.snapshot.dailyUsage`
- **THEN** it MAY continue to show local log-derived deltas for available actions, and MUST NOT present quota caps or saturation as if they were authoritative

### Requirement: Electron Daily Summary Shows Current Daily Quota Saturation

The Electron companion SHALL show daily quota context for each supplied action when cloud includes the current quota level's daily caps.

#### Scenario: Action reaches the current level's daily limit

- **WHEN** `ui.snapshot.dailyUsage.saturated` includes an action, or the supplied total is greater than or equal to the supplied cap for that action
- **THEN** Electron marks that metric as saturated and presents it as a limit-reached state distinct from global risk warnings or captcha restrictions

#### Scenario: Quota metadata is missing

- **WHEN** totals are supplied without quotas
- **THEN** Electron renders the account daily totals without fabricating caps, progress, or limit-reached states

### Requirement: Daily Usage Snapshot Remains Backward Compatible

Cloud and edge SHALL keep `ui.snapshot.dailyUsage` optional and backward compatible with older peers.

#### Scenario: Old edge ignores the field

- **WHEN** an older edge receives `ui.snapshot` with unknown daily usage fields
- **THEN** the message remains a valid snapshot and the old edge can ignore the extra field without breaking identity, last publish, or publish-card rendering
