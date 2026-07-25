## ADDED Requirements

### Requirement: Full-managed authorization MUST be action-scoped and visible

API SHALL expose customer-controlled authorization separately for at least research/read, light interaction, proactive comment, inbound reply, content creation, publish submission, and direct/contact messaging. Automation SHALL normalize each action domain to `disabled`, `require_approval`, `standing_authorized`, or the synchronous-operator `operator_override` class defined below. It MUST NOT infer authorization for one domain from another or from one global full-managed Boolean.

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

Policy-Risk SHALL validate TaskDefinition/action scope/budget when a TaskRun is created and SHALL revalidate customer stop/pause, account binding and page identity, authorization revision, required capability, RiskController, quota, cooldown, duplicate target, content/approval revisions, and schedule deadline immediately before irreversible dispatch. A standing authorization MUST NOT bypass any live safety gate.

#### Scenario: Risk state changes while waiting
- **WHEN** a standing-authorized comment waits for account work and RiskController later denies comments
- **THEN** commit-time admission MUST block dispatch with the current risk reason

#### Scenario: All live gates pass
- **WHEN** a frozen action remains authorized, in window, within budget, correctly bound, capability-supported, and risk-allowed
- **THEN** Policy-Risk MAY admit creation of the dispatchable Execution Attempt

### Requirement: Approval, dispatch, confirmation, and notification MUST remain separate

An approval decision SHALL authorize a matching frozen intent but MUST NOT imply dispatch or platform success. A **post-dispatch result** notification SHALL be best-effort observability only: its failure MUST NOT revoke standing authorization, retroactively invalidate a dispatched action, or fall back to an approval workflow. A **pre-dispatch notice that substitutes for human review** is part of the authorization path instead, and is governed by the operator-visible delivery requirement below rather than by this best-effort rule. A `require_approval` path with missing, expired, mismatched, rejected, or unavailable approval MUST fail closed.

#### Scenario: Post-dispatch result notification fails
- **WHEN** the informational result notification for an already-dispatched standing-authorized comment cannot be delivered
- **THEN** the failure SHALL be traced/observed while the dispatched Attempt's receipt and reconciliation path continues unchanged

#### Scenario: Review approval is missing
- **WHEN** a comment requires review and no valid matching approval arrives before its deadline
- **THEN** the action MUST terminate waiting/skipped/cancelled according to policy and MUST NOT be submitted

#### Scenario: Approval exists but Edge is offline
- **WHEN** immutable publish content remains approved and Edge is temporarily offline within `latestStartAt`
- **THEN** the TaskRun MAY wait for Edge while displaying approved-but-not-dispatched, and MUST NOT display published

### Requirement: Platform, execution, and AI budgets MUST be independent

ManagedPlan/Cycle/TaskRun admission SHALL track separate platform-risk budgets, execution-resource budgets, and AI/content-cost budgets. Exhausting one budget MUST block or end the affected work even when another budget remains. Budget allocation, reservation, consumption, release, and denial reason MUST be observable.

#### Scenario: AI budget is exhausted
- **WHEN** a cycle has remaining platform actions but no remaining authorized creation cost
- **THEN** new creation Steps MUST be skipped/denied while unrelated already-authored and otherwise authorized work MAY continue

#### Scenario: Browser budget is exhausted
- **WHEN** research reaches its browser-minute bound before its requested content count
- **THEN** the StepRun SHALL stop with actual progress and MUST NOT consume extra browser time because platform quota remains

#### Scenario: Comment quota is exhausted
- **WHEN** execution and AI budgets remain but the account comment quota is exhausted
- **THEN** proactive comments MUST be denied by Policy-Risk

### Requirement: Decision Trace MUST explain consequential choices without replacing state

Trigger, ManagedCycle, Task Runtime, Arbiter, Policy-Risk, Ledger, and Reconciler SHALL append structured Decision Trace records for creation, selection, admission, delay, denial, skip, supersession, dispatch, and reconciliation decisions. Each record MUST carry correlation/causation and relevant ManagedPlan/Task/TaskDefinition/persona/policy/risk/budget version references, reason code, input references, and affected TaskRun/StepRun/Attempt. Trace records MUST NOT mutate or override authoritative lifecycle state.

