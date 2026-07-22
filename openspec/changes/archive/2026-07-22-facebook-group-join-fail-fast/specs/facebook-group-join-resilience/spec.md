## RENAMED Requirements

- FROM: `### Requirement: Edge-task-lease failures SHALL be honest, audited, retryable transients`
- TO: `### Requirement: Edge-task-lease failures SHALL be honest, audited terminal attempt failures`

- FROM: `### Requirement: Slow-render observations SHALL be retryable, not terminal`
- TO: `### Requirement: Slow-render observations SHALL fail the current join attempt without cooldown`

- FROM: `### Requirement: Retry backoff SHALL be tiered by transient class`
- TO: `### Requirement: Join execution failures SHALL fail fast while account-level blockers retain pause`

## MODIFIED Requirements

### Requirement: Edge-task-lease failures SHALL be honest, audited terminal attempt failures

The join orchestration SHALL catch edge-task-lease acquisition and disconnect errors, mark the current membership `failed`, and write an audit row with the original lease failure reason. A lease failure MUST NOT leave the membership in `assigned` or `joining`, MUST NOT write a retry cooldown, and MUST NOT cause the next invocation to report `no_targets` while other scoped targets remain available. One account's lease failure MUST NOT abort the scheduler heartbeat for other accounts.

#### Scenario: Lease acquire timeout fails the current target immediately
- **WHEN** acquiring the browser task lease for a join attempt throws an acquire timeout, edge-offline, or disconnect error after a target was claimed
- **THEN** that membership becomes `failed` with the lease reason and an audit row, without a cooldown or hidden retry

#### Scenario: A failed lease does not block the next target
- **WHEN** the account invokes group join again after the previous target failed on lease acquisition and another scoped target is available
- **THEN** the scheduler may claim the other target and MUST NOT return `no_targets` because of the terminal failed row

### Requirement: Slow-render observations SHALL fail the current join attempt without cooldown

When the readiness poll exhausts with the page still below a minimal readiness threshold (document still loading or zero visible action nodes), the edge SHALL report a distinct not-ready outcome carrying readiness diagnostics and the cloud SHALL mark the current membership `failed`. The system MUST NOT schedule a hidden retry, write a minutes-scale cooldown, or call the fail-closed model on an unready observation.

#### Scenario: Ready poll exhausts on a still-loading page
- **WHEN** the join readiness poll reaches its deadline while the document is still loading or no action nodes are visible
- **THEN** the current target is marked `failed`, its not-ready reason is audited, and no cooldown is written

#### Scenario: Pre-click model call remains gated behind minimal readiness
- **WHEN** the observation is not minimally ready
- **THEN** the cloud does not spend a fail-closed pre-click model call and returns the honest current-attempt failure

### Requirement: Join execution failures SHALL fail fast while account-level blockers retain pause

Pure execution failures before confirmed membership—including observe/confirm timeouts, no-observation, navigation errors, not-ready, lease-unavailable, and post-confirmation slow render—SHALL immediately mark the current membership `failed`, retain the original reason in audit, and write no retry cooldown. The failed membership MUST stop occupying the account's unfinished-assignment slot so a later invocation can select another scoped target. Account-level login-required and captcha/checkpoint states SHALL retain their existing account pause, long backoff, and bounded-attempt behavior. Already-joined coverage cooldowns SHALL remain unchanged.

#### Scenario: Navigation failure is terminal for this target
- **WHEN** opening the claimed group page returns `nav_error`
- **THEN** the membership becomes `failed`, the result reports `nav_error`, no cooldown is written, and the command does not comment

#### Scenario: Next invocation selects another target
- **WHEN** a previous target is terminal `failed` due to a join execution failure and the account still has another eligible scoped group
- **THEN** the next invocation can claim the other group without waiting for a retry timer

#### Scenario: Account-level failure keeps the long backoff
- **WHEN** a join attempt encounters login-required or captcha
- **THEN** the account pause and long cooldown behavior apply unchanged rather than treating the account-wide blocker as one target's ordinary failure

#### Scenario: Joined coverage behavior is unchanged
- **WHEN** navigation fails while checking comment coverage for a membership already recorded `joined`
- **THEN** the existing left-confirmation/cooldown protection remains in force and the joined fact is not demoted by this change
