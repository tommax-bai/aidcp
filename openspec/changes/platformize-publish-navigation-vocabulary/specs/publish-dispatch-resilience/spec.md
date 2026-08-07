## MODIFIED Requirements

### Requirement: Browser-control-unavailable publish acquisition SHALL requeue truthfully

When cloud receives `task.released{reason:'cdp_unhealthy'}` while acquiring a publish lease, it SHALL fail acquisition immediately with a distinct browser-control-unavailable result. The publish dispatcher SHALL invalidate that authorization, return the draft to pending approval, and send an operator notice stating that the client may still be online but browser control is unavailable and no publish command was dispatched. It MUST NOT describe this result as edge offline, a normal acquire timeout, or a failed publish sequence.

#### Scenario: Connected edge rejects a publish lease because CDP is unhealthy
- **WHEN** a publish lease receives `cdp_unhealthy` before `task.acquired`
- **THEN** the draft returns to pending approval, the authorization is invalidated, the notice confirms no publish command was sent, and re-approval is required after browser control recovers

#### Scenario: Existing acquisition failures remain distinct
- **WHEN** a lease fails because no edge is online, normal acquisition times out, or a publish sequence fails after acquisition
- **THEN** cloud preserves the existing offline, acquire-timeout, and post-acquire failure semantics rather than reporting `cdp_unhealthy`
