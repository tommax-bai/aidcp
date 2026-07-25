## ADDED Requirements

### Requirement: Automation MUST serialize conflicting work per authoritative account lane

Account Work Arbiter SHALL create a lane from the API-authoritative account/platform binding and frozen `envKey`, binding revision, and execution target, obtaining that binding through the owning domain's interface rather than a direct cross-database read. Work that can conflict on the same platform account SHALL be admitted through this lane before requesting Edge or connector resources. Display names, client-provided IDs, and mutable aliases MUST NOT define the lane. Lane exclusion SHALL be enforced only within the automation owner database and MUST NOT be relied on to exclude writers owned by other domains.

#### Scenario: Lane exclusion is asked to cover another domain's writer
- **WHEN** a design or implementation would depend on the account lane to serialize a write owned by the API or Content domain
- **THEN** it MUST instead route that write through its single owning writer or an eventually consistent contract, because a database-scoped lock cannot exclude a writer connected to a different owner database

#### Scenario: Browse and publish target the same account
- **WHEN** a managed browse TaskRun is active and an approved publish TaskRun becomes eligible for the same account
- **THEN** Account Work Arbiter SHALL order them by declared priority and safe-point rules rather than allowing uncontrolled concurrent page work

#### Scenario: Binding revision changed
- **WHEN** queued work references an obsolete account/environment binding revision
- **THEN** admission MUST fail closed or require a new TaskRun instead of executing against the new binding implicitly

### Requirement: Every work kind MUST declare scheduling and arbitration metadata

Each registered Work Kind SHALL declare priority class, browser requirement, `scheduledAt`, `latestStartAt`, `missPolicy`, maximum account wait, safe points, and resumability. Work without valid metadata MUST NOT enter an account lane.

#### Scenario: Work metadata is complete
- **WHEN** an approved scheduled publish enters the lane with a valid deadline and miss policy
- **THEN** the Arbiter SHALL compare it with current work using the registered metadata and record the decision reason

#### Scenario: Work omits latest start time
- **WHEN** a time-sensitive write work item lacks a valid `latestStartAt`
- **THEN** the Arbiter MUST reject admission as contract-invalid rather than queue it indefinitely

### Requirement: Preemption MUST occur only at declared safe points

Higher-priority work MAY quiesce lower-priority work only at a TaskDefinition/Edge-declared safe point. The system MUST NOT preempt during an in-flight submit command, an unresolved external outcome, or a page transition that has not been validated. Preemption during a partially filled form is likewise prohibited for every ordinary priority class; it is permitted only for the recovery priority class defined below, whose admission MUST NOT be deferred until the incumbent completes, because the incumbent may be blocked by the very condition the recovery work exists to clear. Resume SHALL revalidate account, page, target, and capability state.

#### Scenario: Publish arrives between browse cards
- **WHEN** browse processing reaches a confirmed card boundary and a higher-priority approved publish is waiting
- **THEN** the browse TaskRun MAY checkpoint and release the account lane before publish is admitted

#### Scenario: Publish arrives during comment submit
- **WHEN** a comment command is dispatched and its result is not yet known
- **THEN** the Arbiter MUST NOT preempt or release the work as safely complete until the Attempt reaches a valid receipt/reconciliation state

### Requirement: Account arbitration MUST remain separate from machine browser scheduling

Account Work Arbiter SHALL decide which business work may advance for an account. Edge Host/Edge task/browser-slot coordination SHALL separately own physical profile and page resources. The acquisition order MUST be account admission before machine/profile/browser lease, and the Arbiter MUST NOT hold a machine resource while waiting on another account lane or evict a different account's slot.

#### Scenario: API-only reply is admitted
- **WHEN** an inbound reply work item is admitted and the platform capability declares API-only execution
- **THEN** it SHALL use the account lane without requesting a browser slot