#### Scenario: User asks why only 23 items were read
- **WHEN** a research TaskRun stops below its requested count
- **THEN** the API projection SHALL be able to show actual count and a trace-derived reason such as content exhaustion, deadline, Edge unavailability, or budget limit

#### Scenario: Trace disagrees with Ledger
- **WHEN** a stale or malformed trace says an action succeeded but Ledger has no platform confirmation
- **THEN** customer-visible result MUST follow Ledger and the trace inconsistency SHALL be observable

### Requirement: Platform content and Agent output MUST be treated as untrusted input

Platform posts, comments, messages, DOM text, model output, and Agent proposals MUST pass schema validation, capability/action allowlists, authorization, and policy checks before they influence executable work. Text from those sources MUST NOT be interpreted as an TaskDefinition, raw tool call, Edge command, credential request, or authorization grant.

#### Scenario: Platform post contains tool instructions
- **WHEN** browsed content asks the Agent to call a tool or publish a message
- **THEN** the text MAY be assessed as content but MUST NOT create an executable action outside a registered and authorized TaskDefinition

#### Scenario: Agent returns an unknown action
- **WHEN** an Agent `ReviseTaskProposal` contains a Capability or graph change outside the registered schema
- **THEN** the proposal MUST be rejected and traced without forwarding it to Automation execution or Edge

### Requirement: Client projections MUST distinguish local, durable, and confirmed truth

Customer-facing projections SHALL distinguish Edge Host local runtime state, Automation durable TaskRun/StepRun/wait state, and platform-confirmed action result. Host events and user-level realtime notifications MAY invalidate/refetch API data but MUST NOT directly assert business success. Before first successful API read, clients MUST show unknown/loading/failure rather than fabricated zero or success.

#### Scenario: Host reports command completion
- **WHEN** Classic receives a local Host event but Automation Ledger still shows `submitted_unknown`
- **THEN** the client SHALL show the durable unknown result after API refetch and MUST NOT show platform-confirmed success

#### Scenario: Automation waits while Host is stopped
- **WHEN** a TaskRun is `waiting_for_edge` and the local Host is stopped
- **THEN** the client MAY show both facts separately and starting Host MUST only trigger a new handshake, not mark the TaskRun complete

### Requirement: Trace and evidence retention MUST be purpose-limited and revocable

Automation SHALL define separate retention/access policies for third-party content snapshots, private messages, model inputs, Decision Trace summaries, execution evidence, and operational logs. It SHALL prefer stable references, hashes, reason codes, and minimal excerpts over indefinite full payload retention. Account offboarding or authorized deletion SHALL stop new work, cancel undispatched intents, revoke access, and apply each data owner's retention/deletion contract without erasing legally or operationally required action evidence prematurely.

#### Scenario: Account is offboarded
- **WHEN** API publishes an authoritative account offboarding event
- **THEN** Automation SHALL freeze new work, cancel undispatched intents, preserve dispatched-result reconciliation, and begin scoped retention/deletion processing

#### Scenario: Customer views a decision explanation
- **WHEN** a customer requests why an action was skipped
- **THEN** API SHALL return an authorized trace summary without exposing credentials, unrelated customer data, or unrestricted raw platform/private-message payloads

### Requirement: Admission gates MUST be classified, and an absolute prohibition set MUST be unliftable

Admission gates SHALL be classified as soft pacing gates (session soft budgets, cooldowns, human-likeness throttles) or hard safety gates (RiskController state, platform quota, authorization, target identity, content safety). Authorization SHALL model an explicit `operator_override` class distinct from `standing_authorized`: it MAY skip named soft gates and, where the product has so ruled, specified quota gates, with a recorded operator authorization revision; it MUST NOT skip human approval, content-safety validation, fact recording, or honest non-success reporting, and it MUST NOT be silently downgraded to blocked or deferred. The override signal SHALL be settable only at a synchronous operator entry point and MUST NOT propagate to batched, scheduled, or asynchronous derived work. Policy-Risk SHALL additionally enforce a persona-independent and customer-independent content prohibition set; a prohibited-content match MUST deny regardless of CapabilityScope, standing authorization, approval, exemption, or task parameters, and no configuration path may grant an exception. Where a known exemption exists, it MUST be recorded as an exemption and MUST NOT be documented as full gate coverage.

