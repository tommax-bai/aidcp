# facebook-dev-autobrowse-policy Specification

## Purpose
TBD - created by archiving change facebook-dev-autobrowse-enable. Update Purpose after archive.
## Requirements
### Requirement: Facebook automatic browsing follows product lifecycle across environments

The desktop edge SHALL NOT derive Facebook browse authorization from the resolved Cloud environment or inject `AIDCP_FB_BROWSE_AUTO`. A Facebook core SHALL be capable of the existing browse-and-like loop in `dev`, `ol`, or a custom endpoint only when the platform/account lifecycle asks it to run; normal schedule, pause, identity, capability and risk controls remain authoritative. Non-Facebook cores MUST NOT start Facebook behavior.

#### Scenario: Facebook behavior is environment-neutral
- **WHEN** otherwise identical active Facebook accounts target `dev` and `ol`
- **THEN** neither is disabled solely because of the Cloud environment name, and both remain subject to the same scoped lifecycle and safety controls

#### Scenario: Paused lifecycle still stops browsing
- **WHEN** Cloud or the desktop lifecycle pauses a Facebook environment
- **THEN** automatic browsing stops regardless of inherited stale browse-mode environment values

#### Scenario: Non-Facebook profile is unaffected
- **WHEN** the operator starts a non-Facebook profile
- **THEN** it does not enter the Facebook browse-and-like loop