#### Scenario: Machine has no browser slot
- **WHEN** account work is admitted but the machine cannot provide the required browser/profile resource
- **THEN** the work SHALL enter a named wait subject to its deadline, and the Arbiter MUST NOT evict an unrelated account

### Requirement: Missed schedules MUST follow explicit policy

When `latestStartAt` passes before irreversible dispatch, the Arbiter SHALL apply exactly one declared `missPolicy`: `skip`, `require_reapproval`, or `execute_when_available`. It MUST NOT choose a fallback based on process restart, Edge reconnect, or implementation convenience.

#### Scenario: Scheduled publish misses a skip window
- **WHEN** Edge remains offline until after a publish work item's `latestStartAt` and `missPolicy=skip`
- **THEN** the work SHALL terminate as skipped and MUST NOT publish later

#### Scenario: Approved publish requires reapproval after lateness
- **WHEN** an approved publish passes `latestStartAt` with `missPolicy=require_reapproval`
- **THEN** Automation SHALL invalidate the current execution authorization, retain the immutable intent for audit, and request a new approval decision

#### Scenario: Delay-tolerant research resumes
- **WHEN** delay-tolerant research has `missPolicy=execute_when_available` and a valid Edge connection returns
- **THEN** the Arbiter MAY resume it after live admission and deadline/budget checks

### Requirement: Long approval gaps MUST release page resources

Scheduled and full-managed comments SHALL use separate prepare and commit work admissions: prepare MAY search/read and persist a stable target snapshot, then MUST release page resources during composition/approval; commit SHALL reacquire work, reopen the stable target, and revalidate it before submission. A short in-session approval MAY hold resources only for the bounded duration explicitly allowed by its existing contract.

#### Scenario: Scheduled comment waits for human approval
- **WHEN** prepare has selected a stable target and the comment requires human review
- **THEN** the account/browser work SHALL be released while awaiting approval and reacquired for a separate commit phase

#### Scenario: Target changed before commit
- **WHEN** commit reopens the target and its identity or suitability no longer matches the frozen snapshot
- **THEN** submission MUST be denied with an honest stale/target-changed reason

### Requirement: Arbitration MUST expose fairness and waiting evidence

The Arbiter SHALL record queue entry, admission, quiesce, resume, deadline miss, and release with account/work identifiers, reason codes, and wait durations. Repeated lower-priority starvation and deadline misses MUST be observable by account, work kind, and execution target.

#### Scenario: Managed browsing is repeatedly delayed
- **WHEN** higher-priority writes repeatedly postpone a managed browse work item
- **THEN** metrics and Decision Trace SHALL show cumulative wait and starvation evidence rather than silently resetting its queue age

### Requirement: Lane identity MUST be the platform account and lanes MUST cover only platform-affecting work

The account lane, its quota/risk accounting, and its duplicate-target scope SHALL be keyed by the authoritative platform account alone; `envKey`, edge id, connection, machine, and profile MUST be execution attributes of the lane, never part of its identity. When one platform account is reachable through multiple environments or edges, all such work MUST share one lane, one merged quota/risk ledger, and one duplicate-target scope. Lane admission SHALL be required only for work that can conflict on the platform account itself; work with no platform side effect (content generation, model calls, waiting for approval or another service) MUST NOT hold an account lane, and its concurrency SHALL be governed by finer-grained input-identity keys so that distinct inputs for one account remain parallel.

#### Scenario: One account on two environments
- **WHEN** the same platform account is connected through two environments on two machines
- **THEN** their work SHALL serialize in one lane and consume one merged daily allowance, not two

#### Scenario: Generation and approval wait
- **WHEN** a Task is generating a candidate or waiting for human approval with no platform command in flight
- **THEN** it MUST NOT occupy the account lane, so other sources for that account remain admissible

### Requirement: Safe points MUST be defined by absence of platform side effects

