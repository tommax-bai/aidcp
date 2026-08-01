# Phase-one current-state inventory

Snapshot: 2026-08-01 +0800. Refresh the commands and SHAs before implementation or integration; this file records the admission decision, not an immutable deployment fact.

## 1. Active dependency and repository baselines

| Scope | Ref at inventory time | Relationship / disposition |
| --- | --- | --- |
| control canonical | `main@4efec64f` | `origin/main`; contains the user's route-A decision for split-runtime business configuration ownership |
| this control worktree | `codex/add-managed-automation-task-channel-phase-1@4efec64f` | rebased to `origin/main`; this active change is the only authority for phase one |
| Automation canonical | `master@ac09a7f` | `origin/master`; split-runtime batch E-1 landed |
| Automation split worktree | `codex/split-cloud-automation-production-runtime@ac09a7f` | equal to `origin/master`, ahead 27 of its stale same-name remote feature ref; remains the composition-root writer |
| Cloud canonical | `master@534af192` | `origin/master`; legacy monolith and split source baseline |
| old Cloud managed-runtime worktree | `codex/add-managed-automation-runtime@4a921dc7` | ahead 11 / behind 0 versus `origin/master`; equal to its remote feature ref; **port source only, never merge wholesale** |
| old control managed-runtime worktree | `codex/add-managed-automation-runtime@bbb62cd9` | orphan because the old change moved to `docs/design`; local history is ahead 4 / behind 3 versus current main and has rewritten divergence from its remote feature ref; not authoritative and must not be pushed as reactivation |

Refresh commands:

```bash
./scripts/task-preflight
git fetch origin
git status --short --branch
git -C ../aidcp-automation fetch origin
git -C ../aidcp-automation rev-list --left-right --count master...origin/master
git -C ../aidcp-cloud.wt/add-managed-automation-runtime fetch origin
git -C ../aidcp-cloud.wt/add-managed-automation-runtime rev-list --left-right --count HEAD...origin/master
openspec instructions apply --change split-cloud-automation-production-runtime --json
jq '.summary' ../aidcp-automation/boundaries/composition-root-independent-blockers.json
```

### Production-wiring dependency

Live OpenSpec status was `76/129`. The Automation readiness ledger contained 11 blockers: three operator-command, seven content-owner, and one composition-root blocker named `automation-production-runtime-composition-unwired`.

The earlier E-2 ownership decision is no longer waiting for user input: control commit `4efec64f` selected route A, extracting pure decision logic to kernel. Implementation is still pending. Batches E-2, G, and H, task 3.1's real `main()`, task 4.1's three-ledger contraction, and their tests remain incomplete.

Phase-one task modules may be implemented away from shared composition-root files, but tasks 6.1–6.6 MUST NOT start until all of these are true:

1. `split-cloud-automation-production-runtime` has landed its E-2/G/H implementation and real Automation `main()` on `origin/master`.
2. `automation-production-runtime-composition-unwired` is absent and the independent-root blocker ledger total is zero (not merely “11 dependencies are constructible”).
3. `runAutomationEntry()` no longer stops at `AutomationRootNotReadyError`, and Automation typecheck/acceptance prove the root is bootable with missing dependencies still failing by name.
4. The split change's worktree is clean/integrated and no concurrent session owns `automation-composition-root.ts`, `automation-service-entry.ts`, connection-runtime factories, role registration, protocol mapping, or risk-state hotspots.

Until then the allowed claim is “additive source modules/tests”; production runtime, deployment, and platform evidence are blocked.

## 2. Old Cloud branch commit disposition

The branch contains 11 commits, 63 changed files, 9,310 insertions, and 8 deletions relative to current Cloud master.

