## ADDED Requirements

### Requirement: Capabilities MUST be atomic, typed, and versioned domain contracts

Automation SHALL execute only registered `CapabilityDefinition` versions with validated input/output schemas, declared side-effect class, finite bounds, and capability-specific evidence requirements. A Capability MAY encapsulate the platform operations needed to satisfy one domain contract, but it MUST NOT choose or invoke an unrelated next Capability.

#### Scenario: Content assessment completes
- **WHEN** `content.assess` evaluates a stable content snapshot
- **THEN** it SHALL return a schema-valid value/confidence/reasons result and MUST NOT return a raw Edge command or an instruction to like, comment, or publish

#### Scenario: Unknown capability is requested
- **WHEN** a TaskDefinition references an unpublished Capability/version
- **THEN** publication or Plan compilation MUST fail with a named contract reason before executable work is created

### Requirement: TaskDefinitions MUST express typed and bounded capability relationships

A `TaskDefinition` SHALL contain an immutable versioned `executionGraph` whose nodes reference registered Capabilities or registered runtime control nodes and whose edges use typed conditions. The graph MUST declare maximum nodes, loop iterations, derivation depth, attempts, and wall-clock duration. It MUST NOT contain arbitrary code, dynamic imports, unrestricted HTTP/SQL, raw Edge command names, or unbounded loops.

#### Scenario: Registered task type starts
- **WHEN** a schema-valid Task references a published TaskDefinition version
- **THEN** Plan Compiler SHALL validate all node schemas, edges, terminal paths, bounds, and Capability versions before creating an ExecutionPlan

#### Scenario: Task graph contains an arbitrary expression
- **WHEN** a TaskDefinition contains executable code or a condition outside the registered typed-condition allowlist
- **THEN** publication or Plan compilation MUST fail with `task_definition_invalid`

### Requirement: Task capability scope MUST constrain rather than define execution flow

Each Task SHALL carry a `CapabilityScope` with explicit allowed and denied capabilities. The executable capability set MUST be the intersection of ExecutionPlan nodes, Task scope, API authorization, current platform/Edge capabilities, and live policy/risk/quota/budget admission. Task parameters and graph conditions MAY decide when an allowed capability is selected; the scope alone MUST NOT imply that it will execute.

#### Scenario: Browse and like without commenting
- **WHEN** a research Task allows browse, assess, read, and like while denying comment submission
- **THEN** Plan Compiler MAY enable the conditional like node but MUST remove or reject every comment-submit path

#### Scenario: Every eligible item should be liked
- **WHEN** the Task sets `likeStrategy=always_if_eligible`
- **THEN** each eligible graph branch MAY request like admission, while current risk, quota, identity, duplicate-target, and capability gates MAY still skip individual likes honestly

### Requirement: Agent task commands MUST use consistent verb-object semantics

Agent Service SHALL translate natural language into one of `CreateTaskProposal`, `ReviseTaskProposal`, `CancelTaskProposal`, `QueryTaskRequest`, `CreateManagedPlanProposal`, `ReviseManagedPlanProposal`, or `CancelManagedPlanProposal`. API SHALL authenticate and authorize all state changes. `TaskPatch` and `PlanPatch` MUST NOT be first-class domain commands; an accepted task change SHALL create an immutable `TaskRevision`.

#### Scenario: User narrows a running task
- **WHEN** the user says “接下来不要点赞，只浏览”
- **THEN** Agent SHALL propose `ReviseTask`, API SHALL record a new TaskRevision, and Automation SHALL switch only at a safe point without rewriting prior Attempts

#### Scenario: User asks for an explanation
- **WHEN** the user asks why no content was liked
- **THEN** the system SHALL process a `QueryTaskRequest` against TaskRun, Decision Trace, and Ledger projections and MUST NOT create executable work

#### Scenario: User expands from draft to submission
- **WHEN** a prior Task explicitly produced comment drafts without submit permission and the user later asks to send them
- **THEN** the system SHALL create a separately authorized submit Task referencing the draft results rather than mutating the draft Task to hide a new external side effect

### Requirement: ExecutionPlans MUST be immutable compiled artifacts

Plan Compiler SHALL combine exact Capability versions, a TaskDefinition execution graph, a TaskRevision with CapabilityScope/constraints/completion, and an API authorization revision into one immutable `ExecutionPlan`. Every TaskRun SHALL reference exactly one TaskRevision and ExecutionPlan. A single-action Task SHALL use a one-node ExecutionPlan; a multi-node Task SHALL use the same TaskRun model and MUST NOT require a separate `CapabilityRun` or `WorkflowRun` type.

#### Scenario: Task is revised before dispatch
- **WHEN** an authorized TaskRevision replaces a TaskRun that has no irreversible dispatched Attempt
- **THEN** Automation SHALL compile a new ExecutionPlan and create/supersede the TaskRun without modifying the old plan