A safe point SHALL be defined by the absence of platform side effects, not by command boundaries. Any segment of an in-flight command before its first real page mutation — blocking-overlay waits, inter-action delays, pre-action hesitation, and pre-exit dwell — MUST be cancellable on the spot with a zero-side-effect honest failure receipt, and quiesce SHALL wait only for actions actively mutating the page. The Arbiter SHALL recognise a recovery priority class (captcha, risk-control, and human-assist work that itself needs the browser) which MAY preempt any lower-class work at any time before that work's irreversible dispatch, including work holding a partially filled form; recovery-class admission MUST NOT be deferred until the incumbent completes, and priority MUST be re-evaluated on every arrival rather than only at grant time. A capability MAY declare a read operation as irreversible-consuming when the act of reading destroys unrecoverable platform state; within such a declared window the Arbiter MUST refuse preemption and MUST NOT inject a safe cancellation point even though no page write has occurred. A user-supplied priority flag SHALL only reorder work within the automated classes and MUST NOT promote asynchronous work into the operator or recovery class.

#### Scenario: Browse command is waiting on a captcha overlay
- **WHEN** captcha assist work needs the browser while a browse command sits in a blocking-overlay wait
- **THEN** that command MUST be cancelled immediately with a zero-side-effect receipt and the lane granted, because waiting for it would require the very captcha the assist work is meant to clear

#### Scenario: Notification triage has consumed unread state
- **WHEN** a read step has opened a notification tab whose unread state is destroyed by the act of reading and cannot be re-reported
- **THEN** the Arbiter MUST refuse preemption for the declared window and report the remaining budget instead

### Requirement: Quiesce MUST be verifiable, bounded, and reversible

Quiesce SHALL be considered complete only when the preempted executor has verifiably stopped issuing page-mutating operations; issuing a cancel signal MUST NOT satisfy it. Every executor capable of mutating a page SHALL be registered in one page-write accounting registry and SHALL honour one cancellation token, and no executor may reach the browser control endpoint outside that registry. Quiesce SHALL have a bounded wall-clock limit; if it does not converge within that limit the Arbiter MUST NOT grant the lane, MUST terminate the queued admission with an honest terminal reason, and MUST roll back every suppression or freeze flag it set when quiesce began. Failure to yield within the bound SHALL be classified as a control-plane fault with a machine-readable reason distinguishable from benign retryable conditions; it MUST NOT trigger automatic retry, automatic redispatch, or automatic restoration of queue budget, and MUST surface a named operator action. Work terminated by arbitration — preemption, quiesce, lane release, deadline checkpointing — SHALL be recorded as a scheduling outcome and MUST NOT increment any business failure, retry-exhaustion, or circuit-breaker counter.

#### Scenario: Preempted executor keeps writing
- **WHEN** an executor has not stopped mutating the page within the quiesce bound
- **THEN** the lane MUST NOT be granted, the freeze flags set at quiesce start MUST be rolled back, and a control-plane fault requiring a named operator action MUST be raised

#### Scenario: Publish is preempted by recovery work
- **WHEN** a publish work item is preempted before its irreversible submit
- **THEN** its termination MUST NOT count toward the account's consecutive-failure or circuit-breaker counters

### Requirement: Lane admission MUST be atomic and resolve to exactly one runner

Lane admission — claim, conflict check, intent preparation, and transition to running — SHALL execute as one atomic serialized section per account lane, and admission of the next candidate SHALL only proceed after the current one has established observable ownership. When two conflicting candidates are evaluated concurrently, arbitration MUST resolve to exactly one runner; both deferring on symmetric observation of each other is a defect. Discovery, scanning, and claiming across accounts MUST NOT serialize on any single account's in-flight execution. When an admitted work item holds an exclusive lane, every command it dispatches MUST carry the holder identity of that admission and the enforcement point MUST admit the holder's own commands while blocking others. Worker concurrency SHALL be bounded and configurable.

#### Scenario: Two sources evaluate the same lane at once
- **WHEN** a delegated task and a scheduled task both find the lane free at the same instant
- **THEN** exactly one SHALL be admitted; both observing the other as busy and deferring is a defect, not an honest skip

