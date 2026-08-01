# Phase-one managed automation task channel handoff

Updated: 2026-08-01 (Asia/Shanghai)

## 1. Start here

This is the active implementation change:

- Change: `add-managed-automation-task-channel-phase-1`
- Progress: **26/39 tasks (67%)**
- Control branch: `codex/add-managed-automation-task-channel-phase-1`
- Control worktree: `/Users/baitianxing/codes/aidcp.wt/add-managed-automation-task-channel-phase-1`
- Automation worktree: `/Users/baitianxing/codes/aidcp-automation.wt/add-managed-automation-task-channel-phase-1`
- Kernel worktree: `/Users/baitianxing/codes/aidcp-kernel.wt/add-managed-automation-task-channel-phase-1`
- Transport worktree: `/Users/baitianxing/codes/aidcp-transport.wt/add-managed-automation-task-channel-phase-1`
- API worktree: `/Users/baitianxing/codes/aidcp-api.wt/add-managed-automation-task-channel-phase-1`

At the start of a new session:

```bash
cd /Users/baitianxing/codes/aidcp
./scripts/task-preflight
cd /Users/baitianxing/codes/aidcp.wt/add-managed-automation-task-channel-phase-1
openspec list
openspec validate add-managed-automation-task-channel-phase-1 --strict
git status --short
```

Then read, in order:

1. `proposal.md`
2. `design.md`
3. `tasks.md`
4. `references/current-state-inventory.md`
5. this file

Use the `openspec-apply-change` workflow. Do not revive or apply the withdrawn design under
`docs/design/managed-automation-runtime/` as an active change.

## 2. Product and architecture decision

Phase one builds the single task channel, not a parallel runtime:

```text
manual request now ─┐
                    ├─> Task -> immutable ExecutionPlan -> Run/Ledger/Trace -> Edge evidence
future scheduler ───┘
```

The future scheduler is only another Task producer. It does not get a second execution engine.
Phase one accepts only `persona.research@1`, a bounded read-only
search -> browse -> assess -> summarize graph. ManagedPlan/Cycle/Trigger, platform writes,
customer UI, production enablement, and OL are out of scope.

Runtime ownership is final-state ownership:

- `aidcp-api`: actor authentication, customer/account authorization, customer-safe adapter.
- `aidcp-automation`: Task/Revision/Plan/Run/Step/Intent/Attempt/Trace/lane single writer and worker.
- `aidcp-kernel` or `aidcp-transport`: versioned cross-process DTOs only.
- Edge: atomic browser command execution and evidence, never task orchestration authority.

## 3. Current baselines and merge status

The branches were refreshed on 2026-08-01. Control was reconciled through `origin/main@0d283679`;
the remote default later advanced to `ebd11a5e`, so this published docs branch is now three commits
behind and intentionally remains unintegrated. Kernel already absorbed the two E-2 commits on its
published feature branch. Automation remains intentionally two commits behind its default until the
task 6.1 production-root gate closes.

| Repo | Default baseline | Feature head at handoff | Default behind feature | Feature behind default |
|---|---|---|---:|---:|
| `aidcp` | `origin/main@ebd11a5e` | handoff commit on this branch | 15 commits | 3, deferred until the gated integration refresh |
| `aidcp-automation` | `origin/master@ed2d32b1` | `77ea3af2` | 15 commits | 2, intentionally deferred to task 6.1 |
| `aidcp-kernel` | `origin/master@9cfd1c98` | `2fe845ba` | 2 commits | 0 |
| `aidcp-transport` | `origin/master@a2ffe054` | `e031d6a5` | 2 commits | 0 |
| `aidcp-api` | `origin/master@8c0ba78b` | `354dcc4` | 2 commits | 0 |

Do **not** merge the phase-one branches into defaults yet. The production roots and legacy-side lane
checks are not wired, and guarded PostgreSQL integration has not run.
Before eventual integration, fetch/rebase each repo again, rerun the required suites, and use
fast-forward-only history.

The old Qoder Cloud branch remains source material only:

- Worktree: `/Users/baitianxing/codes/aidcp-cloud.wt/add-managed-automation-runtime`
- Head: `4a921dc7`
- It must not be merged wholesale: it wires the runtime into the old Cloud monolith.
- All 11 commits and 63 changed files have dispositions in `references/current-state-inventory.md`.

## 4. Delivered work

### Control/OpenSpec

- New active proposal/design/spec/task set with strict validation.
- Exact owner/process/migration/flag decisions.
- Old-branch and legacy-producer inventory.
- Current progress evidence in `tasks.md`.

### Kernel (contract commit `34d1b94`, branch head `2fe845b`)

