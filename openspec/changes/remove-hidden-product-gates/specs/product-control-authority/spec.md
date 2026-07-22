## ADDED Requirements

### Requirement: Visible product configuration is the sole ordinary-business authorization

When an account, channel, schedule, or approval behavior has a supported product configuration surface, the system SHALL use that scoped configuration as the sole ordinary-business authorization. A process environment variable, deployment-name allowlist, hidden account list, local client flag, or operator-recorded rollout token MUST NOT silently deny or downgrade an action that the product configuration authorizes.

Infrastructure and safety gates MAY still deny an action only when they represent deployment-target isolation, schema compatibility, active identity and account binding, current platform capability, endpoint circuit state, risk state, rate limit, concurrency, idempotency, irreversible-write validation, or an environment-wide emergency stop whose effective state is projected to the system. Such denial MUST remain observable and MUST NOT be reported as success.

#### Scenario: Enabled account is not downgraded by a hidden allowlist
- **WHEN** an account has a published automatic policy, enabled channel and rule, enabled runtime controls, valid identity/capability, and remaining risk/rate budget
- **THEN** automatic execution proceeds to its normal queue/send path without requiring an environment account allowlist

#### Scenario: Hard safety gate still blocks honestly
- **WHEN** the same account is identity-mismatched, risk-blocked, rate-limited, circuit-open, or globally emergency-paused
- **THEN** the action is rejected or deferred with its real reason and no success is recorded

### Requirement: Removed hidden gates cannot regain authority through stale environment values

Deleted product gates SHALL be ignored after upgrade even if a stale deployment file, inherited shell, or desktop environment still contains their old names and values. Regression tests SHALL exercise representative stale true and false values and prove identical product behavior.

#### Scenario: Stale disabled value is inert
- **WHEN** a deployment retains an old hidden gate with a false/off value after the new version starts
- **THEN** the corresponding product behavior is determined by scoped configuration and safety gates, not by that stale value

#### Scenario: Stale enabled value cannot bypass a visible off state
- **WHEN** a deployment retains an old hidden gate with a true/on value while the account or channel product setting is disabled
- **THEN** no action occurs and the stale value grants no authority