| Commit | Old delivery | Phase-one disposition |
| --- | --- | --- |
| `1b1e590` | contracts and old-state mapping | selectively port/narrow pure contracts; do not port plan/session-mode authority |
| `6ab3a8a` | four migrations and typed stores | adapt into Automation owner ledger; add lane and command receipts; recheck numbering |
| `791c2d1` | linear compiler/worker | adapt to durable account lane, independent shutdown/readiness, and current store ports |
| `19d5445` | hello session mode and task-mode exclusion | replace with durable account lane; do not port protocol/connection-mode behavior |
| `89e203c` | Create/Cancel/Query plus monolith root wiring | split service into Automation owner and API caller; discard monolith root patch |
| `0afda67` | entry/HTTP tests | adapt to API→Automation route/client and result-unknown contract |
| `696ca1e` | `persona.research@1` registry | port and narrow to read-only phase-one registry |
| `afe243e` | research executor and Edge port | adapt to Automation connection runtime and stable read evidence |
| `ae2d484` | account binding and root wiring | retain admission idea; replace root implementation and connection-mode assumption |
| `bfe373c` | E2E and boundary entries | adapt tests/manifests to independent repos and account lane |
| `4a921dc` | disabled API log severity | drop with the monolith API startup path |

### File-by-file classification

Legend: **PORT** = semantic file can be copied then import-formatted; **ADAPT** = useful implementation but contract/owner/process changes are required; **REPLACE** = old behavior is superseded by the account-lane or independent-root design; **DROP** = outside phase one or tied only to the discarded path.

#### Ownership, migrations, and schema

| File | Class | Named reason |
| --- | --- | --- |
| `boundaries/module-ownership.json` | ADAPT | register modules in Automation/API repos, not monolith-only ownership |
| `boundaries/ownership-rules.json` | ADAPT | retain single-writer rules and update repo paths |
| `boundaries/table-ownership.json` | ADAPT | register Automation tables in current manifest |
| `scripts/db-split/owner-tables.automation.txt` | ADAPT | current Automation owner list is the target |
| `migrations/0106_managed_automation_task_authority.sql` | ADAPT | retain task/plan tables; add command receipt and current manifest evidence |
| `migrations/0107_managed_automation_run_state.sql` | ADAPT | retain run/step tables and add durable account lane |
| `migrations/0108_managed_automation_execution_ledger.sql` | ADAPT | retain intent/attempt ledger after state review |
| `migrations/0109_managed_automation_decision_traces.sql` | ADAPT | retain traces after privacy/retention review |
| `src/schema/schema-contract.ts` | ADAPT | Automation derived schema contract is authoritative |
| `test/schema/sync-read-checkpoint-migration.test.ts` | REPLACE | add current migration-order/owner tests instead of editing an unrelated historical checkpoint test |

#### Contracts

| File | Class | Named reason |
| --- | --- | --- |
| `src/managed-automation/contracts/common.ts` | PORT | pure ids, versions, target and timestamp types remain useful |
| `src/managed-automation/contracts/reason-codes.ts` | PORT | phase-one reason vocabulary remains useful after completeness review |
| `src/managed-automation/contracts/action-classification.ts` | PORT | read/write classification is required to reject writes |
| `src/managed-automation/contracts/task.ts` | ADAPT | narrow to phase-one task/revision/scope and add actor/authorization fields |
| `src/managed-automation/contracts/task-run.ts` | ADAPT | add waiting-for-lane/attention states and current recovery rules |
| `src/managed-automation/contracts/execution-plan.ts` | ADAPT | keep immutable plan but enforce phase-one linear bounds/hash |
| `src/managed-automation/contracts/execution-attempt.ts` | ADAPT | align submitted-unknown and read-only re-drive evidence |
| `src/managed-automation/contracts/decision-trace.ts` | ADAPT | add customer-safe projection and retention boundary |
| `src/managed-automation/contracts/capability.ts` | ADAPT | registry must reject all phase-one write capabilities |
| `src/managed-automation/contracts/agent-intents.ts` | REPLACE | new API→Automation DTO/port owns external command shape |
| `src/managed-automation/contracts/index.ts` | ADAPT | export only phase-one contracts |
| `src/managed-automation/contracts/STATE-MAPPING.md` | DROP | old global supersession mapping is no longer authoritative; relevant state decisions live in this change |
| `src/managed-automation/contracts/plan.ts` | DROP | ManagedPlan/Cycle/Trigger Binding are explicitly out of scope |
| `src/managed-automation/contracts/session-mode.ts` | DROP | connection mode is not lane authority |

