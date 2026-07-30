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

Cross-service nodes SHALL use durable commands/events or narrow internal APIs and save external object references. Automation MUST NOT copy or become the writer of Content candidates/assets, API approvals, personas, or account master data, and MUST NOT obtain them by connecting to another domain's database; every cross-owner read SHALL go through an interface implemented by the owning domain on its own connection. Because no transaction may span two owner databases, any API- or Content-owned fact frozen into an ExecutionPlan is a read snapshot and MUST be revalidated before irreversible dispatch rather than treated as transactionally held.

#### Scenario: Frozen approval and candidate are checked before dispatch
- **WHEN** a StepRun is about to dispatch an external write whose ExecutionPlan froze an API-owned approval revision and a Content-owned candidate version
- **THEN** it SHALL re-read both through their owning domains' interfaces and MUST NOT satisfy the check by querying the API or Content database directly

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

### Requirement: Runs MUST terminate as submitted-unknown while a dispatched Attempt is unsettled

A TaskRun that reaches its deadline, budget bound, or cancellation point while any dispatched Attempt has no authoritative platform outcome SHALL terminate with `submitted_unknown` and SHALL remain linked to that unsettled Attempt. It MUST NOT adopt an earlier Attempt's failure reason as the run outcome, MUST NOT be recorded as a clean failure, and MUST NOT redispatch the irreversible action. Customer-visible results for such a run SHALL be derived from the current Ledger outcome rather than the snapshot taken at termination, and parent TaskRun/ManagedCycle summaries SHALL reference the Ledger rather than freeze an unknown child as succeeded or failed.

#### Scenario: Deadline arrives with a dispatched publish outstanding
- **WHEN** a TaskRun reaches its deadline or budget bound while a publish Attempt is dispatched without an authoritative result, and an earlier Attempt had failed for a benign reason
- **THEN** the TaskRun SHALL terminate as `submitted_unknown`, MUST NOT render the earlier failure as the run outcome, and MUST NOT retry the publish

#### Scenario: Reconciler settles after the run terminated
- **WHEN** Reconciler later confirms or disproves the platform write for a terminated `submitted_unknown` TaskRun
- **THEN** the customer-visible result and its parent cycle summary SHALL follow the updated Ledger outcome while the TaskRun's own terminal record remains unchanged

### Requirement: High-frequency session events MUST remain distinct from durable task checkpoints

Task Runtime MAY use an in-process EventBus for high-frequency per-card browse-loop events, but it SHALL durably persist TaskRun/StepRun checkpoints, verified progress, cross-service commands/events, external Attempts, and every fact required for recovery. An in-process event MUST NOT be the only carrier of customer authorization, external-write intent, or terminal platform result.

#### Scenario: Automation crashes during a browse session
- **WHEN** volatile per-card events are lost
- **THEN** the TaskRun SHALL recover from its last durable checkpoint and confirmed unique-content facts without inventing completion

#### Scenario: Approval crosses a service boundary
- **WHEN** API records an approval decision
- **THEN** authorization SHALL reach Task Runtime through a durable contract rather than an in-process event or shared local file

### Requirement: Observations MUST be honest about context, absence, and convergence

Capability outputs SHALL distinguish `not_observed` (the observation itself failed: locator miss, extractor gap, unreachable surface, unverified context) from `observed_absent` (the platform genuinely has no such content or the action legitimately had no effect). Downstream nodes, counts, and assessments MUST NOT treat `not_observed` as an observed negative, and sustained `not_observed` on a published capability MUST be observable as capability degradation rather than as ordinary content outcomes. A read/observe capability MUST declare and verify its context preconditions — that the executor is on the intended surface, and that any requested sort/filter actually took effect — at the moment results are harvested; unverified context MUST produce an honest failure instead of results. Reported platform facts MUST be observed values only: a field the platform did not expose MUST be reported absent and MUST NOT be substituted, derived, or inferred from another field. Where a node's goal is expressed as an external target state, convergence SHALL be judged by re-observing that state; declared loop bounds are backstops and MUST NOT be used as the completion condition.

#### Scenario: Extractor stops matching after a platform layout change
- **WHEN** the body-text extractor returns nothing because its selectors no longer match
- **THEN** the result SHALL be `not_observed` and MUST NOT be recorded as "the content has no body", and the repeated occurrence SHALL surface as capability degradation

#### Scenario: Search navigation is unverified
- **WHEN** a search step cannot prove it reached the results surface for this search term
- **THEN** it MUST fail honestly and MUST NOT report the currently displayed cards as its results

#### Scenario: Sweep target is expressed as a platform state
- **WHEN** a node's goal is "no unread items remain"
- **THEN** it SHALL re-read the unread state after each pass and continue while any remain, stopping at its bound with a recorded reason rather than declaring completion after a fixed number of passes

### Requirement: Nested deadlines MUST be monotonic and cancellation MUST propagate

