## ADDED Requirements

### Requirement: Cross-platform Native commands preserve one-writer task ownership
Every Facebook page command and WeChat browser-session capture command SHALL carry the active Edge task identity, unique command identity, and bounded deadline through Native IPC. Native MUST reject stale tasks, duplicate dispatch, concurrent page writers, and platform/session mismatches before browser input.

#### Scenario: Stale Facebook task sends a write
- **WHEN** Edge has transferred the browser lease to a new task and the old task submits a Facebook interaction command
- **THEN** Native rejects the stale task before any CDP input

#### Scenario: Duplicate write identity is received
- **WHEN** Native receives a Facebook command identity it already completed
- **THEN** it returns the recorded terminal result or rejects the duplicate without redispatch

### Requirement: Cross-platform cancellation cannot erase ambiguous effects
Cancellation, timeout, process exit, or reconnect across Facebook and WeChat Native commands SHALL preserve the declared safe-point and effect-phase rules. Edge MUST NOT infer not-started merely because the Native process lost in-memory state.

#### Scenario: Native exits after possible Facebook submit
- **WHEN** the process exits after a publish/comment submit may have been dispatched and no terminal proof exists
- **THEN** Edge preserves an ambiguous outcome and does not replay the write

#### Scenario: WeChat capture is cancelled
- **WHEN** cancellation is observed during read-only WeChat session capture
- **THEN** Native stops at a safe point, closes its session, and returns a bounded cancelled result without fabricated material
