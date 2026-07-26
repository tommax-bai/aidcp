## ADDED Requirements

### Requirement: Cancel control targets the corresponding queued publish task

The admin publish queue SHALL expose a cancel control for each displayed publish task in `queued`, `planning`, or `deferred` state, and SHALL submit the selected task identifier together with its displayed version to the delegated-task cancellation endpoint.

#### Scenario: Administrator confirms one queued task cancellation

- **WHEN** an administrator confirms cancellation on a specific queued publish task card
- **THEN** the Console sends one cancellation request for that task id with that task's current version
- **AND** no other queued task is mutated by that action

#### Scenario: Administrator dismisses cancellation confirmation

- **WHEN** an administrator closes or rejects the cancellation confirmation
- **THEN** the Console sends no cancellation request
- **AND** the queued task remains unchanged

### Requirement: Cancellation feedback reflects Cloud task truth

The admin publish queue MUST distinguish an immediately terminal cancellation from a cancellation request that Cloud will settle at a safe worker boundary, and MUST NOT claim that work has stopped without terminal evidence.

#### Scenario: Queued task becomes terminal immediately

- **WHEN** Cloud returns the task in a terminal cancelled state
- **THEN** the Console reports that the queued task was cancelled
- **AND** refreshes the queued-task and publish-lifecycle queries so the terminal task leaves the active queue

#### Scenario: Planning task accepts a cancellation request

- **WHEN** Cloud returns a non-terminal task with `cancelRequested=true`
- **THEN** the Console reports that the cancellation request was accepted and will settle at a safe boundary
- **AND** the refreshed card displays a cancellation-in-progress state without another enabled cancel action

### Requirement: Cancellation is concurrency-safe and recoverable

The admin publish queue MUST prevent duplicate cancellation submissions while a request is pending, MUST preserve the task when cancellation fails, and MUST refresh current task truth after a version conflict without automatically retrying the write.

#### Scenario: Cancellation request is pending

- **WHEN** a cancellation request for a queued task has not completed
- **THEN** the corresponding cancel control shows progress
- **AND** cancellation controls cannot submit another request until the pending request settles

#### Scenario: Displayed task version is stale

- **WHEN** Cloud rejects cancellation with a version conflict
- **THEN** the Console explains that the task state changed and refreshes the queued-task query
- **AND** it does not automatically retry cancellation against the new version

#### Scenario: Cancellation fails for another reason

- **WHEN** Cloud rejects or cannot complete the cancellation request for a reason other than a version conflict
- **THEN** the Console keeps the task visible and shows a human-readable failure message without exposing raw diagnostic codes
