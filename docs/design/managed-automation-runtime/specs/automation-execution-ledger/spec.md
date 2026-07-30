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

An Attempt SHALL progress from `prepared` to `dispatched`, then to `platform_confirmed`, `confirmed_not_applied`, `submitted_unknown`, or one of the additional post-dispatch outcomes required below (`accepted_pending`, `held_for_moderation`, `precondition_already_satisfied`); pre-dispatch policy/capability denial and cancellation SHALL use explicit blocked/cancelled outcomes carrying the typed non-start reason required below. The system MUST NOT translate transport timeout, missing ack, page navigation, or process loss after dispatch into success or confirmed failure.

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

### Requirement: Confirmation evidence MUST be observed, attributed, and vetoable

Evidence accepted for `platform_confirmed` MUST be independently derived from the acted-upon platform object: it MUST NOT be a value echoed from the dispatched command, MUST NOT be derived, templated, or reconstructed from identifiers the system already holds, and MUST come from the same observation used to make the judgement rather than a separate sampling. Evidence MUST be scoped to the acting account's own stable platform identity, to the submitted content, and to the intent's frozen target; when it cannot be uniquely attributed to that target, the Ledger MUST refuse business attribution and record a target-mismatch outcome while still counting the action for platform-risk accounting. A capability's confirmation contract MUST be able to declare veto signals: when a recognized not-yet-live or refused indicator is present on the scoped object, the Attempt MUST NOT settle as `platform_confirmed` even if otherwise-sufficient positive evidence is present. Weak page-state proxies — leaving the editor URL, a disabled-button heuristic — MUST NOT be accepted as confirmation, and confirmation MUST NOT be produced by relaxing match conditions or extending windows. When a required evidence field cannot be observed it SHALL be persisted as absent and surfaced as unavailable rather than synthesized.

#### Scenario: Receipt echoes the requested id
- **WHEN** a receipt's target identifier is the same value the command carried
- **THEN** it MUST NOT satisfy confirmation, because it proves only that the command was received

#### Scenario: Comment carries a real id but also a pending-moderation badge
- **WHEN** the posted comment node has a server-assigned id and interaction controls while also showing a recognized pending-review indicator
- **THEN** the veto signal MUST prevent `platform_confirmed`

#### Scenario: Post link cannot be captured
- **WHEN** the full usable detail URL cannot be observed after a confirmed publish
- **THEN** the link SHALL be stored as absent and surfaced as unavailable, and MUST NOT be assembled from a bare identifier

### Requirement: Attempt outcomes MUST preserve distinctions that determine recovery

Pre-dispatch non-start SHALL carry a typed reason derived from the recorded fact of whether the executor body ran and whether any platform command was sent, not from an enumerated allowlist of error codes; an unrecognized failure occurring before dispatch MUST default to the not-dispatched classification, and failures occurring after dispatch — including resource-release failures — MUST NOT be reclassified as not-dispatched. Distinct non-start reasons (unavailable executor, degraded browser control, acquisition timeout, resource-slot wait) MUST NOT be merged or relabelled, because only an explicit resource-wait reason MAY retain authorization for automatic retry. Beyond `platform_confirmed`, `confirmed_not_applied`, and `submitted_unknown`, the lifecycle MUST provide: an `accepted_pending` outcome for a request the platform accepted whose effect is not yet externally visible; a `held_for_moderation` outcome for a write accepted but withheld pending third-party human review; and a `precondition_already_satisfied` outcome for an attempt whose evidence shows the intended end state already held. `confirmed_not_applied` MUST distinguish "the write was never applied" from "the platform actively refused the write"; the refused case is terminal, is not eligible for automatic retry under the same intent, and MUST be routed to risk/attention. An Attempt settling as `submitted_unknown` MUST persist the strongest progress evidence observed before its window closed.

#### Scenario: Native scheduled publish is accepted
- **WHEN** the platform accepts a scheduled publish whose public object will not exist until its due time
- **THEN** the Attempt SHALL settle `accepted_pending`; its internal receipt MUST NOT be exposed as a public id or link and MUST NOT consume publish quota at submission time (its platform-risk consumption is recorded once the effect becomes externally live), and only a due-time bounded reconciliation observing the public object may confirm it