#### Scenario: Operator commands on a restricted account
- **WHEN** an operator issues a precise single-shot command for an account whose quota is spent
- **THEN** the command MAY proceed under `operator_override` while its human-approval and content-safety gates still apply and its consumption is still recorded

#### Scenario: Override is used to drive a batch
- **WHEN** an operator override is attached to work that fans out into many derived actions
- **THEN** the override MUST NOT apply to the derived actions

#### Scenario: Standing authorization meets prohibited content
- **WHEN** a fully authorized plan encounters content in the global prohibition set
- **THEN** the action MUST be denied and no configuration may permit it

### Requirement: Authorization MUST be trigger-path scoped and floored by capability minimums

An authorization revision SHALL bind an action domain to a specific trigger path (schedule, manual/operator, inbound event, or Agent intent). Automation MUST NOT apply a standing authorization granted for one trigger path to work created by a different trigger path; unauthorized paths SHALL fall back to `require_approval`. Each CapabilityDefinition MAY declare a minimum approval level for its action; effective authorization SHALL be the stricter of the capability's declared minimum and the customer's authorization, a customer-level standing authorization MUST NOT lower a capability-mandated `require_approval`, and an unsatisfiable combination MUST fail closed. A shared implementation serving several platforms MUST NOT apply one platform's looser authorization to another.

#### Scenario: Schedule is unattended but manual is not
- **WHEN** an account's scheduled comments are standing-authorized
- **THEN** an operator-issued comment for the same action domain MUST still follow its own approval requirement

#### Scenario: Platform is still in restricted rollout
- **WHEN** a capability declares a minimum of `require_approval` and the customer sets `standing_authorized`
- **THEN** the effective authorization remains `require_approval`

### Requirement: Missing or unresolvable policy inputs MUST resolve to declared safe defaults

For every policy input — authorization, budgets, quotas, ramp curves, operating configuration, account status, per-account operating rows — the behaviour on missing, invalid, or unconfirmable values SHALL be declared explicitly and observably annotated. A missing authorization or enablement configuration MUST resolve to `disabled`, and every newly wired external-write capability MUST have an operator kill switch defaulting to off whose disabled state prevents dispatch, risk/quota recording, and any claim that work occurred. A missing operational threshold MUST fall back per-field to a hard-coded safe default: it MUST NOT disable the affected work and MUST NOT fall back to an unbounded value. Absence MUST NOT be interpreted as "unlimited", MUST NOT disable a gate, and MUST NOT be resolved by substituting a plausible value from a different scope, platform, or account; an absent explicit status MUST NOT default to the permissive value. Recovery from a missing configuration SHALL require an explicit, default-off initialization rather than automatic synthesis. Admission SHALL distinguish an explicit `unsupported` capability declaration, which MUST deny, from a capability-resolution failure, which MUST NOT silently narrow a previously working capability set — it SHALL preserve the prior admitted behaviour or fail with an operator-visible degradation signal, and MUST NOT be recorded as a normal policy denial. This differs from trust-critical configuration such as `execution_target`, whose absence MUST disable the worker.

#### Scenario: Quota row is missing for an action
- **WHEN** no quota configuration exists for an action
- **THEN** admission SHALL use the hard-coded conservative default and MUST NOT treat the action as unlimited or block the account entirely

#### Scenario: Paused account row loses its status
- **WHEN** an account row has no explicit status
- **THEN** it MUST NOT default to active, so an intentionally paused account cannot silently revive on restart

#### Scenario: Capability lookup throws
- **WHEN** the capability registry cannot be resolved for a platform that was working
- **THEN** prior admitted behaviour SHALL be preserved with an operator-visible degradation signal, rather than every action on that platform silently failing closed

### Requirement: Safety signals MUST carry confidence and be calibrated for asymmetric cost

