## ADDED Requirements

### Requirement: Automation definitions MUST be typed, bounded, and versioned

Workflow Runtime SHALL execute only registered Automation Definitions with immutable versions, validated input/output schemas, allowed trigger types, required action scopes/capabilities, and explicit maximum steps, derivation depth, execution attempts, and wall-clock duration. Definitions MUST use registered step types and MUST NOT contain arbitrary code, dynamic imports, unrestricted HTTP/SQL, raw Edge command names, or unbounded loops.

#### Scenario: Registered definition starts
- **WHEN** Trigger Registry requests a Run for a published Definition version with schema-valid input
- **THEN** Workflow Runtime SHALL create the Run and its initial typed Step using that exact immutable Definition version

#### Scenario: Definition contains an arbitrary script step
- **WHEN** a Definition contains a step type or executable expression outside the registered allowlist
- **THEN** publication or Run creation MUST fail with `definition_invalid` before any work is admitted

### Requirement: Workflow progress and waits MUST be durable and orthogonal

Run and Step lifecycle SHALL distinguish `queued`, `running`, `waiting`, `cancel_requested`, and `terminal`; a waiting item MUST carry a named wait reason, and a terminal item MUST carry an honest terminal outcome. Workflow Runtime SHALL persist checkpoints sufficient to resume after process or Edge reconnect without replaying confirmed work.

#### Scenario: Edge disconnects between steps
- **WHEN** a Run reaches an Edge-dependent step while no valid Core connection exists
- **THEN** the Run SHALL persist `waiting` with `waiting_for_edge`, retain its confirmed progress, and resume only after a new authoritative handshake and admission

#### Scenario: Process restarts during content wait
- **WHEN** Automation restarts while a Step is waiting for a referenced Content creation job
- **THEN** Workflow Runtime SHALL reconstruct the wait from durable state and MUST NOT create a duplicate creation job

### Requirement: Workflow steps MUST exchange typed references across service boundaries

The initial step registry SHALL support `resolve_search_terms`, `search`, `browse`, `assess`, `request_creation`, `await_creation`, `await_approval`, `interact`, `publish`, `reply`, `wait_until`, and `return_home`. Cross-service steps MUST use durable commands/events or narrow internal APIs and save external object references; Automation MUST NOT copy or become the writer of Content candidates/assets, API approvals, personas, or account master data.

#### Scenario: Creation is requested
- **WHEN** a `request_creation` Step is admitted
- **THEN** it SHALL emit one idempotent `CreationRequested`, persist the returned/job correlation reference, and transition to `waiting_for_content`

#### Scenario: Content creation fails
- **WHEN** Content returns a terminal failure for the referenced creation job
- **THEN** the dependent Step SHALL fail or skip according to the Definition and MUST NOT synthesize an empty candidate for publication

#### Scenario: Approval is required
- **WHEN** a write Step has `require_approval` authorization
- **THEN** it SHALL wait for an API-owned approval decision matching the frozen content, target, and authorization revisions

### Requirement: Research counts MUST use verified unique content facts

A `browse` Step with a content-count target SHALL count only unique stable content IDs for which the platform capability's required read evidence was confirmed. Merely rendering a card, seeing a duplicate, reconnecting, or scrolling past content MUST NOT increment the count. Confirmed IDs and counts SHALL be checkpointed durably.

#### Scenario: Ten plus twenty research sequence completes
- **WHEN** a Definition performs one search and verifies 10 unique reads, then performs a second search and verifies 20 additional unique reads
- **THEN** Workflow Runtime SHALL advance each Step only at its own verified target and report the actual 30 unique results

#### Scenario: Content supply is exhausted
- **WHEN** a browse Step reaches its bounded page/time budget after verifying 13 of 20 requested items
- **THEN** the Step SHALL report actual count 13 and the Run SHALL use an honest partial/skipped outcome defined by the Definition

#### Scenario: Edge reconnects during browsing
- **WHEN** Edge reconnects after 7 verified items
- **THEN** the Step SHALL resume from the durable unique-ID set and MUST NOT recount the first 7 items

### Requirement: Workflow termination MUST preserve child truth

A parent Run or ManagedCycle SHALL derive its summary from child Step/Run outcomes without converting skipped, failed, cancelled, or `submitted_unknown` work into success. Independent child work MAY continue only when the Definition explicitly permits it and its inputs remain valid.

#### Scenario: Research succeeds and creation fails
- **WHEN** a cycle completes research but its creation job fails
- **THEN** the cycle SHALL report a partial outcome with separate research and creation results, not a full success

#### Scenario: Publish remains unknown
- **WHEN** a publish Step ends with an unresolved `submitted_unknown` Attempt
- **THEN** its parent MUST surface pending/unknown attention and MUST NOT claim that content was published

### Requirement: Cancellation MUST be forward-only and safe-point aware

Workflow Runtime SHALL stop creating new work after a valid cancellation request. A queued or waiting Step without dispatched external action MAY terminate as cancelled at a safe point. A Step with a dispatched Attempt MUST remain linked to receipt/reconciliation and its real outcome MUST override any assumption that cancellation undid the platform action.

#### Scenario: Waiting research Run is cancelled
- **WHEN** a Run waiting for Edge has no dispatched external write and receives an authorized cancellation
- **THEN** it SHALL terminate as cancelled without later dispatch

#### Scenario: Publish is cancelled after dispatch
- **WHEN** cancellation arrives after a publish Attempt was dispatched
- **THEN** Workflow Runtime SHALL mark cancellation requested, continue result reconciliation, and MUST NOT rewrite the Attempt as not submitted

### Requirement: High-frequency session events MUST remain distinct from durable workflow checkpoints

Workflow Runtime MAY use an in-process EventBus for high-frequency per-card browse-loop events, but it SHALL durably persist Run/Step checkpoints, unique verified progress, cross-service commands/events, external Attempts, and all facts required for recovery. An in-process event MUST NOT be the only carrier of customer authorization, external-write intent, or terminal platform result.

#### Scenario: Automation process crashes during a browse session
- **WHEN** volatile per-card events are lost in a process crash
- **THEN** the Run SHALL recover from the last durable checkpoint and confirmed unique-content facts without inventing completion

#### Scenario: Approval crosses service boundary
- **WHEN** API records an approval decision
- **THEN** the authorization SHALL reach Workflow Runtime through a durable contract rather than an in-process event or shared local file
