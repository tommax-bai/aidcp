# Phase-one managed automation task channel handoff

Updated: 2026-08-01 (Asia/Shanghai)

## 1. Start here

This is the active implementation change:

- Change: `add-managed-automation-task-channel-phase-1`
- Progress: **15/39 tasks (38%)**
- Control branch: `codex/add-managed-automation-task-channel-phase-1`
- Control worktree: `/Users/baitianxing/codes/aidcp.wt/add-managed-automation-task-channel-phase-1`
- Automation worktree: `/Users/baitianxing/codes/aidcp-automation.wt/add-managed-automation-task-channel-phase-1`
- Kernel worktree: `/Users/baitianxing/codes/aidcp-kernel.wt/add-managed-automation-task-channel-phase-1`

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

The branches were fetched on 2026-08-01. Control was rebased without conflict after `origin/main`
advanced by six documentation/handoff commits.

| Repo | Default baseline | Feature head at handoff | Default behind feature | Feature behind default |
|---|---|---|---:|---:|
| `aidcp` | `origin/main@0d283679` | handoff commit on this branch | feature commits only | 0 |
| `aidcp-automation` | `origin/master@ac09a7f` | `0a4ecbf` | 7 commits | 0 |
| `aidcp-kernel` | `origin/master@27cbfc5` | `34d1b94` | 1 commit | 0 |

Do **not** merge the phase-one branches into defaults yet. The change is incomplete, the HTTP
port/worker/production roots are not built, and guarded PostgreSQL integration has not run.
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

### Kernel (`34d1b94`)

- Versioned Create/Cancel/Query DTOs and `ManagedTaskCommandPort`.
- Actor, target, result, collision, unknown-result, and customer projection contracts.
- DTO/port only; no business execution code.

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

Important store guarantees already present:

- every durable read/write filters server-injected `execution_target`;
- schema shape probes fail closed without runtime DDL;
- TaskRun/StepRun and Attempt terminal states cannot regress;
- claims and renewals use CAS plus bounded leases;
- command idempotency distinguishes duplicate from collision;
- a managed account lane is retained while an Attempt is `dispatching` or `submitted_unknown`;
- legacy lane acquisition requires concrete in-flight evidence.

## 5. Validation evidence and honest gaps

Passed in `aidcp-automation`:

- managed contract/registry/compiler/store focused suite: **26/26**;
- schema/owner focused suite: **25/25**;
- boundary census after compiler: `source=278 ownership=278 unresolved=0 forbidden=0`;
- `npm run typecheck`: pass.

Added but not actually executed against PostgreSQL:

- `test/managed-automation/stores.integration.test.ts` is discovered and safely skipped because
  `DATABASE_URL` is unset and no guarded `aidcp_test*` database is available.
- It covers concurrent `SKIP LOCKED` claim, terminal CAS race, duplicate/collision, target isolation,
  expired lane takeover, and unknown-Attempt lane retention/release.
- Task 7.3 remains the authoritative requirement to run this test on an isolated test database.

No production route, worker, root wiring, deployment, real Edge dispatch, or platform action has
been claimed. All four rollout flags remain exact-lowercase-`true` opt-in and default false:

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

1. Task 4.1: implement Automation-owned Create/Cancel/Query services.
   - Introduce one atomic creation unit of work for Task + Revision + Plan + Run + command receipt;
     do not compose five independent pool writes in the service.
   - Validate local target before owner reads, verify the API-owned authorization projection,
     validate payload hash/idempotency, registry, parameters, capability scope, schema readiness,
     and feature gates.
   - Append decision traces without allowing traces to become state authority.
2. Task 4.2: implement authenticated versioned internal routes/client with stable
   `result_unknown`; then task 2.5 contract drift tests.
3. Tasks 4.3-4.5: API authorization adapter and customer-safe query projection.
4. Tasks 5.2-5.6: lane arbiter, worker, research executor, dispatch adapter, vertical slice.
5. Tasks 6.x only after the external production-root gate closes.

Do not solve task 4.1 by putting business services in kernel/transport or by reconnecting the old
Cloud monolith. Do not infer lane availability from WebSocket/session mode.

## 8. Closeout commands for the next session

Automation focused check:

```bash
cd /Users/baitianxing/codes/aidcp-automation.wt/add-managed-automation-task-channel-phase-1
npx tsx --test \
  test/managed-automation/contracts.test.ts \
  test/managed-automation/registry.test.ts \
  test/managed-automation/plan-compiler.test.ts \
  test/managed-automation/stores.test.ts
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
