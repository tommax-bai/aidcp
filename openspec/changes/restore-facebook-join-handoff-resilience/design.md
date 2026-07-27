## Context

The legacy Facebook session's `resumeAfterTask()` was deliberately a no-op: once an observe leg released its page lease, the browser remained on the canonical target group until the click leg arrived. The click executor could therefore reuse the already-hydrated group page and avoid a second navigation.

The Native-only host session changed that lifecycle. Its generic `resumeAfterTask()` calls `start()`, and Facebook `start()` executes `browse_scroll(reason=initial_scan)`, whose Rust implementation navigates to `https://www.facebook.com/`. The current Cloud join scheduler still releases the observe lease while it evaluates the pre-click verdict, so task release now produces:

```
observe group → release lease → Native initial_scan/home → acquire click lease → navigate group again
```

The Rust `group_join` implementation still has the correct click-leg canonical-page reuse rule. The lost invariant is in the Native host session, not the target resolver or click implementation.

Separately, the current resilience spec makes `not_ready` and `nav_error` terminal immediately. That preserved a concrete failure and removed the old `assigned` cooldown row that blocked later targets, but it also permanently consumes a valid target after one no-click slow render. The established observe leg is already the safe reload authority, so one in-attempt fresh observe can recover without recreating the database cooldown problem.

## Goals / Non-Goals

**Goals:**

- Restore legacy Facebook task-release page continuity in the Native host.
- Keep autonomous browsing unblocked after a task while deferring home navigation until a deliberate feed command actually arrives.
- Retry exactly once after a no-click `not_ready` or `nav_error`, using a fresh observe leg that navigates the canonical group URL.
- Audit that bounded recovery and keep the final concrete failure if recovery also fails.
- Preserve the fail-fast target-pool property: no cooldown assignment, no false `no_targets`, and no attempt-cap rollback.
- Preserve post-click truth: never automatically repeat a click whose effect may already exist.

**Non-Goals:**

- No change to Rust target scoping, React-compatible click actuation, or canonical click-leg reuse.
- No retry for lease/control-plane failures, timeouts, login/captcha, gated groups, missing buttons, or post-click ambiguity.
- No new database status, schema migration, configurable retry count, or timeout increase.
- No OL deployment, installer packaging, or claim of real-account confirmation from tests.

## Decisions

### 1. Restore Facebook-specific Native resume semantics at the host boundary

`NativeBrowseSession.resumeAfterTask()` will clear the task block and restart the passive Facebook page probe, but it will not call `start()` for Facebook. Xiaohongshu retains the existing generic resume behavior.

This is equivalent to the retired Facebook session's command-driven lifecycle. It does not strand feed browsing: the Native Facebook engine already retains `active_list_url`, and the next deliberate feed scroll calls `ensure_facebook_active_list`, which navigates back to the saved feed/search list when the current page differs. The task release itself no longer manufactures that navigation.

Changing Rust `group_join` reuse was rejected because the browser is genuinely on home today; weakening its canonical-page check would skip a necessary navigation and risk acting on the wrong page. Adding a universal coordinator delay was rejected because it would guess at Cloud timing and penalize every platform/task instead of restoring Facebook's established lifecycle.

### 2. Recover only no-click readiness failures, once, inside the same scheduler invocation

The Cloud scheduler will treat an observe result as recoverable only when:

- `clicked !== true`; and
- the reason is `not_ready...` or `nav_error...`.

It will write a non-terminal scheduler audit row and issue one more ordinary observe leg. Observe remains unconditional navigation, so the recovery gets a clean group-page load. A successful second observation proceeds through the existing judge and click legs. A second failure follows the current terminal `failed` path with the original concrete final reason and no cooldown.

Restoring `markTransientRetry` was rejected because its persisted `assigned` plus cooldown state occupied the account's unfinished-assignment slot and caused false `no_targets`. Retrying indefinitely or adding a configured count was rejected because one observed slow-load failure justifies one bounded recovery, not an open-ended policy.

### 3. Keep clicked and control-plane outcomes outside recovery

`post_not_confirmed_slow`, `join_verification_ambiguous`, or any result with `clicked=true` MUST NOT enter the observe retry. Those outcomes may describe a real platform effect; automatically running another click could duplicate the action or consume risk quota twice.

Lease acquisition/disconnect/control-plane failures remain concrete terminal failures for the target under the current policy. Login/captcha keeps its account-level pause and long backoff. This change only repairs a page-read failure before any irreversible effect.

### 4. Retain current timing and ownership budgets

The existing 30-second join readiness, 45-second post-click verification, 90-second Native command, 120-second Cloud step, and three-minute page lease budgets remain unchanged. The extra observe is sequential and only occurs after the first no-effect result has completed; it does not overlap page writers or create a speculative command.

## Risks / Trade-offs

- [Leaving the group page visible after task release could surprise feed scheduling] → The next explicit feed scroll already validates and restores `active_list_url`; add a host-session test proving resume itself does not navigate and a router contract test remains the feed authority.
- [A genuinely broken group page now costs one extra navigation] → Bound recovery to exactly one no-click attempt and audit it; the second failure remains terminal.
- [A navigation error may reflect a permanent bad URL] → Canonical target validation still runs before execution; one reload is bounded and a repeated error is terminal.
- [A post-click slow render could look similar to a pre-click slow render] → Gate recovery on both phase/result reason and `clicked !== true`; add regression coverage proving clicked ambiguity is never replayed.

## Migration Plan

1. Land the control contract and focused Edge/Cloud implementations in matching isolated worktrees.
2. Validate Edge Native session behavior and Cloud scheduler recovery with focused tests, then run the owning repositories' required suites and typechecks.
3. Integrate Edge and Cloud serially onto the latest default branches, push, and deploy DEV only from canonical checkouts.
4. Verify DEV source/runtime revisions, service health, Edge startup/runtime logs, and a controlled join trace when an account is available.
5. Roll back by reverting the Edge and Cloud commits together. No database migration or data rewrite is required.

## Open Questions

None. Real Facebook confirmation remains a separate platform acceptance boundary.
