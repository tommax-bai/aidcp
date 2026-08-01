## ADDED Requirements

### Requirement: Legacy orchestration SHALL honor the Automation account lane

All legacy orchestration scheduling and dispatch entrypoints SHALL consult the same Automation-owned account lane before sending work. A managed TaskRun lease for one `execution_target + account_id` SHALL exclude incompatible legacy work only for that account. The exclusion MUST be based on durable lane state, not process-local socket mode or an unverified client claim.

#### Scenario: Managed task and legacy schedule become eligible together
- **WHEN** a managed TaskRun owns account A's lane while a legacy schedule for account A becomes due
- **THEN** the legacy schedule SHALL remain unclaimed or skipped with `managed_task_lane_active` and SHALL send no command

#### Scenario: Two accounts have different owners
- **WHEN** account A is managed-task-owned and account B is legacy-eligible
- **THEN** their decision contexts and dispatches SHALL advance independently without cross-account exclusion

#### Scenario: Connection replacement occurs
- **WHEN** account A's Edge socket is replaced during an active managed lane
- **THEN** the new connection SHALL inherit only transport routing; durable lane ownership SHALL remain unchanged until Automation releases or recovers it

### Requirement: Managed lane activation SHALL be reversible without changing legacy defaults

The managed lane integration SHALL be default-disabled. While disabled, existing orchestration eligibility and dispatch SHALL remain unchanged. Disabling new managed claims SHALL stop future lane acquisition but MUST NOT erase a lane that still protects an in-flight Attempt; that lane SHALL remain until receipt/reconciliation reaches its declared release condition.

#### Scenario: Feature remains disabled
- **WHEN** no managed lane flag is enabled
- **THEN** legacy orchestration SHALL behave as before and no TaskRun SHALL acquire a managed lane

#### Scenario: Kill switch during an in-flight attempt
- **WHEN** operators disable new managed work while a TaskRun has a dispatched Attempt
- **THEN** Automation SHALL stop new claims and steps but retain the account exclusion until the Attempt's safe release condition is met