- Versioned Create/Cancel/Query DTOs and `ManagedTaskCommandPort`.
- Actor, target, result, collision, unknown-result, and customer projection contracts.
- DTO/port only; no business execution code.
- The feature branch now ends at `2fe845b`, a merge of current `origin/master@9cfd1c9` into the
  already-pushed DTO commit. Kernel full tests are **73/73** and typecheck passes.

### Transport (`e031d6a`)

- Exact closed JSON validators for Create/Cancel/Query envelopes and responses.
- Authenticated `internal/managed-task/v1/*` Automation route registration and API HTTP client.
- Deterministic auth/disabled-route/protocol/target rejection remains distinct from ambiguous
  timeout, disconnect, handler error, or malformed write response.
- Ambiguous Create/Cancel returns `result_unknown` once with the original command id and no retry.
- The HTTP boundary transparently re-exports the exact managed-task DTO/port types carried by its
  kernel dependency; API therefore consumes one transport contract instead of defining a copy.

### API (`19956bd`, branch head `354dcc4`)

- API-owned adapter accepts only already-authenticated actor context, re-checks the live customer
  enablement plus forward/reverse environment-account scope, and validates the exact account platform.
- It injects contract version and server-selected target, creates canonical Create/Cancel payload
  hashes, and calls only `ManagedTaskCommandPort`; it imports no Automation stores and has no Edge or
  legacy delegated-task fallback.
- Account denial stops before the Automation call. Cross-account Query returns common `not_found`;
  authority read failure remains named `managed_task_authorization_unavailable`.
- API absorbed concurrent `origin/master@8c0ba78b` with a normal merge after the feature branch had
  been pushed. Kernel/transport now resolve to one exact instance (`2fe845b` / `e031d6a`).

### Automation

| Commit | Delivery |
|---|---|
| `7d22a22` | narrowed Task/Plan/Run/Ledger/Trace contracts |
| `b27abc3` | canonical serialization, hashes, validation, safe projections |
| `0d1a048` | exact read-only `persona.research@1` registry |
| `239bdbc` | migrations 0106-0109, owner manifests, schema max |
| `e493afc` | typed authority/run/ledger/trace/account-lane stores |
| `db9a224` | guarded PostgreSQL concurrency/lease/target test |
| `0a4ecbf` | bounded immutable PlanCompiler and StepExecutor contracts |
| `e9bf456` | Create/Cancel/Query services, atomic command unit of work, safe projections |
| `de602c7` | transport pin plus real owner-service HTTP/drift slice |
| `4b885a3` | cancellation-before/after-dispatch reconciliation coverage |
| `7481dea` | durable account-lane arbiter and complete frozen legacy probe surface |
| `cd19501` | default-off TaskRunWorker with lease recovery, retries, checkpoints, cancellation, and shutdown retention |
| `c76c4c5` | four-capability read-only ResearchStepExecutor with evidence validation and dedupe tracing |
| `dab3314` | exact-target, generation-bound connection dispatch adapter and reconnect target selection |
| `77ea3af` | offline/reconnect, timeout, empty, dedupe, recovery, cancellation, and kill-switch vertical coverage |

Important store guarantees already present:

- every durable read/write filters server-injected `execution_target`;
- schema shape probes fail closed without runtime DDL;
- TaskRun/StepRun and Attempt terminal states cannot regress;
- claims and renewals use CAS plus bounded leases;
- command idempotency distinguishes duplicate from collision;
- a managed account lane is retained while an Attempt is `dispatching` or `submitted_unknown`;
- legacy lane acquisition requires concrete in-flight evidence;
- all nine legacy work sources are mandatory inputs; missing wiring remains explicit `unknown` and denies managed acquisition;
- expired TaskRun leases are recovered by target-scoped `SKIP LOCKED` claim without repeating completed checkpoints;
- dispatching or submitted-unknown Attempts are never inferred safe to retry, and graceful shutdown retains their lane;
- an undeliverable exact target checkpoints `waiting_for_edge`, safely releases the lane, and re-resolves transport on the next bounded Attempt;
- post-dispatch timeout stays `submitted_unknown`; reconnect receipts from an older connection generation cannot settle the Attempt;
- disabling new worker claims during an in-flight Attempt retains the account exclusion until a proved safe checkpoint;
- Create commits Task + Revision + Plan + Run + Trace + Receipt in one Automation transaction;
- Cancel is CAS-guarded and remains available when new task creation is disabled;
- Query returns only account-scoped customer projections and redacted trace summaries.

## 5. Validation evidence and honest gaps

Passed in `aidcp-automation`:

- command/store/service/HTTP edge-case slice: **14/14**;
- combined managed/schema/boundary focused run: **48/48**;
- schema/owner focused suite: **25/25**;
- acceptance suite: **145/145**;
- exact dispatch-adapter plus connection-runtime suite: **30/30**;
- lane/executor/adapter/worker/connection focused suite: **54/54**;
- TaskRunWorker lifecycle and vertical slice: **10/10**;
- full suite: **2109 pass / 0 fail / 4 guarded skips**;
- boundary census: `source=288 ownership=288 imports=813 unresolved=0 forbidden=0`;
- `npm run typecheck`: pass.

Passed in `aidcp-transport`:

- managed-task HTTP and drift focused suite: **10/10**;
- full suite: **46/46**;
- `npm run typecheck`: pass.

Passed in `aidcp-api`:

- managed-task API owner adapter: **7/7**;
- acceptance suite: **3/3**;
- full suite: **508/508**;
- `npm run typecheck`: pass;
- `npm ls`: one exact direct/transitive kernel instance and one transport instance.

The inherited `boundaries:refresh` / `boundaries:census` package scripts in this API baseline point
to a helper file that is not present in the split repository, so no API boundary-census pass is
claimed. The new file is in the existing `src/client-auth/` `newFile=inherit` API-owner rule and its
generated manifest entry was recorded explicitly; Automation's real boundary census remains green.

Passed in `aidcp-kernel` after absorbing the concurrent E-2 baseline:

- full suite: **73/73**;
- `npm run typecheck`: pass.

Added but not actually executed against PostgreSQL:

- `test/managed-automation/stores.integration.test.ts` is discovered and safely skipped because
  `DATABASE_URL` is unset and no guarded `aidcp_test*` database is available.
- It covers concurrent `SKIP LOCKED` claim, terminal CAS race, duplicate/collision, target isolation,
  expired lane takeover, and unknown-Attempt lane retention/release.
- Task 7.3 remains the authoritative requirement to run this test on an isolated test database.

No production route registration, atomic command-channel construction, worker/root wiring, deployment,
real Edge dispatch, installed-client capability, or platform action has been claimed. All four rollout
flags remain exact-lowercase-`true` opt-in and default false:

- `AIDCP_MANAGED_TASK_API_ENABLED`
- `AIDCP_MANAGED_TASK_CREATE_ENABLED`
- `AIDCP_MANAGED_TASK_WORKER_ENABLED`
- `AIDCP_MANAGED_TASK_LANE_ENABLED`

## 6. External production-root gate

`split-cloud-automation-production-runtime` remains **76/129** with the Automation readiness
ledger at **11 blockers**. In particular, `automation-production-runtime-composition-unwired`
is still open. Do not perform tasks 6.1-6.6 until E-2/G/H/main/readiness close and the blocker
ledger reaches zero.

This gate does not block pure owner-local implementation and tests for tasks 4.x and 5.x, as long
as no production composition-root file is wired.

## 7. Next implementation slice

Recommended next order:

1. Wait for the external production-root gate to close; refresh/rebase all owner worktrees under task 6.1.
2. Then perform tasks 6.2-6.6 serially across the production roots and legacy dispatch hotspots.
3. Run tasks 7.1-7.7 only after production wiring is complete; task 7.3 still requires a protected `aidcp_test*` database.

Do not extend task 4.2 by putting business services in kernel/transport or by reconnecting the old
Cloud monolith. Do not infer lane availability from WebSocket/session mode.

## 8. Closeout commands for the next session

Automation focused check:

```bash
cd /Users/baitianxing/codes/aidcp-automation.wt/add-managed-automation-task-channel-phase-1
npx tsx --test \
  test/managed-automation/contracts.test.ts \
  test/managed-automation/registry.test.ts \
  test/managed-automation/plan-compiler.test.ts \
  test/managed-automation/stores.test.ts \
  test/managed-automation/command-store.test.ts \
  test/managed-automation/task-command-service.test.ts \
  test/managed-automation/task-command-http-drift.test.ts \
  test/managed-automation/account-lane-arbiter.test.ts \
  test/managed-automation/research-step-executor.test.ts \
  test/managed-automation/connection-runtime-research-dispatch-adapter.test.ts \
  test/managed-automation/task-run-worker.test.ts \
  test/integration/connection-runtime.test.ts
npm run typecheck
npx tsx test/acceptance/helpers/boundary-record.ts census
```

Control validation:

```bash
cd /Users/baitianxing/codes/aidcp.wt/add-managed-automation-task-channel-phase-1
openspec validate add-managed-automation-task-channel-phase-1 --strict
```

When a task is completed, update `tasks.md` with repo, commit SHA, exact validation result,
deployment status, and deviations. A skipped PostgreSQL test is not a passing PostgreSQL test.
