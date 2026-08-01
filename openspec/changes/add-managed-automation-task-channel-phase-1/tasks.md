## 1. Reconcile the current architecture and old assets

- [ ] 1.1 Record the current `split-cloud-automation-production-runtime` dependency, Automation composition-root hotspots, branch/worktree baselines, and the exact gate that must close before production wiring.
- [ ] 1.2 Inventory every managed-automation file and commit on the old `aidcp-cloud` feature branch; classify each as port unchanged, adapt to the independent process, replace, or drop, with a named reason.
- [ ] 1.3 Inventory legacy per-account scheduling/dispatch entrypoints and in-flight evidence in `aidcp-automation`; define the complete lane-read and legacy-in-flight adapter surface before changing behavior.
- [ ] 1.4 Freeze the phase-one owner map, current Automation migration ledger maximum, table manifest changes, cross-process DTO locations, and default-disabled rollout flags.

## 2. Freeze phase-one contracts and registries

- [ ] 2.1 Port and narrow the Task, TaskRevision, CapabilityScope, ExecutionPlan, TaskRun, StepRun, Intent, Attempt, DecisionTrace, reason-code, and action-classification contracts into their final owner/shared locations; exclude ManagedPlan/Cycle/Trigger contracts.
- [ ] 2.2 Add canonical serialization, payload hash, version parsing, target validation, terminal-state guards, and customer-safe projection helpers with unit tests.
- [ ] 2.3 Add versioned CreateTask, CancelTask, QueryTask, receipt, and error DTOs to the approved kernel/transport boundary without business execution code.
- [ ] 2.4 Register and validate only `persona.research@1` and its bounded search→browse→assess→summarize read-only graph; prove every mutation capability is rejected.
- [ ] 2.5 Add contract drift tests across API/Automation transport endpoints and prove unknown versions/capabilities fail honestly.

## 3. Add Automation-owned persistence

- [ ] 3.1 Add target-scoped migrations for task authority, task revisions, immutable plans, task runs, and account lane state using the current Automation migration ledger.
- [ ] 3.2 Add target-scoped migrations for step runs, intents, attempts, command receipts, and decision traces; register every table in Automation ownership manifests.
- [ ] 3.3 Port/adapt typed stores with capability probes, target filters, CAS transitions, bounded leases, stable command dedupe, collision detection, and terminal regression protection.
- [ ] 3.4 Add account-lane store operations for managed acquisition, legacy observation, renewal, safe release, expired-lease recovery, and kill-switch retention.
- [ ] 3.5 Add store unit tests and PostgreSQL integration tests for concurrent claim, duplicate/collision, lease takeover, terminal races, target isolation, and lane release with unknown Attempts.
- [ ] 3.6 Update schema contract and migration-order/owner gates without making a default-disabled feature look production-ready when its runtime dependency is absent.

## 4. Build the API-to-Automation task port

- [ ] 4.1 Implement Automation-owned CreateTask, CancelTask, and QueryTask services with authorization revision, account scope, registry, compiler, store, and readiness checks.
- [ ] 4.2 Implement authenticated, versioned, target-bound Automation routes and transport clients with stable result-unknown behavior.
- [ ] 4.3 Implement the API owner adapter that authorizes actor/account access and calls the Automation port without constructing Automation stores or calling Edge.
- [ ] 4.4 Add command idempotency, collision, cancellation-before/after-dispatch, cross-account query privacy, malformed response, timeout, and disabled-route tests.
- [ ] 4.5 Add safe task/run/reason/trace query projections that exclude secrets, raw private content, hidden model inputs, and unrelated account data.

## 5. Build the bounded execution runtime

- [ ] 5.1 Port/adapt the immutable linear PlanCompiler and StepExecutor contracts; add deterministic plan-hash and bounds tests.
- [ ] 5.2 Implement the account lane arbiter over durable lane state plus a complete legacy-in-flight adapter; do not infer availability from socket mode.
- [ ] 5.3 Implement TaskRunWorker claim, renew, step checkpoint, cancellation, retry, expiry recovery, terminalization, and graceful shutdown behavior behind a default-off gate.
- [ ] 5.4 Implement `ResearchStepExecutor` for the four registered read-only steps with stable content-reference evidence, dedupe, bounded re-drive, and distinct empty/failed/unknown outcomes.
- [ ] 5.5 Implement the Automation connection-runtime dispatch adapter using existing account/edge targeting and atomic command receipts; reject unsupported platform/capability combinations.
- [ ] 5.6 Add unit and vertical-slice tests for waiting-for-lane, cross-account independence, reconnect, timeout-after-dispatch, empty result, duplicate evidence, cancellation, recovery, and kill switch.

## 6. Wire production roots without reviving a second runtime

- [ ] 6.1 Rebase after `split-cloud-automation-production-runtime` closes its Automation main/readiness hotspots and confirm no other session is writing the same composition-root files.
- [ ] 6.2 Wire managed task routes, stores, registry, lane arbiter, worker, executor, and shutdown into the independent Automation root with separate default-off entry/worker/lane flags.
- [ ] 6.3 Wire the API client/authorization adapter into the independent API root; keep customer UI and direct Agent tool exposure out of scope.
- [ ] 6.4 Make every identified legacy scheduling/dispatch entrypoint consult the shared account-lane adapter and emit `managed_task_lane_active` without changing disabled-path behavior.
- [ ] 6.5 Add readiness, metrics, logs, and health detail for disabled, schema-missing, target-invalid, port-unavailable, lane-waiting, claim, recovery, unknown Attempt, and shutdown states.
- [ ] 6.6 Add loopback API→Automation and Automation→connection-runtime tests proving Create→Compile→Run→Trace→Query and proving no legacy fallback or direct Edge path exists.

## 7. Validate, integrate, and prove boundaries

- [ ] 7.1 Run focused contract/store/port/runtime/lane tests and typecheck in every owning repository; record exact counts and gated tests.
- [ ] 7.2 Run owner-boundary, protocol/transport drift, target-isolation, risk honesty, unauthorized-action, acceptance, and full suites in every affected repository.
- [ ] 7.3 Run PostgreSQL CAS/claim/lease/target/lane integration against an isolated DEV-capable database and record rollback-safe schema evidence.
- [ ] 7.4 Rebase and serially integrate affected repositories using fast-forward-only history; update repo/commit/test evidence without force-push.
- [ ] 7.5 Deploy only to named DEV after `scripts/deploy-target dev --check`; verify independent API/Automation/Content health, listeners, worker readiness, disabled default, and rollback. Do not deploy OL.
- [ ] 7.6 Enable the read-only slice only after all gates pass; run a named DEV task probe and distinguish Automation receipt, Edge dispatch, read evidence, and platform observation.
- [ ] 7.7 Update handoff and task evidence, run `openspec validate add-managed-automation-task-channel-phase-1 --strict`, and archive only after all required implementation and live-validation boundaries are complete.
