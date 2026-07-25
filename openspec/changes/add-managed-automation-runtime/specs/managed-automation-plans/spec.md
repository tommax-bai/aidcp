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

### Requirement: Autonomous work MUST respect an account operating window

A ManagedPlan SHALL carry an account-level operating-window calendar (day-of-week × hour) that applies across plans, cycles, and trigger sources. Outside the window Automation MUST NOT start or resume a ManagedCycle, Task, or TaskRun, and work already running SHALL terminate at its next declared safe point rather than merely being barred from restarting. A write/content action window SHALL be a subset of the account's operating window, and an action-level window MAY only narrow it. A missing or invalid window definition MUST be treated as "no autonomous work" and MUST NOT inherit a fail-open default from another mask. The window SHALL be enforced server-side independently of any client or editor guarantee, and when the window reopens Automation SHALL proactively re-admit eligible work rather than wait for an external event.

#### Scenario: Cycle crosses into a closed hour
- **WHEN** a running ManagedCycle reaches an hour outside the account's operating window
- **THEN** it SHALL stop at its next safe point with an honest window-closed outcome rather than continuing to its own wall-clock bound

#### Scenario: Window mask is missing
- **WHEN** an account has no valid operating-window definition
- **THEN** no autonomous cycle SHALL be created for it, and the absence MUST NOT be resolved by reusing another mask's fail-open default

#### Scenario: Window reopens
- **WHEN** the operating window reopens for an account with eligible deferred work
- **THEN** Automation SHALL re-admit that work proactively and MUST NOT depend on an Edge reconnect or an unrelated event to wake it

### Requirement: Cycle cadence MUST be rested and de-synchronized

Consecutive automated cycles for the same account SHALL be separated by a configured rest interval with randomized variance, and Automation MUST NOT start a new cycle immediately upon the previous cycle's terminal outcome. A schedule trigger binding SHALL apply a deterministic per-scope dispatch offset derived from account, local date, and action so that work for different accounts under the same binding is not created at the same instant. The offset MUST be reproducible without stored state, and neither the rest interval nor the offset may be removed as a side effect of introducing account-level or global concurrency control.

#### Scenario: Cycle ends normally
- **WHEN** a ManagedCycle terminates and the plan remains active
- **THEN** the next cycle SHALL start no earlier than the configured rest interval with variance applied, and MUST NOT be created back-to-back

#### Scenario: Many accounts share one daily binding
- **WHEN** fifty accounts are bound to the same daily schedule trigger
- **THEN** their TaskRuns SHALL be created at deterministically staggered offsets within the window rather than at the same instant

### Requirement: Each work scope MUST have exactly one trigger owner

For each `(account, action, schedule window)` there SHALL be exactly one trigger owner at any time. When a Trigger Registry binding is enabled for a scope, every legacy trigger for the same scope MUST be deterministically disabled at startup, and a legacy path MUST NOT be retained as a fallback. Cutover state MUST be observable per account and action. Idempotency derivation for a given `(account, action family)` SHALL be shared across trigger sources so that two different bindings or a binding and a legacy scheduler cannot each produce one execution of the same work.

#### Scenario: New and legacy triggers coexist during migration
- **WHEN** a Trigger Binding is enabled for an account's daily publish while the legacy publish scheduler is still deployed
- **THEN** the legacy trigger for that account and action MUST be disabled at startup and the cutover state MUST be observable, because a concurrency gate only prevents same-instant execution and cannot prevent two triggers firing minutes apart

#### Scenario: Two sources target the same action family
- **WHEN** a delegated task and a scheduled binding both derive work for the same account and action family
- **THEN** they SHALL resolve to the same idempotency scope so that at most one execution is created

### Requirement: Automation writers MUST be single-instance per execution target

For each `execution_target`, the Automation component that owns risk state and quota admission SHALL run as exactly one instance, enforced by acquiring a database-level session-scoped mutual-exclusion handle keyed by the target before enabling any risk or quota write path. Failure to acquire within a bounded wait MUST alert and exit non-zero; loss of the holding connection MUST stop dispatching new interaction commands and MUST NOT continue writing. Deployment of this component MUST be stop-then-start; rolling or blue-green rollout MUST NOT be used.

#### Scenario: Second writer starts on the same target
- **WHEN** a second process attempts to enable the risk/quota write path for a target already held
- **THEN** it MUST fail to acquire the handle, alert, and exit non-zero rather than proceed unlocked

#### Scenario: Writer loses its lock mid-run
- **WHEN** the holding database connection drops
- **THEN** the process MUST stop dispatching new interaction commands and surface the loss rather than continue on stale authority

### Requirement: Background modules MUST be classified before separate deployment

Every Automation worker or background module that owns mutable runtime state SHALL be classified as single-instance or multi-instance and recorded before it is deployed as a separate process; an unclassified module MUST be operated as single-instance. Multi-instance classification SHALL require a durable claim token, a claim lease with expiry, skip-locked claim selection, execution-target filtering on create/claim/recover/terminal writes, and claim recovery at process start. A durable claim without lease expiry or takeover semantics MUST NOT be introduced, because a crashed owner would pin its scope permanently.

#### Scenario: Reconciler is scaled out
- **WHEN** the Reconciler is proposed as an independently scaled worker group
- **THEN** it MUST first be classified multi-instance and satisfy the claim token, lease expiry, skip-locked selection, target filtering, and startup recovery requirements

#### Scenario: Claim holder crashes
- **WHEN** a worker holding a durable single-flight claim dies
- **THEN** the claim SHALL expire or be taken over so the scope becomes re-triggerable, and MUST NOT remain pinned until manual intervention
