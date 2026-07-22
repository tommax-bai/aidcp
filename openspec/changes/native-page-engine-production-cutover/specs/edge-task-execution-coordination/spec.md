## ADDED Requirements

### Requirement: Task and command ownership MUST cross Native IPC

Every Native page command SHALL carry the active Edge `taskId`, a unique per-session `commandId`, and a bounded deadline. Native MUST reject stale task identities, duplicate command identities, and concurrent page writers before CDP dispatch. Edge remains the lease authority and MUST NOT consider IPC acceptance equivalent to platform execution success.

#### Scenario: Duplicate command identity is received
- **WHEN** Native receives a `commandId` already accepted in the current session
- **THEN** it rejects the duplicate or returns the already-recorded terminal result without redispatching browser input

#### Scenario: Lease changes between commands
- **WHEN** Edge grants the page executor to a new `taskId`
- **THEN** subsequent commands from the old task are rejected before dispatch

### Requirement: Cancellation and preemption MUST preserve effect truth

Edge cancellation/preemption SHALL be forwarded to Native and acknowledged only at a declared safe point. Native MUST finish any already-started atomic input region, classify the resulting effect phase, and stop before the next dispatch. Neither cancellation nor deadline expiry may turn a possibly dispatched write into a clean failure.

#### Scenario: Cancel before dispatch
- **WHEN** Native observes cancellation at a safe point before platform input
- **THEN** it returns `not_started` with cancellation reason and performs no write

#### Scenario: Cancel after submit dispatch
- **WHEN** cancellation arrives after a publish/comment/interaction submit may have been dispatched
- **THEN** Native performs only bounded verification and returns `confirmed` or `ambiguous`
- **AND** Edge MUST NOT retry or use JavaScript fallback

### Requirement: Native restart MUST NOT replay unfinished writes

If the Native process exits or is restarted, the supervisor SHALL create a new session identity and SHALL NOT replay an unfinished command automatically. Recovery MAY re-read current platform state for an explicit reconciliation command, but it MUST NOT infer `not_started` from missing in-memory Native state.

#### Scenario: Engine restarts after ambiguous interaction
- **WHEN** the previous process exited after possible dispatch and no terminal proof exists
- **THEN** Edge preserves an ambiguous outcome and requires existing reconciliation/manual handling rather than resending the interaction

