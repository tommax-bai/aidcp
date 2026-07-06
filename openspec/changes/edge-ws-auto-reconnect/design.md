## Context

The edge core currently establishes one cloud WebSocket during startup. If that socket closes unexpectedly, pending requests fail and the client marks itself disconnected, but the process continues to run. Electron only supervises process exit, so a still-running but cloud-disconnected core can leave the operator with a stale "running" impression while cloud no longer routes work to that edge.

The reconnect behavior belongs inside the edge core because it owns the cloud socket, hello request, pacing snapshot, and command handlers. Electron should observe truthful lifecycle logs rather than implement a separate cloud protocol loop.

## Goals / Non-Goals

**Goals:**
- Automatically reconnect the cloud WebSocket after unexpected closure with bounded backoff.
- Re-run hello on each successful reconnect and refresh cloud-derived session/pacing state.
- Recover the browse loop by clearing transient command state and reporting the current page/note snapshot.
- Keep status honest: logs and Electron status must show reconnecting, reconnected, and exhausted states.
- Avoid stale replay: commands or publish work tied to the old socket must not be blindly replayed.

**Non-Goals:**
- Change the cloud protocol schema or add cloud-side reconnect APIs.
- Reconnect AdsPower/CDP here; that remains covered by the existing CDP resilience contract.
- Persist disconnected command queues across cloud restarts.
- Treat reconnect as a risk/budget reset.

## Decisions

- Implement reconnect in `EdgeClient`, not Electron.
  - Rationale: the edge client already owns socket creation, hello, request correlation, and connection truth. Electron cannot safely infer protocol readiness from process state alone.
  - Alternative considered: have Electron kill and restart the core when it sees `WS 已关闭`. That is useful as a last-resort supervisor behavior, but it loses in-memory browser/session context and still leaves a window where the core is alive but unroutable.
- Use bounded exponential backoff with an explicit exhausted state.
  - Rationale: short cloud restarts should self-heal, while long outages must not leave a permanent fake-running process. Exhaustion can exit the core with a restartable failure.
  - Alternative considered: infinite retry. That reduces manual intervention during long outages but makes "running" ambiguous and can hide broken credentials or network reachability indefinitely.
- Re-run hello after every reconnect and notify the browse session.
  - Rationale: cloud restart loses in-memory routing and pacing state. A fresh hello is the existing registration contract, and the browse session should resume from the current observed page rather than stale commands.
  - Alternative considered: reconnect only the TCP/WebSocket layer without re-hello. That would not re-register the edge after cloud process memory is reset.
- Do not replay old commands.
  - Rationale: commands may reference stale page coordinates, old cloud request IDs, or publish state from a dead process. The honest recovery point is a new page snapshot and cloud re-decision.

## Risks / Trade-offs

- [Risk] Reconnect can race with intentional shutdown. -> Mitigation: intentional `close()` disables reconnect timers and prevents new socket creation.
- [Risk] Cloud restarts while edge is executing an action. -> Mitigation: fail pending requests on socket close and do not replay in-flight commands; after reconnect, report current page truthfully.
- [Risk] Backoff exhaustion could stop a recoverable long outage. -> Mitigation: exhaustion exits with restartable semantics so Electron/supervisor can surface the issue and allow a clean restart.
- [Risk] Re-hello may refresh pacing/session fields while browse loop is active. -> Mitigation: apply the new pacing snapshot through the existing browse-session pacing path before re-reporting page state.
