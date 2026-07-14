## Context

The current CDP lifecycle recovers only when the page WebSocket closes. The incident was different: the WebSocket and edge-cloud connection both remained open, while serial `Input.dispatchMouseEvent` calls became extremely slow. A legacy `note.open` therefore spent minutes before reaching its modal timeout and prevented task handoff.

The edge now has a bounded `note.open` source implementation, but a CDP input timeout is still an uncertain browser-control result: the browser may apply that input after the client timeout. It is unsafe to immediately grant a publish lease on the same browser.

## Goals / Non-Goals

**Goals:**

- Detect connected-but-unresponsive CDP input control and make it observable.
- Stop ordinary browsing at a command boundary and prevent page-writing task acquisition while control is uncertain.
- Reuse bounded CDP recovery and the existing supervised recycle path without silently treating a WebSocket connection as a usable browser.
- Return a fast, truthful cloud result that distinguishes browser-control failure from edge offline and confirms no publish command was sent.

**Non-Goals:**

- Do not retry or replay an uncertain click, scroll, or publish command.
- Do not force-stop an external or otherwise non-owned AdsPower browser.
- Do not change content generation, approval policy, or a successfully acquired publish command sequence.

## Decisions

### 1. CDP input health is a first-class edge state

`CdpClient` will measure command duration and classify browser control as `healthy`, `recovering`, or `unavailable`. A timed-out `Input.*` command immediately enters the unavailable path; repeated successful-but-slow input responses enter recovery only after a small consecutive threshold. The event payload includes method, observed duration when available, classification reason, and a process-local recovery correlation id, but no page content or credentials.

Input is chosen over all CDP methods because an input command is the direct browser-control capability required for browse and publish. A slow DOM read alone is diagnostic but does not prove that a click cannot be controlled.

### 2. Timeout is an uncertainty fence, not a retry signal

After an input timeout, the edge MUST stop starting new browse commands and MUST reject new task leases. It MUST NOT declare browser control healthy merely because the old WebSocket reconnects: the timed-out input may have been accepted by Chrome after the client stopped waiting.

For a browser owned by the edge, exhausted recovery escalates to the existing recycle path, which creates a fresh safe browser boundary before future work. For an external/reused browser, the edge remains unavailable and requires operator restart/reconnect; it never kills that browser.

### 3. Reuse CDP recovery for the soft-stall path

For repeated slow but completed inputs, the client explicitly starts the existing bounded rediscover-target, re-enable, and anti-detection reinjection path. Browse remains paused until it completes. A successful recovery clears only the soft-stall state and causes the browse session to re-report current page state for cloud re-planning; it never replays the interrupted command.

This reuses current recovery limits and lifecycle hooks rather than adding a second reconnect loop.

### 4. Task acquisition receives an explicit negative acknowledgement

`EdgeTaskCoordinator` receives a browser-control readiness predicate. If false, it MUST NOT call `quiesceForTask` or acquire ownership. It sends `edge.task.released{reason:'cdp_unhealthy'}` immediately.

Cloud treats that release while acquisition is pending as `EdgeTaskLeaseError('edge_unhealthy')`, not as a normal release or a 45-second timeout. This preserves the task-id protocol and avoids inventing an independent acquire-rejected message.

### 5. Publish results remain truthful and non-destructive

The publish dispatcher maps `edge_unhealthy` to a requeue result: the draft returns to pending approval, the authorization is invalidated, the notice says the client may still be online but browser control is unavailable, and no publish command was dispatched. Existing offline, normal acquisition timeout, and post-acquire sequence-failure paths remain distinct.

## Risks / Trade-offs

- [Transient input jitter could pause browsing] → a single timeout is treated as unsafe, while slow-success recovery needs a consecutive threshold; pausing browse is cheaper than allowing an uncertain click to overlap a publish.
- [A recoverable external browser stays unavailable] → this is intentional: without ownership the edge cannot prove that a timed-out input is no longer in flight; the operator restarts it explicitly.
- [Recovery interrupts an ordinary browse atom] → the atom reports failure and is never replayed; cloud receives a fresh page snapshot only after recovery.
- [New release reason is ignored by older cloud] → edge still does not grant ownership; cloud falls back to its existing acquisition timeout. Cloud is deployed before the updated desktop client for the improved fast result.
- [A timeout occurs during a publish command] → the current publish atom reports its command failure honestly and is never retried automatically; recovery/recycle does not convert it to success.

## Migration Plan

1. Add synchronized protocol and contract changes, then implement and test edge health/recovery and cloud negative-ack mapping in isolated worktrees.
2. Merge edge and cloud changes to their default branches, deploy cloud to `dev`, and verify service, database, and Feishu health.
3. When an operator explicitly authorizes a desktop release, build and publish a new Edge client through the normal release path, update the affected client, and verify an induced input timeout produces `cdp_unhealthy` rather than a 45-second acquire timeout.
4. Roll back cloud/edge commits if protocol or recovery behavior regresses. Older clients remain safe through cloud's existing acquire timeout and release cleanup, but lack the fast classification.

## Open Questions

- None for the safety contract. The exact underlying AdsPower/Chrome cause is intentionally left observable rather than guessed; per-command diagnostics from this change will distinguish future occurrences.