A blocking or throttling signal SHALL carry a declared confidence tier, and the gate polarity and threshold for each tier SHALL be calibrated against the asymmetric cost of false positives and false negatives. A lowest-confidence observation MUST require persistence confirmation across observations before it may be reported, advance account state, or suspend dispatch; a high-confidence identified blocker (captcha, login wall) MUST fail closed immediately without waiting for that confirmation. Detection criteria MUST be specific enough that a single transient page cannot convict an account, and recall MUST NOT be increased by loosening the evidence threshold. The blast radius of an observed obstruction MUST match its true scope: an item-level restriction MUST NOT be escalated to an account-level incident. Admission SHALL support an inconclusive third state that neither convicts nor heals: an inconclusive check MUST NOT count toward a failure debounce, MUST NOT be recorded as healthy, MUST NOT reset a baseline, and MUST leave an observable record rather than a silent no-op. An unclassifiable failure MUST default to the most recoverable class and MUST NOT default to a terminal one; an unknown denial reason from a safety read MUST fail closed.

#### Scenario: A transient overlay appears once
- **WHEN** a lowest-confidence obstruction indicator is seen in one observation and gone in the next
- **THEN** it MUST NOT be reported, MUST NOT advance risk state, and MUST NOT suspend dispatch

#### Scenario: Identity cannot be confirmed this round
- **WHEN** the page cannot be brought to a surface where account identity is readable
- **THEN** the round SHALL be inconclusive: neither a logout verdict nor a health confirmation, and it MUST leave an observable record

### Requirement: Suppressions MUST self-expire and MUST admit their own remedy

Every suppression, degradation, or circuit-open state SHALL carry a bounded wall-clock expiry that does not depend on any external wiring, and each degradation MUST schedule a bounded-backoff recovery whose backoff MUST NOT grow without limit and whose recovery channel MUST NOT reach zero. Only a failure that is structurally impossible to retry MAY enter a state with no automatic recovery, and each such state MUST have a named human entry point. A suppression that blocks an account MUST admit the actions required to clear it: the pass-through allowlist MUST be narrowly enumerated to the clearing path and MUST NOT be generalized to all control commands. A suppression signal and its release MUST be paired: a suppressed observation that was never reported MUST NOT emit an orphan release, and an orphan release MUST NOT lift a suppression. De-escalation MUST NOT follow automatically from the disappearance of the triggering signal; it SHALL be driven by the state machine's recovery window or an explicit operator action. Resolving or acknowledging an alert record MUST NOT clear the underlying runtime condition, resume a suspended resource, or write account risk state; a projection or configuration surface MUST NOT clear a suppression as a side effect of being read or edited.

#### Scenario: Account is paused pending captcha
- **WHEN** an account is suppressed by a captcha incident
- **THEN** the captcha-assist and session-end paths MUST still be deliverable to it, otherwise the suppression is a deadlock

#### Scenario: An endpoint circuit is opened
- **WHEN** a capability is degraded after repeated upstream failures
- **THEN** the degradation MUST carry an expiry after which it lapses without operator action, and a projection MUST NOT report an expired circuit as still open

#### Scenario: Operator ticks an alert closed
- **WHEN** an operator marks a blocking alert resolved
- **THEN** only the alert record changes; the account's suspension, risk state, and resource holds MUST be unaffected

### Requirement: Live identity and evidence prerequisites MUST be verified before acting

Before any page operation on behalf of an account — including read-only browsing, deep read, and evidence collection — the executor SHALL read the live page identity and compare it with the expected account, and MUST NOT substitute a stored binding revision, an online connection, or a prior admission for that check; a mismatch SHALL fail closed before any content fact is recorded. Commit-time admission MUST additionally verify that the prerequisites for the capability's required confirmation evidence are satisfiable before dispatch; when they are not, the action MUST be refused with an honest non-dispatch reason rather than dispatched into a guaranteed-unknown outcome. Verification of the target's identity for an irreversible write MUST be performed in the executor on the surface where the write will occur, not solely by re-reading the target's existence through an owning-domain interface.

#### Scenario: Browsing believes it is on account A
- **WHEN** the browser is actually authenticated as another account
- **THEN** no browse, deep-read, or de-duplication fact may be recorded, regardless of whether any write is planned

#### Scenario: Own platform identity is unknown before a comment
- **WHEN** the acting account's own stable platform identity — required to scope the comment's confirmation evidence — cannot be read
- **THEN** the submission MUST be refused rather than dispatched into an outcome that can never be confirmed

