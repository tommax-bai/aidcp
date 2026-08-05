## Context

Facebook startup authentication runs before the normal core lifecycle controller is assembled. Lifecycle IPC is queued during that interval and also exposed to the authentication coordinator as a cancellation signal. The current authenticated-quiet-window interruption branch closes only the TypeScript CDP session and exits the process; it never invokes the owned AdsPower browser handle. Electron later sees an intentional `user_close` core exit and reports both resources closed without browser-close evidence.

The existing owned-browser close implementation is already authoritative: it calls the AdsPower stop endpoint, probes the profile CDP endpoint until dark, retries/raises to the existing bounded OS process fallback, and returns false when death cannot be confirmed. This change must reuse that mechanism.

## Goals / Non-Goals

**Goals:**

- Make pause/close during every Facebook startup-auth phase close and confirm the owned browser before core exit.
- Keep startup blocked after an unconfirmed close and expose the existing `lifecycle.close_failed` result instead of progressing to identity or Cloud work.
- Require generation-scoped browser-close evidence before Electron projects an intentional core exit as closed.
- Preserve an explicit resume path after an unconfirmed startup close without starting another browser.

**Non-Goals:**

- Change AdsPower stop/retry/OS-kill mechanics, authentication recognition, Cloud behavior, protocol v2, risk state, or slot capacity.
- Add compatibility fallbacks, background retries, new user-visible states, or an installer release.
- Change external-occupancy close semantics where this machine never acquired the profile.

## Decisions

### D1. Resolve pre-controller lifecycle interruption through the owned browser handle

Add one startup-auth lifecycle settlement helper used by the initial authentication coordinator. For `close`, `pause_and_exit`, or `pause`, it invokes the existing `killAndConfirmDead()` handle. Confirmed death emits browser-close evidence and exits; unconfirmed death emits `lifecycle.close_failed` and does not leave startup authentication.

Alternative: allow startup to finish assembling the normal lifecycle controller and replay the queued close. Rejected because identity, Cloud connection, or account work could begin after the operator already requested a stop.

### D2. Block after failure and consume only explicit retry or resume

After an unconfirmed startup close, the helper remains at the startup boundary. A later stop command retries the same authoritative close. A later resume command returns control to a fresh authentication reconciliation in the same browser generation. There is no timer, automatic retry, or second lifecycle state machine.

Alternative: hang permanently after `close_failed`. Rejected because the existing UI advertises retry/resume and the retained core must remain operable.

### D3. Make browser-close evidence explicit and generation-scoped

The core emits a narrow local `lifecycle.browser_closed` IPC only after the owned close returns confirmed. The normal lifecycle controller and the startup helper share this evidence. Electron records it against the current lifecycle generation; an intentional child exit without matching evidence is projected as browser-close unconfirmed, never as closed.

The evidence delivery is awaited before `process.exit` so the child cannot truncate the message. If IPC delivery fails, the supervisor deliberately produces an honest false negative rather than a false success.

Alternative: infer success from the existing AdsPower stop log line. Rejected because stop request acceptance is not proof that the CDP endpoint became dark.

### D4. Keep the change Edge-local

The new message is parent/child IPC inside the desktop process family. It is not protocol v2 and does not cross the Edge/Cloud boundary.

## Risks / Trade-offs

- [Browser closes but confirmation IPC cannot be delivered] → Electron reports unconfirmed closure; a later read-only shell check or restart can reconcile, but it never reports false success.
- [A close fails during startup and no further operator command arrives] → The core and browser remain retained at the blocked startup boundary, matching the existing close-failed contract and performing no account-scoped work.
- [Lifecycle command ordering races around failure] → Reuse the existing pending-command FIFO and add focused ordering tests for retry and resume.
- [Concurrent hotspot drift in `src/main.ts` or Electron lifecycle code] → Rebase on current `master`, compare path intersections, and rerun full Edge validation before integration.

## Migration Plan

Implement in an isolated `aidcp-edge` worktree, run focused lifecycle/auth tests followed by acceptance, full tests, and typecheck, then fast-forward `master`. No database migration, Cloud deployment, or installer build is required. Rollback is a revert of the Edge commit; the prior behavior returns without persistent data changes.

## Open Questions

None.
