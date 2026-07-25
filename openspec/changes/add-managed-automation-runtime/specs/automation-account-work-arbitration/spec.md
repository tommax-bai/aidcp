## ADDED Requirements

### Requirement: Automation MUST serialize conflicting work per authoritative account lane

Account Work Arbiter SHALL create a lane from the API-authoritative account/platform binding and frozen `envKey`, binding revision, and execution target. Work that can conflict on the same platform account SHALL be admitted through this lane before requesting Edge or connector resources. Display names, client-provided IDs, and mutable aliases MUST NOT define the lane.

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

Higher-priority work MAY quiesce lower-priority work only at a TaskDefinition/Edge-declared safe point. The system MUST NOT preempt during partially filled forms, an in-flight submit command, unresolved external outcome, or a page transition that has not been validated. Resume SHALL revalidate account, page, target, and capability state.

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
