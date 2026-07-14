## Why

Edge may remain connected to cloud while the browser's CDP control channel is no longer responsive to input. In the incident, a normal `note.open` accumulated serial mouse-event waits for nearly three minutes, preventing a human-approved publish from safely taking over the browser. Existing recovery starts only after the CDP WebSocket closes, so this connected-but-stalled state is neither recovered nor reported accurately.

## What Changes

- Add an edge CDP control-health state that detects slow or timed-out CDP input commands, stops ordinary browse work at a safe command boundary, and records operator-useful latency diagnostics.
- Add an explicit CDP recovery path for the connected-but-stalled case: reconnect and rediscover the page target using the existing bounded recovery machinery; if recovery is exhausted, use the existing honest node recycle path.
- Make edge task acquisition fail immediately and explicitly when browser control is unhealthy, instead of waiting for the normal 45-second acquire timeout.
- Make cloud map that explicit acquisition failure to a truthful publish requeue notice: the client is connected, but browser control is unavailable and no publish command was sent.
- Preserve browser ownership boundaries: recovery MUST NOT force-stop an external or non-owned AdsPower browser.

## Capabilities

### New Capabilities

- `cdp-control-health-recovery`: Detect, expose, and recover the connected-but-unresponsive CDP input state with bounded, safe behavior.

### Modified Capabilities

- `browse-loop-resilience`: Pause ordinary browse work while CDP control is unhealthy and resume only after a verified recovery.
- `edge-task-execution-coordination`: Reject task acquisition promptly when the edge cannot safely control its browser.
- `publish-dispatch-resilience`: Requeue approved publishes with an explicit browser-control-unavailable result rather than an offline or generic acquire-timeout notice.
- `edge-node-supervised-recycle`: Treat exhausted recovery from a CDP control stall as a recyclable terminal state without touching a non-owned browser.

## Impact

- Edge: CDP client lifecycle, browse-session command admission, task coordinator, protocol types, diagnostics, and tests.
- Cloud: task lease failure mapping, publish dispatcher notification/result handling, protocol types, and tests.
- Control repo: protocol documentation and OpenSpec contract deltas.
- Desktop runtime: a new Edge client release is required for the browser-side protection; cloud deployment alone cannot change an already-installed client.
