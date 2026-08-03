## Context

`spawnEdgeChild()` freezes the authenticated deployment target into `handle.spawnCloudKey`, creates a Node `ChildProcess`, assigns it to `handle.child`, and only later attaches stdout, IPC, error, exit, and close observers. A stale post-refactor reference (`resolvedCloudKey`) is evaluated while building the initial status patch in that unobserved interval. The resulting synchronous `ReferenceError` escapes to the launch queue, while the real child remains owned only by a truthy handle and eventually exits after its broker request times out.

The installed symptom is therefore internally contradictory but mechanically consistent: slot accounting sees no live OS process (`0/N`), while start guards and UI projection still see `handle.child` and remain `starting`. AdsPower runtime state and profile data are not involved.

## Goals / Non-Goals

**Goals:**

- Use the exact deployment target frozen for the current child in every pre-connection startup projection.
- Establish launch readiness and every child observer immediately after the supervisor assumes ownership.
- Fail closed and visibly if any later synchronous setup step throws, while preserving ownership until the child is actually reaped.
- Add a semantic undeclared-identifier gate for Electron CJS plus focused lifecycle-order regression coverage.

**Non-Goals:**

- Redesigning the browser-slot scheduler, respawn policy, AdsPower Local API FIFO, or Cloud protocol.
- Changing deployment-target selection, account sessions, profile data, proxies, or browser kernels.
- Packaging, installing, deploying, or exercising a real account.

## Decisions

### D1 — Read the target from the lifecycle-frozen handle

The initial `targetCloudKey` projection SHALL use `handle.spawnCloudKey`, which is assigned from `cloudSel.key` before `spawn()`. The spawned environment, pending status, and later connection receipt therefore refer to one lifecycle-scoped value.

Alternative rejected: recreate a local `resolvedCloudKey` alias. A second alias can drift again and adds no authority beyond the already-frozen handle field.

### D2 — Assume ownership, create readiness, then attach named observers immediately

After `spawn()` returns, a narrow `core-child-startup.cjs` helper SHALL assign `handle.child`, create and retain the `launchReady` promise, and register message, error, exit, close, and available stdout/stderr handlers before proxy-pipe delivery, queue release, or status publication. Existing handler bodies remain local to `spawnEdgeChild()` as named function declarations; the helper only makes ordering and Node's pre-spawn-versus-runtime `error` distinction executable without extracting a new supervisor subsystem.

Alternative rejected: only move the initial `updateStatus()`. That fixes this exact throw site but leaves another post-spawn synchronous operation able to recreate the same unobserved-child failure.

### D3 — Treat post-spawn setup exceptions as launch failures, not detached work

The post-spawn setup segment SHALL be guarded. On exception it records a redacted stable lifecycle-scoped error, settles launch readiness as false, releases any start-queue reservation, projects a per-environment warning where possible, and sends best-effort `SIGTERM` followed by one bounded `SIGKILL` request if the child does not terminate. It MUST keep `handle.child` until a pre-spawn error or `exit`/`close` observes the actual terminal event; an `error` emitted after spawn confirmation may only mean kill/send delivery failed and is not itself proof of process death.

The existing current-child and one-time exit finalizer remain authoritative for clearing the handle, releasing execution capacity, advancing FIFO, and applying bounded respawn policy. A retryable setup marker supplies a stable failure summary and a synthetic non-zero policy input even if the core handles SIGTERM and exits with code 0. A known non-retryable proxy setup marker preserves its actionable proxy failure instead of converting cleanup SIGTERM into a respawn loop.

Alternative rejected: clear `handle.child` directly in the catch block. That would make the UI look stopped while a real child might still be running and would allow a second spawn for the same environment.

### D4 — Add semantic CJS scope checking without turning on whole-file JS type checking

A focused test invokes the TypeScript compiler over `main.cjs` and fails only on undeclared/typo identifier diagnostics `TS2304` and `TS2552` from the exact loaded source file. The repository's normal TypeScript project excludes Electron CJS, while full `checkJs` currently reports many unrelated structural diagnostics; filtering to scope errors catches this regression class without creating a broad migration.

An executable fake-`ChildProcess` harness covers successful setup, missing stdio on spawn failure, synchronous setup exceptions, queue release, post-spawn kill errors, one-time terminal cleanup, graceful-code-0 retry semantics, and non-retryable proxy failure semantics. Source contracts additionally assert integration ordering and frozen-target use.

## Risks / Trade-offs

- **[Moving listener registration changes event timing]** → Preserve every existing handler body and current-child/generation guard; the helper changes only registration order and error classification.
- **[A setup failure is reported twice]** → The catch records setup failure, while the existing one-time finalizer owns terminal classification; current-child and finalization guards prevent duplicate cleanup.
- **[A cleanup signal cannot be delivered]** → Keep ownership, expose the setup reason, make one bounded force-termination request, and never spawn a duplicate without observed termination.
- **[Compiler scope gate becomes noisy]** → Filter only `TS2304`/`TS2552` diagnostics attached to the exact `src/electron/main.cjs` `SourceFile`; do not gate unrelated JS typing diagnostics.
- **[Concurrent browser-slot work advances main]** → Rebase the isolated Edge worktree before integration and rerun focused, full, typecheck, and strict OpenSpec gates.

## Migration Plan

1. Land the control artifacts and Edge fix through matching isolated branches/worktrees.
2. Run focused lifecycle/target tests, `node --check`, the full Edge suite, typecheck, and strict OpenSpec validation.
3. Integrate only by fast-forward after rebasing onto the latest default branches.
4. Packaging and installation remain a separate explicitly authorized step; existing local settings and AdsPower runtime files require no migration or deletion.

Rollback is a source revert before packaging. No persistent data shape changes are introduced.

## Open Questions

None.