#### Engine, execution, registry, service, and stores

| File | Class | Named reason |
| --- | --- | --- |
| `src/managed-automation/engine/linear-graph.ts` | PORT | bounded linear graph primitive matches phase one |
| `src/managed-automation/engine/plan-compiler.ts` | ADAPT | enforce narrowed registry, canonical hash, authorization revision, and bounds |
| `src/managed-automation/engine/ports.ts` | ADAPT | ports must include lane and current Automation dependencies |
| `src/managed-automation/engine/step-executor.ts` | ADAPT | align cancellation/unknown evidence boundaries |
| `src/managed-automation/engine/task-run-worker.ts` | ADAPT | add lane, renewal, recovery, shutdown and split-root readiness |
| `src/managed-automation/engine/index.ts` | ADAPT | export the adapted engine only |
| `src/managed-automation/execution/edge-dispatch-port.ts` | ADAPT | bind to current connection runtime and receipt types |
| `src/managed-automation/execution/comm-edge-dispatch-adapter.ts` | ADAPT | replace monolith Comm imports with Automation targeting |
| `src/managed-automation/execution/research-step-executor.ts` | ADAPT | require stable content reference, dedupe, and bounded re-drive |
| `src/managed-automation/execution/index.ts` | ADAPT | export adapted execution files |
| `src/managed-automation/registry/persona-research.ts` | ADAPT | retain only the registered read-only graph and exact versions |
| `src/managed-automation/registry/index.ts` | ADAPT | reject every unregistered/write capability |
| `src/managed-automation/service/task-entry-service.ts` | ADAPT | Automation owner service needs command receipt/readiness/account authorization inputs |
| `src/managed-automation/service/index.ts` | ADAPT | export Automation service, not monolith composition helpers |
| `src/managed-automation/stores/store-base.ts` | ADAPT | use current Automation pool/schema capability and target injection |
| `src/managed-automation/stores/task-authority-store.ts` | ADAPT | add command dedupe/collision and new owner types |
| `src/managed-automation/stores/run-state-store.ts` | ADAPT | add lane-aware states and safe recovery |
| `src/managed-automation/stores/execution-ledger-store.ts` | ADAPT | preserve CAS/terminal truth and current Attempt contract |
| `src/managed-automation/stores/decision-trace-store.ts` | ADAPT | add projection/retention boundaries |
| `src/managed-automation/stores/index.ts` | ADAPT | include lane store and adapted stores |
| `src/managed-automation/task-mode-exclusion.ts` | REPLACE | durable account lane replaces session-mode filtering |
| `src/transport/managed-automation-http.ts` | REPLACE | split into kernel DTO/port plus transport route/client and owner adapters |

#### Existing production files touched by the old branch

| File | Class | Named reason |
| --- | --- | --- |
| `src/comm/handler.ts` | REPLACE | remove hello mode behavior; managed tasks reuse normal admitted transport |
| `src/comm/protocol.ts` | DROP | phase one adds no connection mode or new Edge message type |
| `src/comm/ws-server.ts` | REPLACE | use account lane and current Automation connection registry |
| `src/orchestrator/connection-runtime.ts` | REPLACE | lane arbitration lives above durable account state, not connection selection |
| `src/server.ts` | DROP | monolith composition wiring is the wrong production owner |

#### Tests