Nested execution deadlines MUST be monotonic: an outer wait budget SHALL be greater than or equal to the sum of the inner budgets it wraps on the critical path plus round-trip margin, and an inner executor's total bounded window SHALL be strictly less than the caller's wait budget, so the executor's honest terminal reason arrives before the orchestrator gives up. Any admission or acceptance timeout SHALL likewise exceed the counterparty's declared bounded completion deadline plus margin and SHALL cover only total silence, never conditions that have their own immediate negative receipt. When an outer layer stops waiting it MUST propagate cancellation into the inner call rather than abandoning an in-flight request. Each such deadline SHALL have exactly one source of truth, and injection sites MUST NOT hard-code a fallback that differs from the declared default. A dedicated wait budget MUST NOT be shared with probes that run inside per-round retry loops, and enlarging an executor window MUST trigger re-reckoning of every enclosing deadline.

#### Scenario: Executor window exceeds the orchestrator deadline
- **WHEN** a comment submit capability's humanized typing plus post-submit confirmation window is longer than the StepRun's wait budget
- **THEN** the configuration MUST be rejected as contract-invalid, because cutting the executor short converts a knowable outcome into `submitted_unknown`

#### Scenario: Outer layer gives up
- **WHEN** a node's wall-clock bound expires while a model or child job call is in flight
- **THEN** cancellation SHALL be propagated to that call and MUST NOT leave it running to its own default timeout

### Requirement: Preparatory steps MUST be classified and verified before irreversible dispatch

Every preparatory StepRun that precedes an irreversible dispatch MUST declare a post-condition verified from observed state — a necessary signal alone MUST NOT be accepted as sufficient — and MUST be classified as `required` or `best_effort`. Failure of any `required` step SHALL abort the sequence before the irreversible step, and the failure context MUST enumerate every `best_effort` step that was skipped. A verification whose evidence would be destroyed by the irreversible step itself MUST be performed before that step rather than after.

#### Scenario: Media attachment cannot be verified
- **WHEN** the file-input control reports a populated value that is not corroborated by observed editor state
- **THEN** the step MUST NOT be treated as satisfied, and the sequence MUST abort before submission rather than submit a degraded result

#### Scenario: A best-effort step is skipped
- **WHEN** an optional metadata step fails and the sequence continues
- **THEN** the eventual outcome context MUST list that step as skipped so a partially degraded result is never indistinguishable from a complete one

### Requirement: Waits MUST be bounded, honest, and separately accounted

A TaskRun/StepRun SHALL account for named waits separately from its working-time budget: time spent in a declared wait MUST NOT consume the work budget, and MUST remain subject to an independent stall/liveness bound that a wait MUST NOT suspend. A wait SHALL terminate immediately with its true reason as soon as its precondition is known to be unsatisfiable (executor gone, target destroyed, referenced job failed) and MUST NOT continue until its deadline; a timeout or budget-exhaustion outcome MUST NOT be reported when a more specific terminal cause was already known. A budget or deadline that expires while execution is inside a declared non-interruptible unit SHALL be deferred to that unit's next safe point rather than terminating it mid-way. A declared non-interruptible unit MUST be one of the windows the safe-point requirement recognises as able to refuse preemption; a read excursion carrying no such declaration is safe at every point, and an expiring bound SHALL terminate it at once with a zero-side-effect honest receipt. Stall handling SHALL distinguish a recovery nudge that does not end the run from a give-up that reclaims it.

#### Scenario: Executor disappears during a wait
- **WHEN** the connection or resource a wait depends on is known to be gone
- **THEN** the wait MUST end at once with that cause rather than run to its deadline and be reported as a timeout

#### Scenario: Deadline lands inside a non-interruptible unit
- **WHEN** a wall-clock bound expires while an inspection excursion is mid-way
- **THEN** termination SHALL be deferred to that unit's next safe point instead of severing it

### Requirement: Resumed runs MUST be re-driven

When a TaskRun resumes from a wait or is reactivated, Task Runtime SHALL re-issue the command needed to drive the executor loop rather than only marking the run active. A run in `running` status MUST be backed by either an in-flight dispatched command or a named wait; a run that is neither MUST be detected and surfaced as a stall rather than presented as progressing. Liveness of a driven loop MUST NOT depend on the executor spontaneously re-reporting.

#### Scenario: Run resumes after Edge handshake
- **WHEN** a `waiting_for_edge` TaskRun is admitted again after a new authoritative handshake
- **THEN** Task Runtime SHALL re-issue the driving command, and MUST NOT set the run to `running` with nothing in flight

### Requirement: Terminal state MUST be exactly once and MUST NOT be reopened by late work

