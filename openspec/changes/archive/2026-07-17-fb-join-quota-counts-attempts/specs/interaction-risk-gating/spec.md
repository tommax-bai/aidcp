## MODIFIED Requirements

### Requirement: Facebook group join is a first-class rate-limited action

Facebook group join SHALL be a rate-limited action alongside browse/like/collect/comment, subject to the existing minute/hour/day sliding-window quotas, the three quota tiers, and risk-state scaling (warned slows all actions; restricted/frozen stops joining). A brand-new account SHALL be throttled by selecting the conservative tier rather than a bespoke warmup function. Join attempts MUST be pre-gated before dispatch.

The join quota is a **risk budget**: it bounds how much join activity the platform observes from the account. It therefore SHALL count **join actions that actually reached the platform**, not joins that succeeded. A join action reaches the platform when the edge reports that it actually performed the click on the live page (`clicked: true`); whether the group then admits the account (`ok: true`), leaves the request awaiting an admin (`ok: false, reason: 'pending'`), or demands a questionnaire is the platform's answer to an action we already took, and MUST NOT determine whether that action counted.

This MUST NOT be conflated with counting on dispatch. **Dispatch is intent; a click is an accomplished fact.** The cloud MUST NOT count a join because it sent a command — a command may never arrive or never execute. It MUST count only the edge's after-the-fact report that the click really happened. An attempt that never reached the platform — a pre-click observation that the request was already pending, an account that was already a member, an observation-only (shadow) run, a navigation or login failure before the click — reports `clicked: false` and MUST NOT count.

Counting a reached-platform join against the quota MUST NOT mark that join as successful. Success and quota are separate questions with separate answers: the success ledger continues to recognise only a judgment-confirmed join, and a counted-but-unconfirmed join MUST NOT enter the display interaction ledger, MUST NOT be reported to the operator as a completed join, and MUST NOT satisfy any requirement that depends on membership.

A **quota-usage display** is not a membership claim, and the two MUST NOT be conflated. A surface whose subject is budget consumption — how much of an action's daily allowance the account has spent — reports **actions spent**; for joins that means join actions that reached the platform, and showing a pending-approval join there is correct, not an overclaim. The surfaces whose subject is membership — which groups the account actually belongs to — MUST continue to count only judgment-confirmed joins. The same word may therefore denote an action on a budget surface and a membership on a ledger surface; each surface MUST be honest about its own subject rather than forced to the other's meaning.

Any count the system holds of join actions that reached the platform is a **lower bound**, never an exact figure: the recording path re-checks policy before writing and silently discards the receipt of an action that was already performed, so a real click made outside the automatic gate — an operator's manual join, or a click whose account was throttled mid-flight — can reach the platform and leave no trace in that counter. Because of this, a gate MUST NOT be relaxed onto a looser bound than one it already enforces. Where the system holds more than one independent lower bound on the same account's join activity — the recorded-action counter and the confirmed-join ledger are two such bounds — gates MAY enforce each of them against the cap, and doing so MUST be understood as taking the tighter estimate rather than as a defect to be unified away. Unifying them onto the recorded-action counter alone MUST NOT be done while that counter can silently drop a real click, because it would raise the account's true join activity above the cap.

#### Scenario: Join quota denial prevents dispatch
- **WHEN** the risk gate denies a join for an account that has exhausted its minute, hour, or day join quota
- **THEN** no join is dispatched and a quota-denied non-success outcome is recorded

#### Scenario: A join that reached the platform counts even when approval is pending
- **WHEN** the edge reports a join in which it performed the click and the request is left awaiting group-admin approval
- **THEN** the account's join quota counter increases by one
- **AND** the join is NOT recorded as a successful or confirmed join
- **AND** the operator is not told the group was joined

#### Scenario: An attempt that never reached the platform does not count
- **WHEN** the edge reports a join outcome in which it did not perform the click — the request was already pending before this attempt, the account was already a member, the run was observation-only, or navigation or login failed first
- **THEN** the account's join quota counter does not increase
- **AND** no successful join interaction is recorded

#### Scenario: Dispatch alone still never counts
- **WHEN** the cloud dispatches a join command and no edge report of an actual click is received
- **THEN** the account's join quota counter does not increase
- **AND** the quota is never spent on intent that the edge did not confirm as actuated

#### Scenario: A quota-usage display shows actions spent, not memberships
- **WHEN** an operator views a per-account quota-usage display after the account performed one join click that is awaiting group-admin approval
- **THEN** the join budget shows one action spent against the cap
- **AND** the surfaces that report group membership still show zero groups joined and one request awaiting approval
- **AND** neither surface is required to adopt the other's meaning

#### Scenario: Only verified join counts as a successful join
- **WHEN** a join attempt returns anything other than a judgment-confirmed join
- **THEN** no successful join interaction is recorded for that account
- **AND** the success ledger's count of groups joined today is unchanged

#### Scenario: A gate is never relaxed onto a looser bound
- **WHEN** an operator manually joins groups up to the daily cap, bypassing the pre-dispatch quota gate by design, and the recorded-action counter drops some of those receipts because a burst window was already saturated when each receipt arrived
- **THEN** the gate that reads the confirmed-join ledger still bounds the automatic join loop at the cap
- **AND** the automatic loop MUST NOT be allowed to resume merely because the recorded-action counter is short

#### Scenario: Restricted state stops joining
- **WHEN** an account's risk state is restricted or frozen
- **THEN** the join loop for that account does not dispatch, inheriting the same state scaling as other interactions
