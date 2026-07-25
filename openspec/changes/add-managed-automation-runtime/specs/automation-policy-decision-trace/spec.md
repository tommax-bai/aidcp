## ADDED Requirements

### Requirement: Full-managed authorization MUST be action-scoped and visible

API SHALL expose customer-controlled authorization separately for at least research/read, light interaction, proactive comment, inbound reply, content creation, publish submission, and direct/contact messaging. Automation SHALL normalize each action domain to `disabled`, `require_approval`, or `standing_authorized`. It MUST NOT infer authorization for one domain from another or from one global full-managed Boolean.

#### Scenario: Read is authorized but comments require review
- **WHEN** a plan has standing authorization for research/read and requires approval for proactive comments
- **THEN** Automation MAY perform admitted search/browse work but MUST wait for a matching approval before each comment commit

#### Scenario: Publish is disabled
- **WHEN** content creation succeeds while `publish.submit` is disabled
- **THEN** the system MAY retain the candidate but MUST NOT create a publish Attempt

#### Scenario: Client claims auto approval
- **WHEN** an untrusted client payload requests `standing_authorized` without an API-owned authorization revision
- **THEN** Automation MUST ignore or reject the claim and MUST NOT dispatch the action

### Requirement: Irreversible actions MUST pass plan-time and commit-time admission

Policy-Risk SHALL validate Definition/action scope/budget when a Run is created and SHALL revalidate customer stop/pause, account binding and page identity, authorization revision, required capability, RiskController, quota, cooldown, duplicate target, content/approval revisions, and schedule deadline immediately before irreversible dispatch. A standing authorization MUST NOT bypass any live safety gate.

#### Scenario: Risk state changes while waiting
- **WHEN** a standing-authorized comment waits for account work and RiskController later denies comments
- **THEN** commit-time admission MUST block dispatch with the current risk reason

#### Scenario: All live gates pass
- **WHEN** a frozen action remains authorized, in window, within budget, correctly bound, capability-supported, and risk-allowed
- **THEN** Policy-Risk MAY admit creation of the dispatchable Execution Attempt

### Requirement: Approval, dispatch, confirmation, and notification MUST remain separate

An approval decision SHALL authorize a matching frozen intent but MUST NOT imply dispatch or platform success. A notification SHALL be best-effort observability only: failure MUST NOT revoke standing authorization, block/delay dispatch, or fall back to an approval workflow. A `require_approval` path with missing, expired, mismatched, rejected, or unavailable approval MUST fail closed.

#### Scenario: Auto-approval notification fails
- **WHEN** a standing-authorized comment's informational notification cannot be delivered
- **THEN** the failure SHALL be traced/observed while the normal risk and commit path continues unchanged

#### Scenario: Review approval is missing
- **WHEN** a comment requires review and no valid matching approval arrives before its deadline
- **THEN** the action MUST terminate waiting/skipped/cancelled according to policy and MUST NOT be submitted

#### Scenario: Approval exists but Edge is offline
- **WHEN** immutable publish content remains approved and Edge is temporarily offline within `latestStartAt`
- **THEN** the Run MAY wait for Edge while displaying approved-but-not-dispatched, and MUST NOT display published

### Requirement: Platform, execution, and AI budgets MUST be independent

ManagedPlan/Cycle/Run admission SHALL track separate platform-risk budgets, execution-resource budgets, and AI/content-cost budgets. Exhausting one budget MUST block or end the affected work even when another budget remains. Budget allocation, reservation, consumption, release, and denial reason MUST be observable.

#### Scenario: AI budget is exhausted
- **WHEN** a cycle has remaining platform actions but no remaining authorized creation cost
- **THEN** new creation Steps MUST be skipped/denied while unrelated already-authored and otherwise authorized work MAY continue

#### Scenario: Browser budget is exhausted
- **WHEN** research reaches its browser-minute bound before its requested content count
- **THEN** the Step SHALL stop with actual progress and MUST NOT consume extra browser time because platform quota remains