### Requirement: Rejected input MUST NOT be partially executed or silently substituted

Model and Agent outputs that select among supplied candidates SHALL be validated against the exact candidate set of that invocation, not only against a schema; an out-of-range, fabricated, or validator-rejected output MUST terminate that step with a distinguishable honest reason and MUST NOT be silently replaced by a default candidate, a fabricated query, or template text. When a compound authorized instruction contains an invalid component, the whole instruction MUST be rejected with a named validation error; partial execution of the valid components, and silent widening of a rejected narrow scope into a broader one, are prohibited. When a proposal or command resolves an entity reference (account, environment, target container) to zero or more than one authoritative object, the system MUST reject it with an honest ambiguity reason listing candidates and MUST NOT select a default, most-likely, or arbitrary object; Agent output MUST NOT be the resolver of such references.

#### Scenario: Model returns an out-of-range card index
- **WHEN** a selector model returns an index outside this invocation's candidate set
- **THEN** the step MUST end honestly and MUST NOT fall back to the first candidate

#### Scenario: Nickname matches two accounts
- **WHEN** an operator command names an account that matches more than one record
- **THEN** the command MUST be rejected with the candidate list rather than executed against a guess

### Requirement: Operator-visible delivery MUST be part of the authorization path where it substitutes for review

For an action executed under standing authorization without per-action human review, the system MUST successfully deliver a human-visible pre-dispatch notice carrying the account, target, and frozen content before dispatch; if that channel is unwired or delivery fails, the action MUST fail closed with an honest non-dispatch outcome. Delivery of an approval request SHALL likewise be part of the approval path: a failed delivery MUST be recorded as undelivered and raised as an attention-required condition rather than presented as a normal waiting-for-approval state. Every non-success terminal outcome SHALL produce exactly one operator-visible result notification, including deadline-expiry terminals and failures occurring before any Attempt is prepared; a terminal already reported by an owning downstream path MUST NOT be reported twice, and an unchanged reconciliation pass MUST NOT emit a new notification. When admission was granted through a relaxed, fallback, or degraded path, that fact and the specific unmet constraint MUST be carried into the approval surface and the Decision Trace. Only post-dispatch informational notifications are best-effort observability. Suppression or de-duplication of notifications MUST NOT suppress the durable record of the underlying fact, and its key MUST be at the same granularity as the event's semantic identity.

#### Scenario: Unattended comment's notice channel is down
- **WHEN** the pre-dispatch notice for a standing-authorized comment cannot be delivered
- **THEN** the comment MUST NOT be dispatched, because that notice is the only human-visible trace of an unreviewed action

#### Scenario: A run expires with no successes
- **WHEN** a TaskRun terminates on deadline expiry with zero successes and no downstream business notification
- **THEN** exactly one honest operator-visible result MUST be emitted

#### Scenario: Alert cooldown spans two blocker types
- **WHEN** one blocker type's alert is in cooldown and a different blocker type occurs
- **THEN** the second MUST still be recorded durably, and MUST NOT be swallowed by the first's cooldown key

### Requirement: Notification destinations MUST resolve by exact binding with complement fallback

Outbound notification and approval-card destinations SHALL be resolved through one shared resolver from an exact, explicitly stored binding; fuzzy or inferred destinations are prohibited. Unmatched, unbound, or failed resolution SHALL fall back by complement to a declared default destination with an observable configuration-gap record, and a message MUST NOT be silently dropped. Per-message-type allowlists MUST NOT be used to decide which messages may be routed, because a newly added message type would then be indistinguishable from an unwired one. A resolution error MUST NOT abort delivery of the surrounding batch.

#### Scenario: Account has a team binding that does not resolve
- **WHEN** an account carries a team key whose destination cannot be resolved
- **THEN** the message SHALL go to the default destination with a configuration-gap record, not be dropped and not be sent to a guessed destination

### Requirement: Approval waits MUST NOT be expired by scheduling timers

A wait for a human approval decision MUST NOT be terminated, reclassified, or discarded by any timer: only an approval decision or an explicit operator rejection SHALL advance it, and expiry of a dispatch window SHALL at most withdraw the current execution authorization while leaving the content re-approvable. When commit-time admission denies a prepared intent with no platform side effect, the system SHALL invalidate only the stale authorization and MUST keep the underlying approved content in a re-approvable pending state; such a denial MUST NOT be recorded as a terminal failed or discarded outcome.

