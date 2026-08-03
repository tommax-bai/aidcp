## ADDED Requirements

### Requirement: Terminal Reels scroll outcomes continue through normal admission
When a confirmed Facebook Reels session receives a terminal failed scroll receipt whose reason is Reels-specific, Cloud SHALL request one next scroll without waiting for the generic idle watchdog. The continuation MUST pass the existing view-quota, session, soft-pause, interaction-hold, command-dedupe, and dwell gates. It MUST NOT count a view, create interaction cadence, create retry debt, or bypass normal pacing solely because the prior scroll failed.

#### Scenario: Reels navigation is unconfirmed
- **WHEN** Edge reports `action.completed{action:'scroll', ok:false, reason:'reels_navigation_unconfirmed'}` in a confirmed Reels session
- **THEN** Cloud SHALL issue one normally admitted continuation scroll and SHALL NOT wait for the idle watchdog

#### Scenario: Reels identity remains unresolved
- **WHEN** Edge reports `reels_identity_unresolved` or `reels_target_unavailable` in a confirmed Reels session
- **THEN** Cloud SHALL issue one normally admitted continuation scroll without creating a view or interaction opportunity

#### Scenario: Existing admission gate suppresses continuation
- **WHEN** the continuation is rejected by view quota, soft pause, interaction hold, session end, or command dedupe
- **THEN** Cloud SHALL preserve that gate's existing recovery or terminal behavior and SHALL NOT create a bypass timer or debt
