## ADDED Requirements

### Requirement: Every external action MUST have an immutable execution intent

Before dispatching a platform action, Execution Ledger SHALL persist an immutable intent containing account/environment/platform/execution target and binding revision, action and stable target, frozen content/approval/schedule fields, required capability/protocol version, Task/TaskRun/StepRun correlation, and a target-scoped idempotency key. Edge Gateway MUST dispatch from that intent rather than from mutable Task Runtime memory.

#### Scenario: Publish intent is prepared
- **WHEN** a publish StepRun passes Task Runtime and Policy-Risk admission
- **THEN** Ledger SHALL persist the exact candidate, target, visibility, schedule, binding, capability, and idempotency facts before any Edge command is sent

#### Scenario: Duplicate intent is requested
- **WHEN** the same business idempotency key is prepared again in the same execution target and active scope
- **THEN** Ledger SHALL return the existing intent/Attempt relationship or reject the duplicate and MUST NOT create a second platform action

### Requirement: Attempts MUST preserve external-write uncertainty

An Attempt SHALL progress from `prepared` to `dispatched`, then to `platform_confirmed`, `confirmed_not_applied`, or `submitted_unknown`; pre-dispatch policy/capability denial and cancellation SHALL use explicit blocked/cancelled outcomes. The system MUST NOT translate transport timeout, missing ack, page navigation, or process loss after dispatch into success or confirmed failure.

#### Scenario: Edge returns positive platform evidence
- **WHEN** Edge reports a schema-valid stable platform ID/URL, API receipt, or capability-approved post-action proof
- **THEN** Ledger SHALL settle the Attempt as `platform_confirmed` and preserve the evidence reference

#### Scenario: Connection drops after submit
- **WHEN** a submit command was dispatched and the Edge connection drops before an authoritative result
- **THEN** Ledger SHALL settle or retain the Attempt as `submitted_unknown` and MUST NOT dispatch the action again

#### Scenario: Pre-dispatch policy denies action
- **WHEN** live policy denies a prepared action before Gateway dispatch
- **THEN** Ledger SHALL record a blocked/not-dispatched outcome with the policy reason and no platform success

### Requirement: Platform confirmation MUST require action-specific durable evidence

Each platform capability SHALL define the evidence accepted for `platform_confirmed`. A WebSocket ack, command acceptance, click completion, approval decision, notification, Host event, or optimistic client state alone MUST NOT satisfy confirmation. Unknown or malformed evidence MUST preserve a non-confirmed outcome.

#### Scenario: Publish button click succeeds without public result
- **WHEN** Edge confirms the click but cannot capture a public post ID/URL or other approved evidence
- **THEN** the Attempt MUST remain submitted/unconfirmed or unknown according to the action contract

#### Scenario: Comment approval card is accepted
- **WHEN** a user approves a comment but no comment submit receipt exists
- **THEN** approval SHALL be recorded separately and the comment MUST NOT appear platform-confirmed

### Requirement: Reconciliation MUST be bounded and MUST NOT replay unknown writes

Reconciler SHALL process only Attempts requiring external-state reconciliation, use action-specific stable identifiers, account, time window, and content fingerprint, and enforce configured maximum checks/window. It MUST NOT retry the original irreversible action while its outcome is unknown. A unique positive match SHALL confirm; proof of absence SHALL mark not applied; ambiguous or multiple matches SHALL remain unknown and require attention.

#### Scenario: Reconciler finds a unique published post
- **WHEN** one platform post uniquely matches the Attempt's account, time window, content fingerprint, and stable evidence rules
- **THEN** Reconciler SHALL CAS the Attempt to `platform_confirmed` and emit one result event

#### Scenario: Reconciler finds multiple candidates
- **WHEN** more than one platform object could match the unknown Attempt
- **THEN** it MUST retain `submitted_unknown`, record the ambiguity, and MUST NOT choose one as success

#### Scenario: Reconciliation window expires
- **WHEN** all bounded checks complete without proof of success or absence
- **THEN** the Attempt SHALL remain visibly unknown and emit an attention-required event

### Requirement: Retries MUST create bounded Attempts only after non-application is known

Task Runtime MAY create another Attempt for the same intent only before initial dispatch or after the prior Attempt is `confirmed_not_applied`, while authorization, deadline, risk, capability, and retry bounds remain valid. Retry counts and reasons MUST be persisted; no implicit fallback or compatibility branch may add attempts.

#### Scenario: Edge rejects before action starts
- **WHEN** Edge provides authoritative evidence that the action was not applied and the retry contract allows one more attempt
- **THEN** Task Runtime MAY create a new Attempt under the same business idempotency scope after live re-admission

#### Scenario: Prior Attempt is unknown
- **WHEN** a Task Runtime retry timer fires for an Attempt in `submitted_unknown`
- **THEN** Ledger MUST reject redispatch and route the Attempt to reconciliation instead

### Requirement: Cancellation MUST not erase dispatched truth

An authorized cancellation before dispatch SHALL prevent dispatch and record a cancelled Attempt/intent. After dispatch, Ledger SHALL record `cancel_requested` without rewriting the Attempt's external outcome. Any deletion, withdrawal, or compensating platform write MUST be a new action with its own authorization, intent, Attempt, and evidence.

#### Scenario: Prepared comment is cancelled
- **WHEN** cancellation arrives before the comment command is dispatched
- **THEN** Ledger SHALL mark it cancelled and Gateway MUST never send it

#### Scenario: Published post is later removed
- **WHEN** a user wants to remove a platform-confirmed post
- **THEN** the system SHALL create a separately authorized delete/withdraw intent and MUST preserve the original publish confirmation

### Requirement: Gateway receipts MUST be capability-versioned, deduplicated, and target-scoped

Edge Gateway SHALL accept commands and receipts only for a valid handshake generation, account/environment binding, protocol version, capability declaration, execution target, TaskRun/StepRun/Attempt identity, and replay-protected command context. Unknown capability or version MUST return `unsupported`; duplicate receipts MUST be idempotent.

#### Scenario: Edge lacks required capability
- **WHEN** an intent requires `publish_x_v2` but the connected Edge declares only `publish_x_v1`
- **THEN** Gateway MUST refuse dispatch as unsupported and MUST NOT substitute the older command

#### Scenario: Receipt is replayed
- **WHEN** Gateway receives the same valid receipt more than once
- **THEN** Ledger SHALL apply it once and preserve a duplicate-receipt diagnostic without emitting duplicate business results

#### Scenario: OL receipt reaches DEV worker
- **WHEN** a receipt or Attempt identity belongs to a different execution target
- **THEN** the worker MUST reject it without mutating local-target lifecycle state
