## Context

Cold standby was introduced to close the browser during deterministic long waits while keeping the edge engine and cloud lifecycle stable. The intended parked state is:

```text
browser closed
core alive
cloud connection maintained or recovering
Electron remains in standby
```

The dev incident for account `工程师大白` showed a different behavior. After a daily view-quota wait, the edge repeatedly reconnected, cloud armed nickname capture, no initial `page.cards` arrived, capture timed out, cloud sent `back`, and the connection dropped again. This created an operator-visible loop of "account ready / cloud connected / browse started / browse ended".

There are two independent failure amplifiers:

- Edge treats cloud reconnect exhaustion in the same way regardless of standby state: core exits with recycle semantics, and Electron can respawn the full browser startup path.
- Cloud arms nickname capture on connection setup, even when reconnecting or when the account already has a nickname. That makes a parked/recovering edge wait for first feed cards and issue recovery `back` commands when cards do not arrive.

## Goals / Non-Goals

**Goals:**

- Keep cold standby as the primary state until scheduled wake, manual wake, or a real new browser startup occurs.
- Do not restart the browser just because cloud reconnects exhausted while already in cold standby.
- Make cloud reconnect loss during standby visible as a standby substate, not as a generic login/run failure.
- Trigger nickname capture only once after a full browser start/restart reaches first feed cards.
- Add focused regression tests for the standby reconnect and nickname-capture boundaries.

**Non-Goals:**

- Do not change quota computation, risk policy, pacing, or standby eligibility.
- Do not make cloud believe a disconnected WebSocket is connected.
- Do not package or release a desktop installer.
- Do not remove nickname capture entirely; it remains a startup-time display-name refresh.

## Decisions

### Decision 1: Treat standby cloud reconnect exhaustion as standby-degraded, not recycle

When core receives `cloud.unrecoverable` while `coldStandbyActive` is true, it should not call the normal shutdown/recycle path. Instead it remains in cold standby and reports a lifecycle/status signal to the Electron supervisor so the shell can show that standby is still active while cloud connectivity is recovering.

Alternative considered: increase reconnect attempts. That only reduces frequency; it still lets a long outage convert standby into browser respawn.

### Decision 2: Electron must preserve standby classification across child close

Electron already tracks `coldStandbyPending` and `coldStandbyActive`. Those flags must participate in child-close classification. A child close during standby is an intentional standby loss/degraded state, not an ordinary abnormal exit that should consume respawn budget and start a browser.

Alternative considered: rely only on core never exiting. That is not sufficient because process exits can still happen from OS/runtime errors, and the supervisor must not turn those into immediate browser startup loops while the operator expected standby.

### Decision 3: Nickname capture is tied to browser generation first-feed readiness

Cloud should stop arming nickname capture from hello/reconnect alone. The only normal trigger is the first `page.cards` after a complete browser start/restart, once for that browser generation. This preserves the useful "startup display-name refresh" behavior while removing reconnect/cold-standby noise.

Implementation can use an explicit edge-side browser generation if available, or a cloud-side per-connection startup-readiness latch if that is the least invasive path. The invariant is behavioral: cloud reconnect without browser restart must not reopen the nickname capture latch.

### Decision 4: Existing nickname does not justify reconnect capture

If `accounts.nickname` is already populated, reconnect must not trigger a refresh. A later full browser startup may refresh once if the startup latch opens, but reconnect alone remains a no-op.

## Risks / Trade-offs

- Standby cloud reconnect might remain degraded longer than before if cloud is unavailable. Mitigation: preserve clear standby/reconnecting UI and scheduled/manual wake paths.
- If a real browser restart is not distinguishable from a core reconnect, nickname capture could be under-triggered. Mitigation: base the latch on browser startup/feed readiness and add tests for full restart versus cloud reconnect.
- Supervisor logic can accidentally hide true crashes. Mitigation: only suppress browser respawn while explicit standby flags are active; non-standby abnormal exits keep existing honest warnings and respawn policy.
- Older edges will ignore any new status detail. Mitigation: keep protocol additions optional and localized to Electron/core IPC where possible.

## Migration Plan

1. Implement and validate in isolated `aidcp-edge` and `aidcp-cloud` worktrees using change name `cold-standby-reconnect-stability`.
2. Run focused tests first, then repo typechecks.
3. Land to default branches without force-push.
4. Deploy cloud changes to dev from the clean default checkout.
5. Do not build desktop installers; edge fix becomes available to local build/run and next explicit release.
