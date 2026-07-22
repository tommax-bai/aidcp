## ADDED Requirements

### Requirement: Automation must run one writer instance per execution target

The automation process that owns risk state and quota admission SHALL run as exactly one instance per `executionTarget`. Uniqueness MUST be enforced mechanically, not only by written deployment discipline: the process MUST acquire a database-level mutual exclusion handle (a session-scoped advisory lock keyed by `executionTarget`) before enabling any risk write path.

The deployment shape MUST remain stop-then-start. Rolling and blue-green deployments of the automation writer MUST NOT be used, because their overlap window makes the single-writer invariant false exactly while both builds are live.

Fail-closed rules:

- When the writer lock cannot be acquired within a bounded wait, the process MUST refuse to enable the risk write path, MUST emit an alert naming the target whose lock is held, and MUST exit non-zero. It MUST NOT continue without the lock.
- When the lock-holding connection drops, the process MUST treat write authority as lost, MUST stop dispatching new interaction commands, and MUST alert. It MUST NOT keep writing risk state.
- When `executionTarget` is missing or invalid, the process MUST NOT acquire the lock, MUST NOT enable the risk write path, and MUST NOT start the risk accounting worker.

#### Scenario: Rolling deployment fails loudly

- **WHEN** a second automation instance for the same `executionTarget` is started while the first still holds the writer lock
- **THEN** the second instance MUST fail to acquire the lock within the bounded wait, alert, and exit non-zero
- **AND** it MUST NOT start the risk write path or the accounting worker

#### Scenario: Stop-then-start hands over cleanly

- **WHEN** the running automation instance is stopped and a new one is started
- **THEN** the released lock MUST be acquirable by the new instance
- **AND** risk state and counters MUST be reloaded from the database on startup

#### Scenario: Lost lock is not downgraded to unlocked writing

- **WHEN** the lock-holding database connection drops while the process keeps running
- **THEN** the process MUST stop dispatching new interaction commands and MUST alert
- **AND** it MUST NOT continue writing `risk_state`

#### Scenario: Missing execution target disables the writer

- **WHEN** the deployment target environment value is absent or not `dev`/`ol`
- **THEN** the process MUST NOT acquire a writer lock and MUST NOT enable the risk write path
- **AND** the refusal MUST be visible in startup logs rather than silent

### Requirement: Background components must be classified single-instance or multi-instance

Every background component that owns mutable runtime state SHALL be classified as either single-instance or multi-instance, and the classification SHALL be recorded in the cloud decomposition documentation before the component is deployed as a separate process. A component MUST NOT be run in more than one instance per `executionTarget` unless it is classified multi-instance.

A component MAY be classified multi-instance only when all four properties hold: durable claim token, claim lease with expiry, skip-locked claim selection, and `executionTarget` filtering on create, claim, recover, and terminal write; plus claim recovery on process start. The reference implementations are the delegated-task worker and the content-schedule hour-cell claim.

Components whose authority lives in process memory MUST be classified single-instance. At minimum this covers: the risk controller host (in-memory state and sliding-window counters), the publish dispatcher (in-flight set, per-account serialization tail, open circuit breakers, with no dispatch-level claim in the publish ledger), the captcha assist service (in-memory incidents and recovery leases, whose assist links are only resolvable by the issuing process), and the edge connection runtime registry (per-connection WebSocket runtimes).

New background components MUST be classified before merge. An unclassified component MUST be treated as single-instance.

#### Scenario: New worker is classified before deployment

- **WHEN** a new background worker that scans, claims, retries, or recovers durable work is added
- **THEN** its classification MUST be recorded in the decomposition documentation before it is deployed as a separate process
- **AND** if unclassified, it MUST be operated as single-instance

#### Scenario: Multi-instance claim requires the full pattern

- **WHEN** a component is proposed as multi-instance while lacking a claim lease or `executionTarget` filtering
- **THEN** the classification MUST be rejected and the component MUST be operated as single-instance
- **AND** the missing property MUST be recorded rather than assumed harmless

#### Scenario: Memory-authoritative components are never replicated

- **WHEN** an operator considers running a second replica of the publish dispatcher, captcha assist, or connection runtime registry for the same target
- **THEN** the classification table MUST show them as single-instance and the second replica MUST NOT be started