#### Scenario: Follow target is already followed
- **WHEN** evidence shows the account already follows the target
- **THEN** the outcome SHALL be `precondition_already_satisfied`, counting no new action, resetting no interval, and MUST NOT be treated as `confirmed_not_applied` for retry purposes

#### Scenario: Browser control is unhealthy while the client is online
- **WHEN** page automation cannot be acquired because browser control is degraded rather than because no slot is free
- **THEN** the reason MUST be recorded as degraded control and MUST NOT be presented as an offline executor or a resource-slot wait

### Requirement: Recording an actuated fact MUST be unconditional

Once an Attempt reaches a state evidencing that a real platform action occurred, the Ledger SHALL record that fact and its accounting effects unconditionally. It MUST NOT re-evaluate policy, risk, quota, or authorization when settling an Attempt, and a state change occurring after dispatch MUST NOT erase or suppress the record of what already happened. Live admission applies only before dispatch. If a consumption fact cannot be durably enqueued, the system MUST alert and stop dispatching further automatic actions for that account rather than proceeding as if nothing happened; retries SHALL be bounded and exhausted records SHALL become visible dead letters.

#### Scenario: Quota fills while a receipt is in flight
- **WHEN** an action's receipt arrives after the account's quota has been exhausted
- **THEN** the action MUST still be recorded, because re-judging admission at settle time destroys only the evidence, not the action

### Requirement: Idempotency and retry preconditions MUST cover attempts, completed work, and residual state

Duplicate suppression SHALL cover attempts, not only successful writes: for a target committed by a run whose submit capability was admitted, a non-success terminal outcome (approval rejected, validator rejected, failed, timed out) MUST suppress that target from re-selection for a bounded configurable window. A rehearsal run whose submit capability was denied creates no Attempt and MUST NOT write such a suppression, so rehearsing cannot consume the production target pool, and re-selection afterwards MUST be an explicit traced decision. A target with an outstanding `submitted_unknown` Attempt MUST NOT receive a new intent until that Attempt is settled. Idempotency MUST also cover records that already reached terminal success, and the business idempotency key MUST be anchored to the identity of the approved artifact and to platform-stable identifiers; a binding MUST NOT derive a key at a granularity that lets the same approved artifact be authorized twice. Before dispatching a new Attempt for an intent whose previous Attempt was cancelled or preempted after partial composition, the executor SHALL verify that the platform-side authoring surface is in a clean starting state and MUST NOT append onto residual draft state.

#### Scenario: The same approved draft is authorized twice
- **WHEN** an already-published record's identifier is authorized again
- **THEN** the Ledger MUST NOT create a second platform action, whether or not its original scope is still active

#### Scenario: Retry after a preempted half-filled composer
- **WHEN** a new Attempt is created for an intent whose composer was left partially filled
- **THEN** the starting surface MUST be verified clean, because appending would produce duplicated body text as a "successful" post

### Requirement: Frozen intent MUST be applied verbatim and confirmed against its field set

An executor SHALL apply frozen intent content byte-for-byte and MUST NOT perform its own truncation, clamping, reformatting, or rewriting of approved content; the value recorded, the value dispatched, the value shown to the approver, and the value that reaches the platform MUST be the same string. Any system-side normalization that changes approved bytes MUST invalidate the matching approval and require an explicit re-authorization of the normalized bytes before dispatch. Platform confirmation MUST verify that the observed result matches the frozen intent's field set: an execution that silently dropped a frozen field (such as attached media) MUST NOT settle as `platform_confirmed`, and the persisted record MUST be corrected to reflect what actually happened. An authorization credential MUST anchor to the content version rendered to the approver rather than a version re-read at click time, and version agreement is the sole fidelity gate — provenance or signature fields MUST NOT substitute for it.

#### Scenario: Executor truncates an approved title
- **WHEN** an executor applies its own length limit to approved content
- **THEN** this MUST be rejected as a contract violation, because the record would no longer equal what the platform shows

