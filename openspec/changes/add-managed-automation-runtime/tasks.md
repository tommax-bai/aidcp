## 1. Freeze contracts and current-state inventory

- [ ] 1.1 Inventory current Automation-owned modules, tables, workers, locks, Edge commands, receipts, and process entrypoints in `aidcp-cloud`; map each item to one of the nine target modules or record a named exception.
- [ ] 1.2 Inventory `RoleDispatcher`, content schedules, `delegated_tasks`, publish/comment/reply state machines, EdgeTaskCoordinator, browser-slot scheduling, RiskController, and current reconcilers; record their state and failure-semantics mappings to ManagedPlan/ManagedCycle/Task/ExecutionPlan/TaskRun/StepRun/Attempt.
- [ ] 1.3 Freeze versioned schemas for CapabilityDefinition, TaskDefinition.executionGraph, Task/TaskRevision/CapabilityScope runtime projection, immutable ExecutionPlan, ManagedPlan runtime projection, ManagedCycle, TaskRun, StepRun, ExecutionIntent, ExecutionAttempt, DecisionTrace, and Trigger Binding.
- [ ] 1.4 Freeze the durable message envelope and first message set, including message/idempotency/aggregate versions, correlation/causation/trace identifiers, schema references, and trusted execution target.
- [ ] 1.5 Decide and document `personaVersion` as either an API-owned monotonic version or normalized content hash; add the required API schema/contract change and prohibit `updated_at` as a version.
- [ ] 1.6 Define the initial action-scope authorization mapping from existing `off|review|auto_approve` controls to `disabled|require_approval|standing_authorized`.
- [ ] 1.7 Define platform-specific evidence contracts for unique content reads and platform-confirmed publish/comment/reply outcomes; mark unsupported evidence paths explicitly.
- [ ] 1.8 Create separate follow-up OpenSpec deltas before changing any existing content-schedule, publish, comment, reply, delegated-task, browser-slot, client projection, or protocol behavior.

## 2. Build the durable runtime foundation

- [ ] 2.1 Add additive migrations for plan/task runtime projections, task revisions, cycles, immutable execution plans, task/step runs, trigger bindings/inbox, capability/task definitions, intents, attempts, receipts, reconciliation work, decision traces, and budget allocations/consumption — all in the automation owner database, using that database's own migration ledger, with every new table registered in the table-ownership manifest.
- [ ] 2.2 Add target-first claim/recovery indexes and `(execution_target, idempotency_key)` uniqueness where applicable; make all target values server-injected and disable workers on invalid deployment target.
- [ ] 2.3 Add legal lifecycle/CAS predicates for TaskRun, StepRun, Intent, and Attempt transitions so stale messages cannot move terminal state backward.
- [ ] 2.4 Implement typed stores with transaction boundaries, owner checks, pagination/retention hooks, and no cross-owner reads, writes, row locks, or joint commits against API/Content-owned tables; obtain every cross-owner fact through an interface implemented by the owning domain on its own connection.
- [ ] 2.5 Implement Outbox/Inbox publishing and consumption with message-version/schema validation, durable deduplication, aggregate ordering, retry/dead-letter metrics, and correlation propagation, reusing the automation domain's existing single-writer outbox plus in-process relay and internal HTTP; do not borrow another domain's outbox and do not introduce a message broker.
- [ ] 2.6 Add execution-target isolation, duplicate delivery, stale aggregate version, illegal transition, and worker-disabled acceptance tests.
- [ ] 2.7 Register every new table and module in the existing ownership/lock/split gates rather than adding a parallel gate, and prove cross-owner row locks, writes, and DML violations stay at zero as the tables are added; account-lane mutual exclusion SHALL be proven to hold only within the automation database and MUST NOT be relied on to exclude API- or Content-domain writers.

## 3. Implement Capability, TaskDefinition, Trigger, Cycle, and Task Runtime modules

- [ ] 3.1 Implement code-reviewed CapabilityDefinition and TaskDefinition registries with immutable versions, typed inputs/outputs, side-effect/evidence metadata, typed execution-graph edges, and finite bounds.
- [ ] 3.2 Implement initial Capability adapters for search-term resolution, search, feed observation/advance, content assessment/read, creation request, like, comment compose/submit, publish, reply, and return; add registered runtime nodes for waits and child-Task references.
- [ ] 3.3 Implement Plan Compiler validation for graph type compatibility, terminal paths, bounded loops, Task CapabilityScope, API authorization, platform capability, completion semantics, and immutable ExecutionPlan output; reject arbitrary scripts, unknown actions, raw Edge commands, unrestricted URLs/SQL, and dynamic imports.
- [ ] 3.4 Implement Trigger Registry allowlists, binding versions, event/schedule/manual/Agent-intent admission, idempotent creation, concurrency policies, and causal-depth protection.
- [ ] 3.5 Implement ManagedCycle creation, bounded child-Task derivation, Task budget allocation, partial summaries, and API result events.
- [ ] 3.6 Implement Task Runtime TaskRun/StepRun checkpoints, named waits, terminal outcomes, cancellation safe points, TaskRevision supersession, and restart recovery without duplicate external jobs.
- [ ] 3.7 Add tests for duplicate triggers, unknown schemas, derivation loops, latest-wins before/after dispatch, process restart, content waits, approval waits, partial completion, and truthful parent summaries.

