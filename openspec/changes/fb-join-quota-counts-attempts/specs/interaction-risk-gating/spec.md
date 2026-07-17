## MODIFIED Requirements

### Requirement: Facebook group join is a first-class rate-limited action

Facebook group join SHALL be a rate-limited action alongside browse/like/collect/comment, subject to the existing minute/hour/day sliding-window quotas, the three quota tiers, and risk-state scaling (warned slows all actions; restricted/frozen stops joining). A brand-new account SHALL be throttled by selecting the conservative tier rather than a bespoke warmup function. Join attempts MUST be pre-gated before dispatch.

The join quota is a **risk budget**: it bounds how much join activity the platform observes from the account. It therefore SHALL count **join actions that actually reached the platform**, not joins that succeeded. A join action reaches the platform when the edge reports that it actually performed the click on the live page (`clicked: true`); whether the group then admits the account (`ok: true`), leaves the request awaiting an admin (`ok: false, reason: 'pending'`), or demands a questionnaire is the platform's answer to an action we already took, and MUST NOT determine whether that action counted.

This MUST NOT be conflated with counting on dispatch. **Dispatch is intent; a click is an accomplished fact.** The cloud MUST NOT count a join because it sent a command — a command may never arrive or never execute. It MUST count only the edge's after-the-fact report that the click really happened. An attempt that never reached the platform — a pre-click observation that the request was already pending, an account that was already a member, an observation-only (shadow) run, a navigation or login failure before the click — reports `clicked: false` and MUST NOT count.

Counting a reached-platform join against the quota MUST NOT mark that join as successful. Success and quota are separate questions with separate answers: the success ledger continues to recognise only a judgment-confirmed join, and a counted-but-unconfirmed join MUST NOT enter the display interaction ledger, MUST NOT be reported to the operator as a completed join, and MUST NOT satisfy any requirement that depends on membership.

Every gate that spends this quota MUST read the **same numerator**. A scheduling pre-filter and the dispatch-time quota check MUST NOT measure the account's join activity with two different counts against one shared cap.

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

#### Scenario: Only verified join counts as a successful join
- **WHEN** a join attempt returns anything other than a judgment-confirmed join
- **THEN** no successful join interaction is recorded for that account
- **AND** the success ledger's count of groups joined today is unchanged

#### Scenario: One numerator serves the shared cap
- **WHEN** the scheduling pre-filter and the dispatch-time quota check both evaluate the same account's join activity against the daily join cap
- **THEN** both read the same count of join actions that reached the platform
- **AND** neither uses the count of confirmed joins as the numerator for that cap

#### Scenario: Restricted state stops joining
- **WHEN** an account's risk state is restricted or frozen
- **THEN** the join loop for that account does not dispatch, inheriting the same state scaling as other interactions
