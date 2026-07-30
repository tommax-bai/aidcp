## MODIFIED Requirements

### Requirement: Group join is controlled by scoped account automation and fails closed

Facebook independent time-scheduled unattended group joining SHALL be controlled by the account's explicit group-join automation configuration, active schedule window, platform match, account state, and authoritative effective operation mode. The scheduler MAY trigger only when that mode is `persona`. Effective `slow_start`, `rule`, or `consumption` mode MUST suppress the independent scheduled trigger before target assignment or navigation. The mode MUST be resolved from the environment operation-policy authority; an unavailable, unknown, conflicting, or stale projection SHALL fail closed and MUST NOT be guessed as `persona`.

The scheduled join path MUST NOT require a process-global automatic or shadow environment variable. A per-group `enabled=false` or scope mismatch MUST exclude that group from assignment and joining. Risk quota, session budget, pre-click observation/judgment, exact target and confirmed outcome remain mandatory.

This restriction governs the independent schedule trigger, not the atomic group-join executor. Rule, consumption, slow-start, manual, or other explicitly specified orchestration MAY invoke that existing executor only according to its own contract, while preserving all group scope, ownership, risk, session, target, observation, click and confirmation gates. Invoking the executor from a mode-specific orchestration MUST NOT create, consume, or impersonate an independent scheduled-join fire.

#### Scenario: Account automation off prevents joining
- **WHEN** an account's group-join automation configuration is disabled or its daily cap is zero
- **THEN** no independently scheduled group is joined or risk-recorded even if stale global join variables are enabled

#### Scenario: Account automation on needs no global switch
- **WHEN** account group-join automation and its current schedule slot are enabled, the effective mode is `persona`, and all target/risk/session gates pass
- **THEN** the scheduler may attempt one scoped join without requiring `AIDCP_FB_GROUP_JOIN_AUTO`

#### Scenario: Disabled group is excluded
- **WHEN** a group target has `enabled=false`
- **THEN** it is never assigned to an account and never navigated to for a join attempt

#### Scenario: Non-persona mode suppresses the independent scheduler
- **WHEN** the time-scheduled join slot arrives while the authoritative effective mode is `slow_start`, `rule`, or `consumption`
- **THEN** the scheduler does not assign a target, navigate, click, dispatch a join or create a synthetic scheduled outcome

#### Scenario: Mode-specific orchestration can use the atomic executor
- **WHEN** rule or consumption orchestration reaches its own contractually authorized join stage
- **THEN** it may invoke the atomic group-join executor subject to every existing scope, risk, session, exact-target and confirmed-outcome gate
- **AND** that invocation is attributed to the mode-specific batch rather than the independent schedule

#### Scenario: Unknown operation mode fails closed
- **WHEN** the scheduled join tick cannot resolve one authoritative fresh effective operation mode for the account's environment
- **THEN** it does not join, risk-record, or infer `persona`, and exposes the named policy or binding blocker
