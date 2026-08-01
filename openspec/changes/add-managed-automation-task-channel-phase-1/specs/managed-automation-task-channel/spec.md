## ADDED Requirements

### Requirement: Automation SHALL own the phase-one task authority

Automation SHALL be the single writer of Task, TaskRevision, immutable ExecutionPlan, TaskRun, StepRun, ExecutionIntent, ExecutionAttempt, DecisionTrace, and account lane state. API, Agent, Client, Content, and Edge MUST NOT write those records directly or construct a second task worker.

#### Scenario: API creates a task
- **WHEN** an authorized API caller requests a phase-one task
- **THEN** API SHALL send a versioned command to Automation and Automation SHALL create the authoritative records in its owner database

#### Scenario: Edge reports execution evidence
- **WHEN** Edge reports an atomic command outcome
- **THEN** Automation SHALL append the Attempt/Trace transition and Edge MUST NOT decide the TaskRun terminal state

### Requirement: Task entry commands SHALL be versioned, authorized, target-bound, and idempotent

CreateTask, CancelTask, and QueryTask SHALL carry a supported contract version, authenticated actor context, account scope, and server-injected `execution_target`. CreateTask and CancelTask SHALL carry stable command identifiers and return applied, duplicate, collision, rejected, or result-unknown outcomes without converting transport ambiguity into business success.

#### Scenario: Duplicate create command
- **WHEN** Automation receives the same target and command id with the same canonical payload
- **THEN** it SHALL return the original receipt and MUST NOT create a second Task or TaskRun

#### Scenario: Command id collision
- **WHEN** the same target and command id is reused with a different canonical payload
- **THEN** Automation SHALL reject it as a collision with zero task-state mutation

#### Scenario: Target mismatch
- **WHEN** a request target differs from the local Automation target or local target is missing or invalid
- **THEN** the command SHALL be rejected before any owner read or write and the worker SHALL remain disabled

### Requirement: ExecutionPlans SHALL be immutable bounded compiled artifacts

PlanCompiler SHALL resolve a registered TaskDefinition version, exact Capability versions, TaskRevision parameters, CapabilityScope, authorization revision, bounds, and completion conditions into one immutable ExecutionPlan with a stable hash. Every TaskRun SHALL reference exactly one TaskRevision and one ExecutionPlan. Phase one SHALL accept only bounded acyclic linear graphs from the code registry.

#### Scenario: Valid read-only research task
- **WHEN** `persona.research@1` parameters and authorization pass schema and scope validation
- **THEN** the compiler SHALL emit the registered search, browse, assess, and summarize nodes with exact versions and a stable plan hash

#### Scenario: Unknown or unbounded graph
- **WHEN** a TaskDefinition version is unknown, a node capability is unsupported, or the graph exceeds its declared bound
- **THEN** compilation SHALL fail before a TaskRun becomes claimable

#### Scenario: Task revision changes
- **WHEN** parameters or authorization revision change after plan creation
- **THEN** the system SHALL create a new TaskRevision, ExecutionPlan, and TaskRun rather than mutate the existing plan

### Requirement: Durable work SHALL use target-scoped CAS and leases

TaskRun and StepRun claims SHALL use atomic compare-and-set transitions, bounded leases, owner identity, attempt counters, and target filters. A worker MUST NOT claim, recover, or mutate another target's rows. Terminal TaskRun, StepRun, and Attempt states MUST reject regression.

#### Scenario: Competing workers claim one run
- **WHEN** two workers try to claim the same eligible TaskRun
- **THEN** exactly one SHALL acquire the lease and the other SHALL observe a non-claim result

#### Scenario: Lease expires after worker loss
- **WHEN** a worker disappears while holding a lease
- **THEN** recovery SHALL wait for expiry, inspect persisted step and attempt state, and resume from the durable boundary without rewriting completed steps

#### Scenario: Terminal regression
- **WHEN** a stale worker tries to change a terminal run or attempt back to a non-terminal state
- **THEN** the CAS SHALL fail and the terminal evidence SHALL remain unchanged

### Requirement: Account lanes SHALL arbitrate managed tasks and legacy orchestration

Before executing a TaskRun, Automation SHALL acquire the lane keyed by `execution_target + account_id`. It SHALL acquire managed ownership only after confirming no incompatible legacy work is in flight. While the managed lease is active, every legacy scheduling and dispatch entrypoint for that account SHALL skip with a stable observable reason. Other accounts SHALL remain independently schedulable.

#### Scenario: Legacy work is already active
- **WHEN** a managed TaskRun reaches the head of its queue while the same account has incompatible legacy work in flight
- **THEN** the TaskRun SHALL remain waiting and MUST NOT preempt or dispatch through that account

#### Scenario: Managed task owns the lane
- **WHEN** a TaskRun has acquired the managed lane
- **THEN** legacy entrypoints for that account SHALL return `managed_task_lane_active` and dispatch no Edge command

