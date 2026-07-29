## Why

The Native Facebook cutover preserved the join executor's click-leg reuse check but lost the legacy page-lifecycle invariant that kept the browser on the target group between observe and click. Releasing the observe lease now resumes the recommendation feed before the click leg, causing a visible group → home → group bounce, an unnecessary second load, and avoidable `not_ready` failures on slow pages.

The later Cloud fail-fast policy also makes a no-click slow-render result permanently fail the target. We need to restore the earlier resilience intent without restoring the retained cooldown assignment that blocked later targets and produced false `no_targets`.

## What Changes

- Preserve the target group page across the bounded observe → pre-click-judge → click handoff of one logical join attempt; autonomous Native browsing MUST NOT navigate home during that handoff.
- Keep observe as the recovery authority: a fresh logical attempt still navigates to the canonical group page, while the click leg reuses only the exact current canonical group root.
- Give a pre-click, no-effect `not_ready`/navigation-readiness failure one bounded reload-and-reobserve recovery within the same logical attempt, with an auditable recovery count and no retained cooldown assignment.
- After a click may have been dispatched, prohibit automatic re-click. Reconcile membership, pending, and questionnaire state read-only; unresolved effects remain ambiguous and never become success.
- Preserve the fail-fast change's target-pool property: a finally failed attempt releases the unfinished-assignment slot, reports its concrete reason, and cannot cause false `no_targets`.
- Do not raise the established Edge/Native/Cloud timeout ceilings and do not add a configurable retry knob.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-group-join-resilience`: Restore page-continuous Native join handoff and a bounded no-click readiness recovery while preserving honest post-click reconciliation and non-blocking terminal failures.

## Impact

- Control: updated resilience contract, design, validation, and delivery evidence.
- Edge: task-coordinator/Native browse handoff lifecycle and Native Facebook join focused tests.
- Cloud: Facebook group-join scheduler recovery orchestration, audit evidence, and focused tests.
- Protocol/database/Console: no public command-schema or database-schema change is intended.
- Runtime: Edge and Cloud behavior changes require DEV deployment/refresh and live-state verification; OL and desktop packaging remain out of scope.