#### Scenario: Draft sits unreviewed past its dispatch window
- **WHEN** an approval has not arrived when `latestStartAt` passes
- **THEN** the execution authorization MAY be withdrawn while the content remains pending and re-approvable, and it MUST NOT be auto-published, auto-discarded, or reclassified as failed

### Requirement: Budget consumption MUST be keyed on platform engagement

Platform-risk budgets and account quotas SHALL be consumed by every Attempt that reached `dispatched` — including `submitted_unknown`, `accepted_pending`, `held_for_moderation`, and later `confirmed_not_applied` outcomes — not only by `platform_confirmed` ones; a consumed-but-unconfirmed action MUST NOT be reported as a completed action on any success surface. An action denied before dispatch MUST NOT consume any budget, and work that terminated before its executor body ran MUST release its reservation and its schedule slot, while work that ran and honestly declined to write MUST still consume its allocation. All such counters MUST derive from durable records and MUST NOT rely on in-process counters that reset on restart; any in-memory counter used for admission SHALL be periodically reconciled against its durable source with a zero-divergence criterion, alerting and rebuilding from the durable source on any divergence. The window definition used by the gate, the remaining amount, the release time, and every projection of them MUST be identical. Accounting-failure polarity SHALL be declared per ledger class: a safety/consumption ledger write failure MUST halt further automatic actions for that account, while a cost/metrics ledger write failure MUST NOT block, delay, or propagate into the calling path, and a non-idempotent accumulating write MUST NOT be retried.

#### Scenario: Comment is dispatched but never confirmed
- **WHEN** a comment reaches `submitted_unknown`
- **THEN** it MUST consume the account's comment quota while remaining unreported as a completed comment

#### Scenario: Executor never started
- **WHEN** a scheduled work item ends before its executor body runs
- **THEN** its reservation and hour slot MUST be released rather than burned with zero actions

#### Scenario: Cost accounting backend is slow
- **WHEN** the token-usage ledger cannot be written
- **THEN** the model call path MUST NOT be blocked or failed, and the failed increment MUST NOT be retried into a double count

### Requirement: Rate-limit backstops MUST be provably looser than configured quotas

Where a rate-limit backstop (minimum interval, restart quiet period) coexists with a configurable quota, the backstop SHALL be provably looser than the quota for every action, tier, and window, enforced arithmetically at the single value-resolution point rather than by review. No derived transform (scaling, clamping, ramping, rounding) may reduce a positive configured allowance to zero or make a configured quota unreachable. Where a backstop discards rather than queues suppressed intents, that discard is acceptable only while the backstop is provably looser; if it becomes the binding constraint in any window, it MUST be changed to queue. The combined worst-case daily exposure across actions sharing one account MUST be a considered value rather than the sum of independently exhausted quotas.

#### Scenario: Cooldown equals the hourly quota interval
- **WHEN** a minimum interval is configured such that the configured hourly quota can never be reached
- **THEN** the configuration MUST be rejected, because the operator-visible quota control would be a dead knob

#### Scenario: Scaling rounds a quota to zero
- **WHEN** a ramp or tier multiplier would reduce a configured allowance of one to zero
- **THEN** it MUST round up, because zero is a hard denial and silently stops the feature

### Requirement: Account threat state MUST have one writer driven only by platform signals

Account threat state SHALL have exactly one writer and SHALL be advanced only by platform-observable signals or explicit operator signals. Budget or quota exhaustion, configuration edits, ramp settings, alert resolution, backstop gates, and read-only projections MUST NOT emit a risk signal, trigger a state transition, or write account risk state; a budget denial SHALL be back-pressure only. Risk state and its windowed counters MUST be durable: the system MUST NOT operate with an in-memory-only risk store, and startup MUST replay the current window's counts. Every risk-state write SHALL carry an ownership predicate, and a zero-row result MUST surface as an explicit failure rather than be retried, widened, or reported as success. A saturated burst window is an abnormal-pace signal that MUST alert; a saturated daily window is expected budget exhaustion and MUST NOT alert. Long suppression periods MUST throttle their observability records, and throttling MUST NOT degrade to silence: each suppression period MUST leave at least one record identifying the account and reason.

