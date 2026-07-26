## RENAMED Requirements

- FROM: `### Requirement: Group join is disabled by default and fails closed`
- TO: `### Requirement: Group join is controlled by scoped account automation and fails closed`

## MODIFIED Requirements

### Requirement: Group join is controlled by scoped account automation and fails closed

Facebook unattended group joining SHALL be controlled by the account's explicit group-join automation configuration, active schedule window, platform match and account state. It MUST NOT require a process-global automatic or shadow environment variable. A per-group `enabled=false` or scope mismatch MUST exclude that group from assignment and joining. Risk quota, session budget, pre-click observation/judgment, exact target and confirmed outcome remain mandatory.

#### Scenario: Account automation off prevents joining
- **WHEN** an account's group-join automation configuration is disabled or its daily cap is zero
- **THEN** no group is joined or risk-recorded even if stale global join variables are enabled

#### Scenario: Account automation on needs no global switch
- **WHEN** account group-join automation and its current schedule slot are enabled and all target/risk/session gates pass
- **THEN** the scheduler may attempt one scoped join without requiring `AIDCP_FB_GROUP_JOIN_AUTO`

#### Scenario: Disabled group is excluded
- **WHEN** a group target has `enabled=false`
- **THEN** it is never assigned to an account and never navigated to for a join attempt