#### Scenario: Images are dropped by the executing path
- **WHEN** a publish intent carrying media is executed by a path that cannot attach media
- **THEN** the Attempt MUST NOT be confirmed as success and the record MUST show media as not attached

### Requirement: Gateway admission MUST separate transport facts from business readiness

Gateway admission SHALL depend only on transport-level facts (node identity, account/environment binding, protocol version, capability declaration, execution target). Missing persona, inactive plan, exhausted quota or budget, unsupported business capability, and business-runtime construction failures MUST NOT be returned as handshake errors and MUST NOT close or refuse the connection; the affected business actions SHALL instead fail closed with their own named reasons while the connection stays routable. Every node identity SHALL be unique per environment and stable across restarts, derived from an authoritative environment key rather than a host-derived constant; a node that cannot derive one MUST refuse to start, and a handshake whose node identity is already held by a live connection bound to a different environment or account MUST be rejected rather than treated as a reconnect replacement. When a new connection legitimately claims an existing node identity, Gateway SHALL close the incumbent only after the candidate has completed a successful handshake and entered the routing registry. Connection presence, declared capability, and command delivery are three separate facts and MUST NOT be inferred from one another: an executor that loses a declared capability mid-connection MUST withdraw it or close, and a command accepted by the transport with no live consumer MUST fail with an explicit undelivered reason rather than be silently queued or counted as dispatched. Capability negotiation SHALL cover the execution substrate as well as the command set: when the declared fingerprint profile, egress identity, or profile-bound platform login cannot be delivered, the Edge MUST fail honestly and MUST NOT start, report readiness, or fall back to a different substrate.

#### Scenario: Account has no persona
- **WHEN** an Edge connects for an account whose persona is missing
- **THEN** the handshake MUST succeed and the persona-dependent actions MUST fail closed with their own reason, rather than the connection being refused into a reconnect storm

#### Scenario: Browser control dies while the connection stays up
- **WHEN** page automation becomes impossible on a still-connected Edge
- **THEN** that capability MUST be withdrawn so admission stops routing page work to it

#### Scenario: Fingerprint profile cannot be delivered
- **WHEN** the declared profile or egress identity is unavailable at startup
- **THEN** the Edge MUST refuse to start and MUST NOT fall back to a local browser with the machine's real fingerprint and egress

### Requirement: Directed dispatch MUST NOT fan out

Directed Gateway dispatch SHALL deliver only to the single resolved target connection. A dispatch whose target is missing or unresolved MUST reach zero connections, MUST report an honest zero-delivery result with a warning, and MUST NOT fan out to any other connection; any all-connections broadcast SHALL require a distinct, explicitly named operation and MUST NOT be reachable by omitting a target. When one account has multiple simultaneously valid connections, dispatch SHALL select a deterministic single recipient and record that selection. Command payloads MUST NOT be transmitted to connections belonging to another account or customer, even when those connections would reject them on receipt.

#### Scenario: Target resolution fails
- **WHEN** a command's target account has no resolvable connection
- **THEN** delivery count MUST be zero with a warning, not a fan-out to every online connection

#### Scenario: One account has two live connections
- **WHEN** two valid connections exist for the same account
- **THEN** a deterministic single recipient SHALL be chosen and logged, rather than either connection receiving the command non-deterministically

### Requirement: The account consumption ledger MUST NOT be partitioned by execution target

The per-account platform-risk consumption ledger SHALL be a single append-only record set that is not partitioned by `execution_target` and carries no ownership predicate. A receipt whose account ownership changed in flight SHALL still be recorded into that single ledger. Target isolation applies to lifecycle state, claims, scans, recovery, and idempotency scopes, and MUST NOT be extended to the consumption ledger, because the platform observes one account's total activity regardless of which deployment target issued it.

#### Scenario: Account moves from DEV to OL
- **WHEN** an account's ownership changes while a receipt is in flight
- **THEN** the consumption fact SHALL be appended to the same account ledger, and the account MUST NOT receive a fresh daily allowance as a result of the move