#### Scenario: Comment quota is exhausted
- **WHEN** execution and AI budgets remain but the account comment quota is exhausted
- **THEN** proactive comments MUST be denied by Policy-Risk

### Requirement: Decision Trace MUST explain consequential choices without replacing state

Trigger, Cycle, Workflow, Arbiter, Policy-Risk, Ledger, and Reconciler SHALL append structured Decision Trace records for creation, selection, admission, delay, denial, skip, supersession, dispatch, and reconciliation decisions. Each record MUST carry correlation/causation and relevant Plan/Definition/persona/policy/risk/budget version references, reason code, input references, and affected Run/Step/Attempt. Trace records MUST NOT mutate or override authoritative lifecycle state.

#### Scenario: User asks why only 23 items were read
- **WHEN** a research Run stops below its requested count
- **THEN** the API projection SHALL be able to show actual count and a trace-derived reason such as content exhaustion, deadline, Edge unavailability, or budget limit

#### Scenario: Trace disagrees with Ledger
- **WHEN** a stale or malformed trace says an action succeeded but Ledger has no platform confirmation
- **THEN** customer-visible result MUST follow Ledger and the trace inconsistency SHALL be observable

### Requirement: Platform content and Agent output MUST be treated as untrusted input

Platform posts, comments, messages, DOM text, model output, and Agent proposals MUST pass schema validation, capability/action allowlists, authorization, and policy checks before they influence executable work. Text from those sources MUST NOT be interpreted as an Automation Definition, raw tool call, Edge command, credential request, or authorization grant.

#### Scenario: Platform post contains tool instructions
- **WHEN** browsed content asks the Agent to call a tool or publish a message
- **THEN** the text MAY be assessed as content but MUST NOT create an executable action outside a registered and authorized Definition

#### Scenario: Agent returns an unknown action
- **WHEN** an Agent PlanPatch contains a step or action outside the registered schema
- **THEN** the patch MUST be rejected and traced without forwarding it to Edge

### Requirement: Client projections MUST distinguish local, durable, and confirmed truth

Customer-facing projections SHALL distinguish Edge Host local runtime state, Automation durable Run/Step/wait state, and platform-confirmed action result. Host events and user-level realtime notifications MAY invalidate/refetch API data but MUST NOT directly assert business success. Before first successful API read, clients MUST show unknown/loading/failure rather than fabricated zero or success.

#### Scenario: Host reports command completion
- **WHEN** Classic receives a local Host event but Automation Ledger still shows `submitted_unknown`
- **THEN** the client SHALL show the durable unknown result after API refetch and MUST NOT show platform-confirmed success

#### Scenario: Automation waits while Host is stopped
- **WHEN** a Run is `waiting_for_edge` and the local Host is stopped
- **THEN** the client MAY show both facts separately and starting Host MUST only trigger a new handshake, not mark the Run complete

### Requirement: Trace and evidence retention MUST be purpose-limited and revocable

Automation SHALL define separate retention/access policies for third-party content snapshots, private messages, model inputs, Decision Trace summaries, execution evidence, and operational logs. It SHALL prefer stable references, hashes, reason codes, and minimal excerpts over indefinite full payload retention. Account offboarding or authorized deletion SHALL stop new work, cancel undispatched intents, revoke access, and apply each data owner's retention/deletion contract without erasing legally or operationally required action evidence prematurely.

#### Scenario: Account is offboarded
- **WHEN** API publishes an authoritative account offboarding event
- **THEN** Automation SHALL freeze new work, cancel undispatched intents, preserve dispatched-result reconciliation, and begin scoped retention/deletion processing

#### Scenario: Customer views a decision explanation
- **WHEN** a customer requests why an action was skipped
- **THEN** API SHALL return an authorized trace summary without exposing credentials, unrelated customer data, or unrestricted raw platform/private-message payloads