## 4. Implement account arbitration and policy-risk admission

- [ ] 4.1 Implement authoritative AccountExecutionKey resolution from API binding snapshots/revisions and reject stale or client-derived account lanes.
- [ ] 4.2 Register Work Kind metadata for priority, browser need, schedule/deadline/miss policy, maximum wait, safe points, and resumability.
- [ ] 4.3 Implement account-lane admission, quiesce/checkpoint, safe resume, starvation evidence, and deadline handling without cross-account browser-slot eviction.
- [ ] 4.4 Establish and mechanically test the lock order account admission → machine/profile/browser lease; cover concurrent browse, comment, publish, API-only reply, reconnect, timeout, and process death.
- [ ] 4.5 Implement `skip`, `require_reapproval`, and `execute_when_available` schedule-miss behavior and add approval-retention tests for immutable work within its valid window.
- [ ] 4.6 Implement plan-time and commit-time Policy-Risk admission using API authorization revisions, runtime stop/pause, binding/page identity, capabilities, RiskController, quota, cooldown, duplicate target, content/approval revisions, and deadlines.
- [ ] 4.7 Implement independent platform-risk, execution-resource, and AI/content-cost budget allocation, reservation, consumption, release, and denial evidence.
- [ ] 4.8 Add safety tests proving standing authorization cannot bypass risk, quota, identity, version, deadline, or platform confirmation and notification failure never changes authorization.

## 5. Implement Ledger, Gateway, reconciliation, and trace

- [ ] 5.1 Implement immutable ExecutionIntent preparation and target-scoped business idempotency before any Edge/platform dispatch.
- [ ] 5.2 Implement ExecutionAttempt transitions for prepared, blocked/cancelled before dispatch, dispatched, platform-confirmed, confirmed-not-applied, and submitted-unknown.
- [ ] 5.3 Adapt Edge Gateway handshake, generation, account binding, capability snapshot, protocol version, signed command context, replay protection, routing, and receipt deduplication to Ledger identities.
- [ ] 5.4 Implement capability-specific evidence validators and prove that ack, click completion, approval, notification, or Host state alone cannot produce platform confirmation.
- [ ] 5.5 Implement bounded action-specific Reconciler adapters for supported publish/comment/reply capabilities, including unique match, proven absence, multiple-candidate ambiguity, and exhausted-window attention.
- [ ] 5.6 Enforce retry only before dispatch or after confirmed non-application; reject redispatch of submitted-unknown actions.
- [ ] 5.7 Implement forward-only cancellation and separate authorization/intents for delete or withdraw actions.
- [ ] 5.8 Implement structured Decision Trace append/query APIs and consistency checks proving Trace cannot override TaskRun/Ledger truth.
- [ ] 5.9 Run protocol-drift, replay, target-isolation, unauthorized-write, submitted-unknown, cancellation, reconciliation ambiguity, and result-event exactly-once tests.

## 6. Deliver the first read-only vertical slice

- [ ] 6.1 Publish `persona-refresh-research@1` TaskDefinition with typed `resolve search terms → search → read 10 → search → read 20 → assess → return` capability nodes and finite page/time/browser budgets.
- [ ] 6.2 Connect API `PersonaUpdated` to a versioned Trigger Binding; create the authorized Task/TaskRevision and freeze persona, plan, TaskDefinition, Capability, binding, and execution-target facts into its immutable ExecutionPlan.
- [ ] 6.3 Adapt Agent/Content search-term generation to return schema-valid candidates without direct tools or Edge commands.
- [ ] 6.4 Implement capability-specific verified unique-read counting, persistent ID checkpoints, duplicate exclusion, and actual-count partial outcomes.
- [ ] 6.5 Integrate account arbitration, Edge waiting/handshake wakeup, browser-slot acquisition, safe quiesce/resume, and return-home without changing unrelated browse-loop behavior.
- [ ] 6.6 Add restart, Edge disconnect/reconnect, persona supersession, duplicate trigger, content exhaustion, browser-budget exhaustion, unsupported platform, and 10+20 happy-path acceptance tests.
- [ ] 6.7 Run a named DEV-account probe and report source validation, deployed service version, Edge/Host state, actual unique counts, and absence of platform writes as separate evidence.

## 7. Migrate creation, comments, publish, and reply by vertical slice