| File | Class | Named reason |
| --- | --- | --- |
| `test/managed-automation/engine-fakes.ts` | ADAPT | add lane and split-process ports |
| `test/managed-automation/engine-plan-compiler.test.ts` | PORT | retain deterministic bounded graph cases and extend hash/version checks |
| `test/managed-automation/engine-worker.test.ts` | ADAPT | add lane/recovery/shutdown/kill-switch cases |
| `test/managed-automation/entry-fakes.ts` | ADAPT | model owner-safe port and readiness |
| `test/managed-automation/entry-service.test.ts` | ADAPT | add auth revision, dedupe/collision, privacy and unknown results |
| `test/managed-automation/research-slice-e2e.test.ts` | ADAPT | run through Automation lane and connection runtime, not test-only assembly |
| `test/managed-automation/stores-unit.test.ts` | ADAPT | include command receipt and lane transitions |
| `test/managed-automation/stores-pg.integration.test.ts` | ADAPT | include current migrations, lane and Automation target isolation |
| `test/transport/managed-automation-http.test.ts` | REPLACE | verify API→Automation route/client/adapter split |
| `test/comm/ws-server-task-mode.test.ts` | DROP | no task-mode connection behavior |
| `test/handler-session-mode.test.ts` | DROP | no session-mode parsing |
| `test/integration/connection-runtime-task-mode.test.ts` | REPLACE | account-lane legacy exclusion integration test |

## 3. Legacy account-work inventory and lane adapter surface

### Producers and dispatch points

| Source | Current dispatch/claim boundary | In-flight evidence that lane acquisition must inspect | Required lane hook |
| --- | --- | --- | --- |
| per-connection browsing/interactions: `RoleDispatcher` | `startSession`/resume plus the single `sendCommand()` wrapper | `sessionActive`, comment subline/pending interaction state, Edge task lease, pending Facebook consumption action | deny new legacy session/resume while managed-owned; re-read lane in `sendCommand()` so a mid-session transition cannot leak a command |
| comment scheduler: `CommentScheduler` | `triggerForMode`, `triggerManual`, `triggerTargeted` before per-account single-flight | `isRunning(accountId)`, comment approval/in-flight step, Edge task lease and durable audit/consumption state | check before single-flight admission and again immediately before irreversible/atomic Edge dispatch |
| Facebook group join: `FacebookGroupJoinScheduler` | `triggerScheduled`, `triggerForMode`, `joinSpecificGroup`, before-dispatch callback | `isRunning(accountId)`, claimed membership/action and Edge lease | check before claim and at the existing before-dispatch callback |
| Facebook consumption coordinator | `trigger` plus durable `claimAction`/`bindTargetAndMarkDispatched` | in-memory `isRunning`, runtime rows with owner lease and `dispatch_phase` | managed acquisition treats active/unknown rows as busy; legacy trigger checks lane before claim and dispatch CAS |
| publish dispatch: `PublishDispatcher` and trigger receiver | `dispatch`, `scanAndDispatchApproved` | `getInFlightRecordIds`, approval dispatch revision, sequencer/in-flight account chain | check before scan claim/trigger and again before Edge handoff; dispatched/unknown blocks managed lane release |
| publish schedule/reconcile | `PublishScheduler.checkAndMaybeTrigger`/manual/scheduled/delegated and `ScheduledPublishReconciler.tick` | `PublishScheduler.isBusy`, due records, publish dispatcher in-flight/approval state | check before taking scheduled/delegated work and before handing to dispatcher |
| delegated tasks | `DelegatedTaskWorker.tick` → `claimNext` → executor | target-scoped claim lease, current attempt, progress and terminal evidence | managed lane acquisition sees active claim/attempt as busy; worker checks lane before claim and executor handoff |
| content schedule and remaining batch-G schedulers | not yet wired into independent Automation root | API-owned schedule claim plus any Automation executor state | batch G MUST expose the same `LegacyAccountWorkPort`; absence is `unknown`, never clear |

Risk/accounting reconcilers, offboard reconcilers, alert workers, mirror refreshers, and receipt-only reconciliation do not themselves drive the browser and therefore do not acquire the account lane. They MAY continue while managed-owned. A reconciler that can re-dispatch an Edge command must be reclassified as a producer and added above before task 1.3 evidence is accepted.

### Frozen adapter shape

The lane arbiter consumes one complete adapter instead of importing every legacy class:

```ts
type LegacyWorkSource =
  | 'role_dispatcher'
  | 'edge_task_lease'
  | 'comment_scheduler'
  | 'facebook_group_join'
  | 'facebook_consumption'
  | 'publish_dispatch'
  | 'publish_schedule'
  | 'delegated_task'
  | 'content_schedule';

type LegacyAccountWorkSnapshot =
  | { kind: 'clear'; checkedAt: string }
  | { kind: 'busy'; checkedAt: string; sources: LegacyWorkSource[]; evidenceRefs: string[] }
  | { kind: 'unknown'; checkedAt: string; source: LegacyWorkSource; reason: string };

interface LegacyAccountWorkPort {
  snapshot(accountId: string): Promise<LegacyAccountWorkSnapshot>;
}
```

`unknown` has the safety polarity **deny managed acquisition**. The snapshot is admission evidence only; lane acquisition MUST re-check it inside the owner operation/CAS window or use an equivalent reservation handshake so “clear then legacy claim” cannot race. Every producer also reads lane immediately before its own claim/dispatch. One-sided checking is insufficient.

## 4. Frozen owner, migration, DTO, and flag map

### Owners

| Object / behavior | Owner |
| --- | --- |
| Task/Revision/Plan/Run/Step/Intent/Attempt/Trace/command receipt/account lane | `aidcp-automation` database and service |
| actor/customer/account authorization and customer-facing projection entry | `aidcp-api` |
| shared pure DTO/port/error discriminants | `aidcp-kernel` |
| internal HTTP envelope, route/client codecs | `aidcp-transport` |
| platform atomic command execution and page evidence | `aidcp-edge` |
| legacy monolith branch | port source and compatibility reference only; not a production owner |

### Migration allocation

The shared Cloud ledger currently reaches `0105_facebook_primary_browse_surface`; the derived Automation checkout contains only Automation-owned migrations through `0102_facebook_consumption_runtime`. The next globally valid allocation is therefore 0106–0109, subject to a fresh check immediately before creation:

| Version | Tables |
| --- | --- |
| `0106_managed_task_authority` | `tasks`, `task_revisions`, `execution_plans`, `managed_task_command_receipts` |
| `0107_managed_task_run_state` | `task_runs`, `step_runs`, `managed_account_work_lanes` |
| `0108_managed_task_execution_ledger` | `execution_intents`, `execution_attempts` |
| `0109_managed_task_decision_traces` | `decision_traces` |

All tables are Automation-owned, include `execution_target`, have no cross-owner foreign keys, and must be added to `boundaries/table-ownership.json` plus the Automation owner table list. If another migration takes any number before implementation, renumber before first deployment; never reuse a ledger id.

### DTO placement

- kernel: request/receipt/projection/error discriminated unions and `ManagedTaskCommandPort`/query port interfaces only.
- transport: canonical envelope validation, route constants, server route factory and HTTP client.
- Automation: owner service, stores, compiler, route adapter, worker, lane and executor.
- API: actor/account authorization adapter and later customer/Agent route; no Automation store or Edge dependency.

### Default-off flags

| Flag | Default | Meaning |
| --- | --- | --- |
| `AIDCP_MANAGED_TASK_API_ENABLED` | false | register authenticated internal query/cancel/create routes; disabling still permits no new external calls |
| `AIDCP_MANAGED_TASK_CREATE_ENABLED` | false | admit new Task creation; cancel/query can remain available for drain/inspection |
| `AIDCP_MANAGED_TASK_WORKER_ENABLED` | false | claim new TaskRuns and steps |
| `AIDCP_MANAGED_TASK_LANE_ENABLED` | false | activate managed lane acquisition and legacy exclusion |

Only exact lowercase `true` enables a flag. Enabling worker while lane, schema, target, stores, connection runtime, or independent-root readiness is absent yields a named disabled/not-ready result and zero claims. Kill switch order is create off → worker off → preserve lane for dispatched reconciliation; API query/cancel may remain on.