#### Scenario: Different account remains available
- **WHEN** account A holds a managed lane and account B is otherwise eligible for legacy work
- **THEN** account B SHALL continue independently and MUST NOT inherit account A's exclusion

### Requirement: Connection metadata SHALL NOT replace lane authority

Edge hello or connection metadata MAY describe transport capabilities but MUST NOT be the authority that grants, releases, or recovers a managed account lane. A reconnect or socket replacement MUST NOT silently switch the account between managed and legacy ownership.

#### Scenario: Edge reconnects during a task
- **WHEN** the routed Edge reconnects while a TaskRun owns the account lane
- **THEN** Automation SHALL preserve durable lane/run state and re-resolve transport without treating the new hello as a new task authorization

### Requirement: Phase one SHALL execute only registered read-only research capabilities

The phase-one registry SHALL admit only `persona.research@1` and its declared read-only capabilities. It MUST reject any graph containing publish, comment, reply, like, follow, join, delete, or other platform mutation.

#### Scenario: Read-only task is admitted
- **WHEN** a Task requests only the registered research capabilities within its scope
- **THEN** Automation MAY create a claimable TaskRun after all other admission checks pass

#### Scenario: Write capability is requested
- **WHEN** a Task or compiled node requests a platform mutation
- **THEN** admission SHALL fail as unsupported before lane acquisition or Edge dispatch

### Requirement: Attempts SHALL preserve dispatch and evidence truth

Automation SHALL record intent creation, dispatch acceptance, submitted/unknown, completed, empty, failed, timeout, undeliverable, aborted, and unsupported outcomes distinctly. A transport send, activity entry, lane release, or model summary MUST NOT prove a read result. Unique-read completion SHALL require stable content references and capability-specific post-evidence.

#### Scenario: Transport times out after dispatch
- **WHEN** Automation cannot prove whether Edge accepted or completed an atomic command
- **THEN** the Attempt SHALL remain submitted-unknown or enter explicit reconciliation and MUST NOT be marked completed or failed by inference

#### Scenario: Empty research result
- **WHEN** Edge proves the command completed but no eligible content was observed
- **THEN** the Attempt SHALL record empty separately from failed and the plan SHALL apply its declared empty-result edge

#### Scenario: Duplicate content observation
- **WHEN** a later step reports a content reference already counted by the same TaskRun
- **THEN** DecisionTrace SHALL record the duplicate and completion counters MUST NOT increase

### Requirement: Cancellation SHALL stop new work without erasing dispatched reconciliation

CancelTask SHALL prevent undispatched steps and intents from being claimed or sent. It SHALL NOT delete history or convert an already dispatched Attempt into cancelled; dispatched work SHALL continue receipt/reconciliation and the TaskRun SHALL expose the resulting partial or attention-required state.

#### Scenario: Cancel before dispatch
- **WHEN** cancellation commits before the next intent is dispatched
- **THEN** no later Edge command SHALL be sent and the run SHALL terminate as cancelled with preserved prior steps

#### Scenario: Cancel after dispatch
- **WHEN** an Attempt is already dispatched at cancellation time
- **THEN** Automation SHALL stop subsequent steps but continue reconciling that Attempt without inventing a platform outcome

### Requirement: Feature gates SHALL fail safe and report readiness honestly

Task entry, worker claiming, and legacy-lane exclusion SHALL be independently default-disabled. Missing schema capability, invalid target, unavailable owner port, incomplete Automation composition root, or missing Edge capability SHALL keep the affected gate closed with a named reason. Source tests alone MUST NOT be reported as production runtime, DEV deployment, or platform evidence.

#### Scenario: Worker flag enabled before root readiness
- **WHEN** the worker flag is true but its required stores, lane arbiter, connection runtime, or target are not ready
- **THEN** Automation SHALL start without the managed worker or fail its managed component explicitly and SHALL claim zero TaskRuns

#### Scenario: All source tests pass
- **WHEN** contracts, stores, worker, and loopback tests pass locally but no DEV three-process run occurred
- **THEN** delivery evidence SHALL say source-validated and MUST NOT say deployed or platform-confirmed

### Requirement: Query projections SHALL be scoped and explain honest outcomes

QueryTask SHALL return only actor-authorized task/run summaries and safe reason/trace projections. It SHALL distinguish queued, waiting-for-lane, running, cancelled, completed, partial, failed, submitted-unknown, unsupported, and attention-required states without exposing tokens, unrelated account data, raw private content, or hidden model inputs.

#### Scenario: Actor queries another account
- **WHEN** an actor lacks access to the Task account
- **THEN** QueryTask SHALL return the common not-authorized/not-found envelope without disclosing task existence

#### Scenario: Run needs reconciliation
- **WHEN** a dispatched Attempt is submitted-unknown
- **THEN** the projection SHALL show attention/reconciliation state and MUST NOT present a successful research count