#### Scenario: Own quota saturates
- **WHEN** an account hits its own configured hourly quota
- **THEN** this MUST NOT advance the account toward a restricted threat state, because self-inflicted throttling is not a platform signal

#### Scenario: Risk store is unavailable at startup
- **WHEN** no durable risk store can be reached
- **THEN** the writer MUST NOT run with an in-memory substitute that reports every account as normal

### Requirement: Task inputs and writes MUST be scoped to the acting account

Every input a TaskRun reads to produce or dispatch an action — persona, reference corpus, interaction and de-duplication history, contact payloads — and every fact it writes back MUST be scoped to the acting account and its owning customer. Cross-account reads or writes MUST fail closed rather than fall back to another account's data. This scoping applies to reads performed through owning-domain interfaces as well as to Automation-owned tables.

#### Scenario: Reference corpus is empty for this account
- **WHEN** an account has no curated corpus
- **THEN** composition MUST proceed without one or skip honestly, and MUST NOT read another account's corpus

### Requirement: Projections MUST be honest about absence, failure, and freshness

A projection SHALL represent a structurally unsupported or unknown metric by omitting the field and MUST NOT substitute zero; conversely, capability support MUST be read only from an explicit declaration and MUST NOT be inferred from a metric or budget that happens to be zero. A read failure MUST be presented as a failure with a retry affordance and MUST NOT be presented as still loading, as empty data, or as built-in default values masquerading as real configuration; "no permission", "not yet initialized (actionable)", and "read failed" MUST be distinguishable. Customer- and operator-facing projections of budgets, limits, ramp progress, and window state SHALL be derived from the same evaluation and clock read the corresponding admission decision uses, MUST be read-only, and MUST carry a server-generated freshness timestamp letting a consumer distinguish "no activity" from "observation stalled". A queue projection MUST distinguish waiting for resources from waiting for a human decision, MUST NOT describe list order as a precise queue position, and MUST apply filtering before limiting so queued items are not displaced by unrelated terminals. A configuration surface MUST NOT offer a mode the runtime will skip, and MUST NOT maintain a second copy of the platform capability matrix.

#### Scenario: Platform has no favourites concept
- **WHEN** a platform does not expose a favourites count
- **THEN** the field MUST be omitted rather than rendered as zero, and the platform's support MUST NOT be inferred from that zero

#### Scenario: Panel request fails
- **WHEN** a panel query errors
- **THEN** the surface MUST show a failure with retry, never an indefinite skeleton, an empty state, or fabricated defaults

#### Scenario: A mode is not yet implemented for a platform
- **WHEN** a platform's publish supports only review mode
- **THEN** the configuration catalogue MUST NOT offer unattended mode as configurable, because a dispatch-time `unsupported` leaves the operator with a silently ineffective switch

### Requirement: Explanations MUST NOT exceed recorded evidence

Human-readable explanations derived from reason codes MUST NOT exceed the precision of persisted evidence: an unrecognized reason code MUST be surfaced verbatim rather than paraphrased or embellished, and a failure recorded only at stage granularity MUST be described at that stage with a reference to the underlying record. When a run terminates with zero successes because a bound was exhausted, the customer-visible outcome SHALL state both why it stopped and why it did not succeed, taking the latter from the last settled Attempt carrying a non-empty reason; a bound-exhaustion accounting message alone MUST NOT be presented as the failure cause. When an executor has reported an authoritative outcome reason for a step, the orchestrator MUST settle that step on the reported reason instead of waiting out its own deadline, and MUST surface that reason rather than attributing the failure to timeout, connectivity, or content availability. Automation and any Agent-mediated projection MUST NOT synthesize a cause more specific than the Ledger and Trace records support.

#### Scenario: Attempts are exhausted
- **WHEN** a task ends at its attempt bound with zero successes
- **THEN** the result MUST carry the last settled Attempt's real reason in addition to "attempt bound reached"

#### Scenario: Executor already reported a navigation failure
- **WHEN** the executor reports that it never reached the results surface
- **THEN** the step MUST be settled and explained with that reason, not with the orchestrator's own timeout