#### Scenario: Lane holder issues its own command
- **WHEN** the work item holding an exclusive keep-open lane dispatches its next command
- **THEN** that command MUST carry the holder identity and MUST NOT be blocked by the exclusion it installed

### Requirement: Logical ownership MUST survive resource release

Ownership of a work scope SHALL be a logical claim independent of physical resource occupancy. Releasing page, browser, or lane resources during composition, approval, or any other wait MUST NOT make the work invisible to other sources: a second source evaluating the same `(account, action family)` scope MUST observe the outstanding claim and skip or queue accordingly. Ownership SHALL be cleared only by a terminal outcome, an authorized cancellation, or claim expiry.

#### Scenario: A draft is awaiting human approval
- **WHEN** a publish work item has released its resources and is awaiting approval
- **THEN** a scheduled publish trigger for the same account and action family SHALL observe the outstanding claim and MUST NOT generate a second candidate for the same slot

### Requirement: Resource release MUST pair with a wake path

Whenever the system releases or parks a resource in favour of a wait, it SHALL simultaneously establish a wake path that does not depend on computing a recovery time; if no such wake path exists for that wait, the resource MUST NOT be released. Wake paths SHALL be dead-man safe: a periodic re-evaluation channel plus a bounded revisit deadline whose semantics are "come back and ask again", which MUST NOT be presented as a promise that the block will be cleared by then. Release SHALL be denied whenever clearing the current blocker itself requires that resource (captcha, re-login, operator intervention in the browser, resource held elsewhere, unknown state); this veto SHALL be evaluated before and above every release trigger rather than inside an individual trigger branch, and the "requires the resource" fact SHALL come from an authoritative server-side source. When a requester abandons an admission or resource request after its own timeout, it SHALL actively release that request's identity and re-release upon any late grant carrying the same identity, until the owner confirms convergence or the request record expires.

#### Scenario: Account is blocked by a captcha
- **WHEN** an account is blocked pending captcha resolution in its browser
- **THEN** the browser MUST NOT be released or parked, because the action that clears the block needs it

#### Scenario: Admission request times out and is granted late
- **WHEN** a requester gives up waiting and the resource is granted afterwards
- **THEN** the requester MUST release it rather than leave an ownerless lease held until natural expiry

### Requirement: Consecutive external-write failures MUST suspend the account lane

The Arbiter SHALL track consecutive external-write failures per account and, on reaching a configured threshold, MUST suspend admission of further already-authorized irreversible work for that account while preserving each item's authorization, and MUST emit an operator alert. Clearing the suspension SHALL require an explicit human action that is always reachable, so a suspended account can never become undispatchable with no path to recovery. Preemption and other scheduling terminations MUST NOT contribute to this counter.

#### Scenario: Edge page automation breaks
- **WHEN** three consecutive publish dispatches for one account fail at the sequence level
- **THEN** further approved publishes for that account SHALL be suspended with their authorizations retained, rather than each burning down its own retry bound

### Requirement: Budget admission MUST precede physical resource acquisition

Budget and quota admission for a work item SHALL be evaluated against the authoritative ledger before any physical resource (browser wake, profile, browser slot, model call) is acquired, and SHALL be a stateless recomputation rather than a cached derived flag. A denial SHALL place that work item into a bounded named wait scheduled by the budget's release time; it MUST NOT terminate the account's session, MUST NOT block admission of unrelated authorized work for the same account, and MUST NOT be answered by an unbounded or implementation-chosen delay.

#### Scenario: Daily view quota is already exhausted
- **WHEN** a browse work item is evaluated for an account whose view quota is spent
- **THEN** it MUST be denied before the browser is woken, and the denial MUST NOT stop an unrelated approved publish for the same account

#### Scenario: Session resumes after a long sleep
- **WHEN** a denied work item's wait elapses
- **THEN** eligibility SHALL be recomputed from the authoritative ledger rather than from a stored sleep flag
