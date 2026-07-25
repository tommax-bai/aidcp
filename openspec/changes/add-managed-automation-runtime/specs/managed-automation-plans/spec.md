## ADDED Requirements

### Requirement: Managed plans MUST separate proposal, authorization, and runtime ownership

An Agent Service MAY produce a structured `CreateManagedPlanProposal`, `ReviseManagedPlanProposal`, or `CancelManagedPlanProposal`, but the API SHALL authenticate the customer, persist the customer-visible `ManagedPlan`/revision, record its action authorization revision, and publish a durable activation/update/pause/cancel event. Automation SHALL own only the runtime projection and MUST NOT treat an Agent proposal, client payload, natural-language message, or Edge report as plan authorization.

#### Scenario: Agent proposal is activated through API
- **WHEN** an Agent produces a valid plan proposal and an authorized customer accepts it through the API
- **THEN** the API persists a versioned ManagedPlan and Automation creates or updates its runtime projection from the durable API event

#### Scenario: Agent attempts direct execution
- **WHEN** an Agent or client sends an unapproved plan directly to Automation or Edge
- **THEN** the system MUST reject it without creating executable work or platform commands

### Requirement: Managed automation MUST use bounded lifecycle layers

The system SHALL represent a long-lived goal as `ManagedPlan`, a day/campaign window as `ManagedCycle`, one concrete bounded goal as `Task`, execution of one TaskRevision/ExecutionPlan as `TaskRun`, a recoverable capability-node execution as `StepRun`, and one real platform attempt as `ExecutionAttempt`. A ManagedCycle, Task, ExecutionPlan, and TaskRun MUST have finite wall-clock, node, attempt, and budget bounds; the system MUST NOT represent continuous account operation as one unbounded TaskRun.

#### Scenario: Daily full-managed operation starts
- **WHEN** an active plan reaches the start of a configured operating day
- **THEN** Automation creates a bounded ManagedCycle that references the frozen plan version and derives bounded child Tasks under the plan's authorized TaskDefinitions and budgets

#### Scenario: Cycle reaches a configured bound
- **WHEN** a cycle exhausts its wall-clock or allocated budget while some child work remains
- **THEN** the cycle SHALL terminate with an honest complete, partial, skipped, or failed summary and MUST NOT silently continue as an unbounded run

### Requirement: Trigger bindings MUST be explicit, versioned, and causally bounded

Trigger Registry SHALL accept only registered event, schedule, manual, or API-authorized Agent-intent types. Each binding MUST name an exact TaskDefinition version, input schema, scope key, idempotency derivation, concurrency policy, and maximum derivation depth. Durable trigger messages MUST carry `messageId`, `correlationId`, `causationId`, `aggregateVersion`, and server-injected `executionTarget`.

#### Scenario: Persona update matches a registered binding
- **WHEN** API emits a supported `PersonaUpdated` version for an active plan
- **THEN** Trigger Registry SHALL create at most one TaskRun for the binding's account, persona version, and TaskDefinition version scope

#### Scenario: Unknown event reaches Trigger Registry
- **WHEN** an event type or schema version has no registered binding
- **THEN** Trigger Registry MUST reject or dead-letter it with an observable contract reason and MUST NOT ask an Agent to invent an execution graph

#### Scenario: Derived events exceed the bound
- **WHEN** processing an event would create a causal chain deeper than the binding's maximum derivation depth
- **THEN** the system SHALL stop derivation, record a decision trace, and MUST NOT create another Task or TaskRun

### Requirement: Concurrent triggers MUST follow a declared supersession policy

Each binding SHALL declare `ignore_if_running`, `queue`, or `latest_wins`. `latest_wins` MAY supersede an older TaskRun only while the older TaskRun has no irreversible dispatched Attempt. A TaskRun with a dispatched external write MUST remain independently observable and reconcile to its real result.

#### Scenario: Latest persona version arrives before dispatch
- **WHEN** a `latest_wins` research TaskRun for persona v7 is waiting without a dispatched external write and persona v8 arrives
- **THEN** Automation SHALL mark the v7 TaskRun superseded and create a new TaskRun frozen to persona v8

#### Scenario: New plan version arrives after publish dispatch
- **WHEN** a publish Attempt from plan v4 is already dispatched and plan v5 becomes active
- **THEN** the v4 Attempt MUST continue receipt/reconciliation independently and MUST NOT be overwritten or represented as cancelled by plan v5

### Requirement: TaskRuns MUST freeze business intent while honoring live safety controls

At TaskRun creation, Automation SHALL compile an immutable ExecutionPlan that freezes the TaskRevision, ManagedPlan/TaskDefinition/persona versions, Capability versions, account/environment/platform/target binding revision, content and approval revisions, target/text/media/schedule/visibility fields, idempotency key, and allocated budgets. A business update SHALL create a new TaskRevision, ExecutionPlan, and TaskRun according to policy rather than mutate an in-flight plan. Emergency stop, account pause, binding validity, authorization revocation, capability, risk, quota, cooldown, target existence, and deadline SHALL be re-read before irreversible dispatch.

#### Scenario: Candidate changes after approval
- **WHEN** the current candidate version no longer matches the TaskRun's frozen content and approval revisions
- **THEN** Automation MUST deny dispatch and require a new authorized TaskRun or approval revision

#### Scenario: Account is paused after TaskRun creation
- **WHEN** a frozen TaskRun reaches an irreversible step after the account has been paused
- **THEN** live safety admission SHALL prevent dispatch even though the original plan version remains valid

### Requirement: Durable automation work MUST be isolated by trusted deployment target

Every ManagedCycle, Task runtime projection, ExecutionPlan, TaskRun, StepRun, Attempt, trigger inbox/outbox record, claim, scan, recovery, and idempotency uniqueness scope SHALL include a server-injected `execution_target=dev|ol`. Missing or invalid local deployment target configuration MUST disable workers that claim or recover durable automation work. The target MUST NOT be accepted from a client, Agent, Edge report, natural language, or inferred from `envKey`.

#### Scenario: DEV and OL contain equal business keys
- **WHEN** shared PostgreSQL contains TaskRuns with the same account and idempotency key under DEV and OL
- **THEN** each worker SHALL claim, read, update, and recover only rows for its own trusted target

#### Scenario: Worker has no valid deployment target
- **WHEN** an Automation worker starts without a valid `AIDCP_DEPLOY_ENV`
- **THEN** durable scanners and claimers MUST remain disabled and emit an explicit operator-visible failure
