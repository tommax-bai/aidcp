## ADDED Requirements

### Requirement: Electron Presence Explains Quota Rest State

The Electron companion SHALL distinguish quota-driven waiting from generic stale activity in the presence strip when cloud-supplied quota-window data shows that the current running session has reached an active limit.

#### Scenario: Current quota window is saturated

- **WHEN** Electron is in a running session, the latest presence event is stale, and `ui.snapshot.dailyUsage.windows` shows a current session, minute, hour, or day window with at least one saturated capped action
- **THEN** the presence strip SHALL render a quota-specific rest message naming the action and window
- **AND** it SHALL include the estimated remaining wait until `releaseAt` when that timestamp is available and in the future
- **AND** the presence strip MUST NOT animate as if work is still happening

#### Scenario: Quota evidence is stale or incomplete

- **WHEN** the latest presence event is stale but the relevant quota window is expired, missing, or lacks capped saturated action evidence
- **THEN** Electron SHALL keep the existing stale-activity fallback instead of fabricating a quota-rest explanation