#### Scenario: Task is revised after dispatch
- **WHEN** an older TaskRun already has a dispatched external write
- **THEN** that Attempt SHALL continue receipt/reconciliation under the old TaskRun while the new revision receives a separate ExecutionPlan and TaskRun

### Requirement: Task progress and waits MUST be durable and orthogonal

TaskRun and StepRun lifecycle SHALL distinguish `queued`, `running`, `waiting`, `cancel_requested`, and `terminal`; a waiting item MUST carry a named wait reason, and a terminal item MUST carry an honest terminal outcome. Task Runtime SHALL persist checkpoints sufficient to resume after process or Edge reconnect without replaying confirmed work.

#### Scenario: Edge disconnects between nodes
- **WHEN** a TaskRun reaches an Edge-dependent node while no valid Core connection exists
- **THEN** it SHALL persist `waiting_for_edge`, retain confirmed progress, and resume only after a new authoritative handshake and admission

#### Scenario: Process restarts during content wait
- **WHEN** Automation restarts while a StepRun waits for a referenced Content creation job
- **THEN** Task Runtime SHALL reconstruct the wait from durable state and MUST NOT create a duplicate creation job

### Requirement: Cross-service task nodes MUST exchange typed references

Cross-service nodes SHALL use durable commands/events or narrow internal APIs and save external object references. Automation MUST NOT copy or become the writer of Content candidates/assets, API approvals, personas, or account master data.

#### Scenario: Creation is requested
- **WHEN** a creation-request Capability is admitted
- **THEN** it SHALL emit one idempotent `CreationRequested`, persist its job/correlation reference, and enter `waiting_for_content`

#### Scenario: Content creation fails
- **WHEN** Content returns terminal failure for the referenced creation job
- **THEN** the dependent StepRun SHALL fail or skip according to TaskDefinition and MUST NOT synthesize an empty candidate for publication

#### Scenario: Approval is required
- **WHEN** an external-write node has `require_approval` authorization
- **THEN** it SHALL wait for an API-owned approval matching the frozen content, target, TaskRevision, and authorization revision

### Requirement: Research counts MUST use verified unique content facts

A content-read node with a count target SHALL count only unique stable content IDs for which the platform capability's required read evidence was confirmed. Rendering a card, seeing a duplicate, reconnecting, or scrolling past content MUST NOT increment the count. Confirmed IDs and counts SHALL be checkpointed durably.

#### Scenario: Ten plus twenty research sequence completes
- **WHEN** an ExecutionPlan performs one search and verifies 10 unique reads, then performs a second search and verifies 20 additional unique reads
- **THEN** Task Runtime SHALL advance each StepRun only at its verified target and report the actual 30 unique results

#### Scenario: Content supply is exhausted
- **WHEN** a read StepRun reaches its page/time budget after verifying 13 of 20 requested items
- **THEN** it SHALL report actual count 13 and the TaskRun SHALL use the honest partial/skipped outcome defined by TaskDefinition

#### Scenario: Edge reconnects during browsing
- **WHEN** Edge reconnects after 7 verified items
- **THEN** the StepRun SHALL resume from the durable unique-ID set and MUST NOT recount the first 7 items

### Requirement: Parent outcomes and cancellation MUST preserve child truth

A parent TaskRun or ManagedCycle SHALL derive its summary from child StepRun/TaskRun outcomes without converting skipped, failed, cancelled, or `submitted_unknown` work into success. After a valid cancellation request, Task Runtime SHALL stop creating new work at the next declared safe point. A dispatched Attempt MUST remain linked to receipt/reconciliation, and its real outcome MUST override any assumption that cancellation undid the platform action.

#### Scenario: Research succeeds and creation fails
- **WHEN** a cycle completes research but its creation Task fails
- **THEN** the cycle SHALL report a partial outcome with separate research and creation results

#### Scenario: Waiting research is cancelled
- **WHEN** a TaskRun waiting for Edge has no dispatched external write and receives authorized cancellation
- **THEN** it SHALL terminate as cancelled without later dispatch

#### Scenario: Publish is cancelled after dispatch
- **WHEN** cancellation arrives after a publish Attempt was dispatched
- **THEN** Task Runtime SHALL retain cancellation requested, continue reconciliation, and MUST NOT rewrite the Attempt as not submitted

### Requirement: High-frequency session events MUST remain distinct from durable task checkpoints

Task Runtime MAY use an in-process EventBus for high-frequency per-card browse-loop events, but it SHALL durably persist TaskRun/StepRun checkpoints, verified progress, cross-service commands/events, external Attempts, and every fact required for recovery. An in-process event MUST NOT be the only carrier of customer authorization, external-write intent, or terminal platform result.

#### Scenario: Automation crashes during a browse session
- **WHEN** volatile per-card events are lost
- **THEN** the TaskRun SHALL recover from its last durable checkpoint and confirmed unique-content facts without inventing completion

#### Scenario: Approval crosses a service boundary
- **WHEN** API records an approval decision
- **THEN** authorization SHALL reach Task Runtime through a durable contract rather than an in-process event or shared local file
