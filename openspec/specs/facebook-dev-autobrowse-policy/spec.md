# facebook-dev-autobrowse-policy Specification

## Purpose
TBD - created by archiving change facebook-dev-autobrowse-enable. Update Purpose after archive.
## Requirements
### Requirement: Facebook automatic browsing follows product lifecycle across environments

The desktop edge SHALL NOT derive Facebook browse authorization from the resolved Cloud environment or inject `AIDCP_FB_BROWSE_AUTO`. A Facebook core SHALL be capable of automatic browsing in `dev`, `ol`, or a custom endpoint only when the platform/account lifecycle asks it to run. Cloud SHALL select either the existing persona browse mode or the account's enabled fixed Facebook rule mode before session assembly; the Edge MUST NOT choose or widen that mode. Normal active schedule, slow-start precedence, pause, identity, capability, accounting and risk controls remain authoritative. Non-Facebook cores MUST NOT start Facebook behavior or accept Facebook rule-mode configuration.

#### Scenario: Facebook behavior is environment-neutral
- **WHEN** otherwise identical active Facebook accounts target `dev` and `ol`
- **THEN** neither is disabled solely because of the Cloud environment name, and both remain subject to the same scoped lifecycle and safety controls

#### Scenario: Paused lifecycle still stops browsing
- **WHEN** Cloud or the desktop lifecycle pauses a Facebook environment
- **THEN** automatic browsing stops regardless of inherited stale browse-mode environment values

#### Scenario: Cloud chooses rule mode
- **WHEN** an eligible Facebook account has rule mode enabled, slow start is not active and its active-window cell permits browsing
- **THEN** Cloud assembles the fixed rule-mode loop and Edge executes only the resulting admitted atomic commands

#### Scenario: Non-Facebook profile is unaffected
- **WHEN** the operator starts a non-Facebook profile or attempts to enable Facebook rule mode for it
- **THEN** it does not enter the Facebook browse loop and the rule-mode write is rejected