- [ ] 7.1 Integrate Content creation through idempotent `CreationRequested/Completed/Failed`, external job references, frozen persona/input versions, AI budgets, and no copied candidate ownership.
- [ ] 7.2 Add/update the required publish OpenSpec deltas, then integrate approval revision, schedule window/miss policy, account admission, immutable intent, Edge dispatch, platform confirmation, and submitted-unknown reconciliation.
- [ ] 7.3 Add/update the required comment OpenSpec deltas, then implement prepare/commit account and Edge leases, stable target snapshots, resource release during composition/approval, commit-time reopen/revalidation, and honest zero-target outcomes.
- [ ] 7.4 Normalize comment standing authorization across sources while preserving visible configuration; prove best-effort notification cannot block/delay/fallback and review remains fail-closed.
- [ ] 7.5 Add/update the required reply OpenSpec deltas, then integrate inbox trigger, candidate generation, review/standing authorization, account lane, API-only/browser capability routing, Ledger, and confirmation.
- [ ] 7.6 Adapt existing single-action `delegated_tasks`, schedules, and publish/comment/reply entrypoints to create or reference Task/ExecutionPlan/TaskRun/Intent/Attempt records without turning `delegated_tasks` into a task-graph or second runtime table.
- [ ] 7.7 Add per-slice backward-compatibility, target-isolation, authorization, risk-honesty, cancellation, unknown-result, deadline, and platform-confirmation acceptance tests before enabling its Trigger Binding.
- [ ] 7.8 Perform named DEV-account probes for each platform-writing slice only after explicit test authorization; report approved, dispatched, platform-confirmed, unknown, and client-visible states separately.

## 8. Add full-managed cycles and customer projections

- [ ] 8.1 Add API customer-auth contracts for Task/TaskRevision and ManagedPlan lifecycle, per-action authorization, three budget classes, emergency stop, cycle/task/run queries, and trace summaries.
- [ ] 8.2 Add Agent Service contracts for `CreateTaskProposal`, `ReviseTaskProposal`, `CancelTaskProposal`, `QueryTaskRequest`, and matching ManagedPlan commands with schema validation, API authorization, and no direct Capability/Automation/Edge tool path.
- [ ] 8.3 Implement daily/campaign Trigger Bindings and ManagedCycle composition for bounded research, interaction, creation, publish, and reply child Tasks.
- [ ] 8.4 Implement pause/offboard behavior that freezes new work, cancels undispatched intents, preserves dispatched reconciliation, and starts owner-specific retention/deletion flows.
- [ ] 8.5 Build API projections that distinguish local Host state, durable Automation state, and platform-confirmed result; realtime events SHALL only invalidate/refetch.
- [ ] 8.6 Update Classic Client to consume the API projections and retain Edge Host lifecycle control without direct platform-action methods.
- [ ] 8.7 Defer Agent Client implementation to its own OpenSpec; verify this change adds only service/API contracts needed by a future client.
- [ ] 8.8 Add customer-facing explanations for allowed, denied, delayed, skipped, partial, superseded, submitted-unknown, and attention-required outcomes without exposing internal secrets or unrelated data.

## 9. Privacy, operations, extraction, and cutover

- [ ] 9.1 Define and implement retention/access policies for third-party snapshots, private messages, Agent/model inputs, traces, execution evidence, and logs; add deletion/offboarding tests.
- [ ] 9.2 Add metrics and alerts for trigger duplicates/loops, queue wait/starvation, missed windows, invalid CapabilityDefinitions/TaskDefinitions, stale bindings, policy denials, budget exhaustion, unsupported capabilities, unknown Attempts, reconciliation ambiguity, and target mismatch.
- [ ] 9.3 Add dashboards/runbooks that distinguish API authorization, Automation dispatch, Edge/Host transport, and platform-confirmed outcomes.
- [ ] 9.4 Run Ledger/Trace shadow mode against existing state machines, compare outcomes, and resolve every semantic mismatch before making Ledger authoritative.
- [ ] 9.5 Cut over one Capability/TaskDefinition version at a time with a kill switch that stops new TaskRuns but leaves dispatched Attempts available for receipt/reconciliation.
- [ ] 9.6 After single-writer and contract gates pass, extract the nine modules into the independent `aidcp-automation` repository without cross-repository source imports or shared-file authorization/locks.
- [ ] 9.7 Create separate build, typecheck, focused/full safety tests, migration, DEV deployment, rollback, and version-reporting pipelines for `aidcp-automation`.
- [ ] 9.8 Re-run Cloud/Automation/API/Content/Edge contract, protocol, risk, unauthorized-publish, target-isolation, data-plane separation, and end-to-end acceptance suites after extraction.

## 10. Final validation and closeout

- [ ] 10.1 Verify all five capability specs have automated acceptance coverage and every implementation deviation is recorded with repo, commit, validation, deployment, and rollback evidence.
- [ ] 10.2 Verify no arbitrary TaskDefinition scripting, first-class Workflow/CapabilityRun runtime, direct Agent/Client→Capability/Edge action path, second risk-state writer, cross-service business-table write, hidden authorization gate, or optimistic platform success was introduced.
- [ ] 10.3 Validate protocol documentation and both endpoint implementations for every new capability/message version; prove unknown capability/version fails honestly.
- [ ] 10.4 Validate clean DEV deployment, health, listeners, workers, shared-DB target isolation, dashboards, customer projections, and bounded rollback before any OL release proposal.
- [ ] 10.5 Run `openspec validate add-managed-automation-runtime --strict`, update task evidence, and archive only after all required implementation and truthful live-validation boundaries are complete.