Terminal transition handling for a TaskRun, StepRun, or ManagedCycle SHALL be idempotent and its side effects SHALL execute exactly once per terminal event; a repeated invocation for the same terminal MUST NOT cancel, revoke, or supersede follow-on work already scheduled by the first invocation. Once a run reaches a terminal outcome, late results from work that was still in flight MUST be discarded at every persistence and outbound-delivery point and MUST NOT create a second outcome, durable artifact, or notification for the same trigger. After any executor interruption (connection loss, control-plane recovery, process restart), an in-flight capability invocation **that has not yet dispatched a platform write** SHALL be discarded and reported honestly as failed — including for capabilities whose side-effect class is `none` or `reversible`. An invocation that had already dispatched an irreversible platform command MUST instead be retained as `submitted_unknown` under the Ledger's uncertainty contract and routed to reconciliation, and MUST NOT be reported as failed or discarded. Reconciliation settling such an Attempt is not "late in-flight work": it SHALL update the Ledger and the projections derived from it, while MUST NOT rewriting the run's own terminal record or reactivating the run. Resumption MUST re-observe current platform state rather than replay the interrupted invocation or reuse coordinates, handles, or snapshots captured before the interruption.

#### Scenario: Terminal handler runs twice
- **WHEN** a cycle's terminal handler is invoked a second time for the same terminal event
- **THEN** it MUST NOT cancel the next cycle already armed by the first invocation

#### Scenario: Timed-out generation returns late
- **WHEN** a generation round already reported as failed returns a result afterwards
- **THEN** that result MUST be discarded before persistence and before any approval card is emitted

### Requirement: Task scope MUST bound targets as well as capabilities

A Task SHALL carry an explicit target scope (which containers, surfaces, or relationship sets its actions may touch) alongside its CapabilityScope, and admission MUST reject any target outside it. When the eligible target set is empty, the TaskRun MUST terminate with an honest no-target outcome and MUST NOT widen its scope, surface, or search space to obtain one. Once a TaskRun has committed to a concrete target, a failure at any later node MUST terminate that run honestly against that target: it MUST NOT re-select or substitute another target within the same run, and a completion count MUST NOT be satisfied by a target other than the one committed to. A denied capability MUST be expressible as a runtime skip that still executes the preceding selection, composition, and validation nodes and produces auditable output without recording cooldown, risk, de-duplication, or success, in addition to being expressible as compile-time removal.

#### Scenario: No qualified target exists
- **WHEN** a comment Task finds no candidate meeting its relevance and target-scope constraints
- **THEN** it SHALL report zero with a no-qualified-target reason and MUST NOT broaden its search space or relax its constraints to produce one

#### Scenario: Approval is rejected after target commitment
- **WHEN** a human rejects the drafted comment for the committed target
- **THEN** the run SHALL terminate honestly and MUST NOT select a different target to satisfy the same count

#### Scenario: Rehearsal before enabling an unattended write
- **WHEN** a Task denies the submit capability for rehearsal
- **THEN** it SHALL still run target selection, composition, and validators and emit auditable output, while recording no cooldown, risk, de-duplication, or success fact

### Requirement: Content production outcomes MUST be evidenced and MUST NOT be substituted

When a required content component of an external write cannot be produced or is rejected (composition abstained, empty, over-length, plagiarised, or a mandatory payload such as a contact block is unavailable), the StepRun MUST terminate with an honest skip. It MUST NOT substitute template, placeholder, previously used, or auto-corrected text, and MUST NOT dispatch a degraded variant whose business meaning differs from the authorized action. A non-platform production goal SHALL count a unit as produced only when its artifact is durably persisted and readable back.

#### Scenario: Composition abstains for a mandatory comment
- **WHEN** a rule marks a comment mandatory and composition abstains or fails validation within its bounds
- **THEN** the run MUST skip honestly and MUST NOT satisfy the mandatory rule with template text

#### Scenario: Model returned text but nothing was persisted
- **WHEN** a Task asked for three candidates and the model returned text for all three but none was durably stored
- **THEN** the produced count SHALL be zero

### Requirement: Execution timing MUST have declared floors, spread, and monotone slowing

Capability execution timing SHALL declare a non-zero lower bound as well as an upper bound. Configuration MAY only slow execution and MUST NOT reduce any interval below its built-in floor, enforced both at the authoritative read path and at the executor. Sampled intervals SHALL be distributed rather than pinned at the floor. Pacing factors derived from risk state or quota tier SHALL be monotonically slowing — a more permissive tier MUST NOT speed execution up — and a tier change SHALL propagate to in-flight work, not only at the next dispatch. A missing timing parameter MUST fall back to a non-zero default and MUST NOT fall back to zero. Any probabilistic or randomized branching SHALL be a bounded declared parameter of the compiled ExecutionPlan with an injectable random source and its draw recorded in the Decision Trace; a model or Agent output MUST NOT be relied on to produce randomness or frequency.

#### Scenario: Pacing parameters are absent
- **WHEN** a dispatched command carries no think/dwell values
- **THEN** the executor SHALL apply non-zero defaults and MUST NOT leave a content page with zero delay

#### Scenario: Risk tier changes mid-run
- **WHEN** an account moves to a more restricted tier while a TaskRun is executing
- **THEN** the slower pacing SHALL apply to the remainder of that run rather than only to subsequently created work
