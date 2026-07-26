## Context

Environment creation currently performs the right high-level order—ensure the bundled CLI service, resolve `aidcp` through `group/list`, then call `user/create`—but two seams can still select the wrong runtime state. First, `resolveAdsOpts` gives a renderer/settings `apiBase` higher priority than the actual port returned by `ads status`, so an old `50325` value can redirect creation away from a managed daemon that correctly fell back to another port. Second, the CLI PID/state registry is machine-level; `ads status` can report a daemon left by an earlier AIDCP or CLI session, and `ensureRuntime` currently adopts it without refreshing the start-time account context.

The repository already has bounded `stopRuntime` behavior, starts the bundled runtime through one `ensureAdsServiceOnce` single-flight, stops the managed daemon during an orderly app quit, and can recover browser children after a daemon registry restart through profile-scoped CDP validation. This change closes the cold-session ownership seam without scanning or signaling the independent AdsPower desktop process.

## Goals / Non-Goals

**Goals:**

- Establish one fresh registered CLI daemon at most once per AIDCP desktop-app session before managed reads/writes begin.
- Make the CLI-reported `adsServiceBase` authoritative whenever a managed runtime has been established.
- Keep `group/list` as the exact pre-write self-proof for the required `aidcp` group.
- Return specific, actionable failures for daemon-stop failure and fresh-runtime group absence.
- Cover reset ordering, alternate-port routing, and fail-closed creation with focused tests.

**Non-Goals:**

- Killing the independent AdsPower desktop application or scanning arbitrary processes by executable name.
- Creating or renaming AdsPower groups automatically.
- Packaging or publishing a desktop installer in this change.
- Changing browser lifecycle ownership, Cloud protocol, account assignment, or proxy behavior.

## Decisions

### 1. Reset only through the bundled CLI control path, once per app session

The first `ensureAdsServiceOnce` attempt in an app session will ask the resolved bundled CLI to run its existing bounded `status`/`stop` sequence before `ads start`. “Already stopped” is success. A stop command failure or a daemon that remains running after the confirmation bound is a hard failure; the app will not continue to `group/list` or `user/create`.

The reset marker becomes complete only after a fresh `ensureRuntime` succeeds. If warm-up fails partway through, the next real action retries the reset instead of trusting partial state. Later service re-ensures in the same healthy app session do not repeatedly stop the daemon.

Alternative considered: process-name scanning and `SIGKILL`. Rejected because it cannot distinguish the bundled CLI daemon from AdsPower desktop or unrelated user processes and would bypass the CLI's own state cleanup.

Alternative considered: restart only after `group/list` misses `aidcp`. Rejected because stale-base routing could query a foreign but healthy endpoint first, and a new session should establish its managed runtime identity before any metadata operation rather than repair it after an ambiguous result.

### 2. Managed runtime base outranks renderer and persisted API-base values

Once `ensureAdsServiceOnce` has populated `adsServiceBase`, `resolveAdsOpts` will select it before form or persisted values. Form/settings values remain fallback inputs only when no managed base exists. This preserves cold diagnostic behavior while preventing a historical `50325` override from redirecting a managed creation flow whose CLI reported `50326` or another port.

Alternative considered: clear historical settings on load. Rejected because destructive migration is unnecessary and would erase an operator override that may still be useful in development or before managed service establishment.

### 3. Exact `aidcp` visibility remains the write gate

The existing group resolver remains before `user/create` and continues matching `groupName === 'aidcp'`. After the fresh runtime and authoritative-base changes, a successful `group/list` with no exact match is no longer described as generic service unavailability; it reports that the current managed runtime account/permission space lacks the pre-provisioned group. No automatic `group/create` fallback is restored.

### 4. Keep orchestration testable below Electron boot

The reset-before-ensure behavior will live in the Ads runtime helper with injectable command execution, while `main.cjs` owns the one-per-app-session marker and base precedence. Focused unit tests will assert command order and failure propagation without launching Electron or real AdsPower processes; existing create-service tests will cover the clarified group failure.

## Risks / Trade-offs

- **Registered CLI daemon is shared by another CLI consumer** → The reset uses only the CLI's registered daemon control path and runs once at the explicit AIDCP session boundary, but another CLI consumer can still be disrupted. The client will never scan/kill AdsPower desktop or arbitrary processes, and stop failure remains fail-closed.
- **A daemon reset temporarily loses V2 registry state while a browser child survived a prior crash** → Existing profile-scoped `DevToolsActivePort` validation remains the recovery path; no broad process adoption is added.
- **Warm-up and a user action race** → Existing `ensureAdsServiceOnce` single-flight serializes them; the session reset marker is committed only after success.
- **Fresh daemon still lacks `aidcp`** → Creation stops before `user/create` with account/permission-specific guidance. Repeating a restart would not repair an operator-side missing group, so recovery is bounded to the one session reset.

## Migration Plan

1. Land the OpenSpec delta and focused Edge tests.
2. Land Edge source changes on `master`; do not package an installer unless explicitly requested.
3. On first launch with the new source/build, the app resets any registered CLI daemon once, starts the managed runtime, and uses its reported base.
4. Rollback is a source revert: the previous adoption/base-precedence behavior returns without data migration.

## Open Questions

None for source implementation. Real-machine coexistence with AdsPower desktop on `50325` remains a packaging acceptance case, not a prerequisite for code-level validation in this change.
