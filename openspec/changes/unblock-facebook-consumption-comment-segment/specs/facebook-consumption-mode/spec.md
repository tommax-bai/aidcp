## MODIFIED Requirements

### Requirement: Confirmed unique views create one like opportunity without debt

Consumption browsing SHALL count only confirmed Facebook `view` facts with an authoritative account, stable canonical content key, occurrence time, source dedupe key, matching policy revision and server-injected execution target. Mounted cards, placeholders, navigation-only opens, duplicate content within the current collecting set, duplicate deliveries and views observed while another effective mode owns the account MUST NOT count.

For `N=consumption.viewsPerLike`, the Nth unique confirmed view SHALL atomically reset the view counter and create exactly one like opportunity bound to that Nth content. Cloud MUST NOT search for a different target or carry a missed like to later content. Immediately before dispatch, the like MUST pass all existing content-safety, RiskController, ratio, cooldown, session, daily, platform-capability, current-target, already-liked and postcondition gates.

The like opportunity SHALL permit only one bounded platform attempt. While its receipt is pending, the same opportunity SHALL remain in flight, add no credit and MUST NOT be redispatched. `already_liked`, `already_reacted`, ambiguous, submitted-unknown, gated, not-started, structural, rejected and failed terminal outcomes MUST NOT be recorded as a newly produced like and MUST NOT create retry debt; after a terminal outcome, subsequent confirmed unique views begin the next N-view collection.

**A downstream obligation that is still waiting before any platform attempt MUST NOT stop view counting or like creation.** The single advancement slot SHALL hold only a dispatchable or in-flight action: a join or comment obligation in `waiting_target` / `waiting_gate` whose dispatch phase is still `not_started` SHALL release that slot while remaining durable and non-terminal. Confirmed unique views SHALL continue to be recorded and SHALL continue to reach the Nth-view like threshold while such an obligation waits. An action that has already been dispatched MUST keep the slot, so that no new opportunity is created while an irreversible write is in flight.

#### Scenario: Configured view threshold creates one exact-target like
- **WHEN** the Nth eligible unique confirmed view is applied for one account, target and revision
- **THEN** Cloud resets the view counter and creates exactly one like opportunity for that Nth content

#### Scenario: Duplicate view does not approach the threshold
- **WHEN** a content key already counted in the current collecting set is reported again
- **THEN** the confirmed-view counter remains unchanged and no additional like opportunity is created

#### Scenario: Already-liked target produces no success credit
- **WHEN** the Nth content is already liked before the consumption attempt
- **THEN** the opportunity ends with the truthful already-liked outcome
- **AND** no confirmed-like credit or replacement target is created

#### Scenario: Pending like is active but non-counting
- **WHEN** the like attempt has been dispatched but its receipt is still pending
- **THEN** the same opportunity remains in flight, adds no confirmed-like credit and is not dispatched a second time

#### Scenario: Blocked or ambiguous like creates no debt
- **WHEN** the like becomes risk-suppressed, ambiguous, submitted-unknown or failed
- **THEN** the opportunity records that terminal outcome, adds no confirmed-like credit and is not replayed after the blocker clears

#### Scenario: Waiting comment obligation does not stop browsing credit
- **WHEN** a comment obligation is durable in `waiting_gate` or `waiting_target` with dispatch phase `not_started` and further unique confirmed views arrive
- **THEN** Cloud records those view facts and creates the next like opportunity at the Nth view
- **AND** the comment obligation remains durable and non-terminal without restoring any credits

#### Scenario: Dispatched action still holds the slot
- **WHEN** an action has already been dispatched to Edge and its receipt has not settled
- **THEN** further confirmed views MUST NOT create another opportunity for that account and revision

### Requirement: Only confirmed newly joined groups create historical-group comment opportunities

Consumption mode SHALL increment its confirmed-join counter only when the exact matching standalone consumption join opportunity produces platform-confirmed proof of a newly joined group. `already_member`, pending approval, ambiguous, observation-only, gated, not-started, rejected and failed outcomes MUST NOT increment the counter. Membership created manually, by persona scheduling, by rule mode or under another revision MUST NOT count toward this cadence.

For `J=consumption.confirmedJoinsPerComment`, the Jth confirmed newly joined group SHALL atomically reset the confirmed-join counter and create exactly one separate historical-group comment opportunity. The new membership result SHALL be recorded before comment target selection. Candidate eligibility SHALL be determined solely by the authoritative `joined_at` wait and per-group re-comment cooldown predicates; Cloud MUST NOT add a source- or threshold-based exclusion for the triggering group.

If no eligible group exists, the comment opportunity SHALL remain durable as `waiting_target`; it MUST retain one comment obligation without restoring the J confirmed-join credits or creating a duplicate opportunity. Once an eligible group is bound, approval or another reversible pre-dispatch gate MAY leave that same obligation waiting without a platform attempt. After one bounded platform comment attempt is dispatched, a pending receipt keeps it in flight and non-counting without redispatch; an ambiguous, submitted-unknown or failed terminal outcome consumes the opportunity without retry debt. Another comment opportunity then requires J later confirmed new group joins under the same active revision.

**Outstanding obligations of one type SHALL be capped at one per account and active revision.** When a threshold is reached while a non-terminal obligation of the same action type already exists, Cloud MUST NOT create a second one; it SHALL keep the existing obligation and MUST record that the newly earned opportunity was merged into it. It MUST NOT drop the event silently, because "quietly did one fewer round" and "merged into the standing obligation" are different facts to operations.

#### Scenario: Configured confirmed-join threshold creates one comment opportunity
- **WHEN** the Jth platform-confirmed newly joined group for the active consumption revision settles
- **THEN** Cloud resets the confirmed-join counter and creates exactly one separate historical-group comment opportunity

#### Scenario: Already-member result does not approach the threshold
- **WHEN** a standalone join opportunity discovers that the account was already a member
- **THEN** Cloud records `already_member` without incrementing the confirmed-join counter

#### Scenario: Pending or ambiguous join does not create a comment
- **WHEN** the would-be Jth join is pending approval, ambiguous or otherwise unconfirmed
- **THEN** Cloud creates no historical-group comment opportunity

#### Scenario: Triggering group receives no special exclusion
- **WHEN** the Jth confirmed new join creates a comment opportunity
- **THEN** Cloud evaluates that group by the same `joined_at` wait and re-comment cooldown predicates as every other joined group
- **AND** it adds no separate exclusion based on the group having triggered the threshold

#### Scenario: Second earned comment merges into the standing obligation
- **WHEN** the Jth confirmed new join is reached while an earlier comment obligation for the same account and revision is still non-terminal
- **THEN** Cloud keeps exactly one comment obligation and creates no second one
- **AND** it records the merge explicitly rather than passing over the event without a trace

### Requirement: Consumption mode preserves all admission and action blockers

Cloud SHALL start or advance consumption mode only when it is the authoritative effective operation mode for the uniquely bound Facebook environment. Active slow start SHALL have absolute precedence. An unknown or conflicted environment binding, unreadable or unsupported policy snapshot, sleeping weekly active window, offline account, account single-flight conflict, platform mismatch or stale projection MUST fail closed with a named blocker.

Consumption browsing, like, join and comment SHALL retain all applicable existing safety, RiskController, ratio, cooldown, session, daily, capability, membership, approval, dedupe, exact-target and postcondition gates. Configured cadence values create opportunities only; they MUST NOT reserve quota, bypass approval, authorize an action, turn ambiguity into confirmation or weaken truthful partial outcomes. Independent persona-scheduled automatic group joining MUST NOT run while consumption is the effective mode.

A terminal admission rejection encountered before irreversible dispatch SHALL end the current opportunity without dispatch and without debt. Target absence and approval waiting are non-terminal states explicitly covered by their own contracts. A pending receipt after dispatch SHALL remain non-counting and in flight without redispatch; an ambiguous or failed terminal receipt SHALL preserve its exact state and MUST NOT be automatically retried.

**A blocker on one action type MUST NOT be allowed to stop the other action types.** When a named blocker holds an obligation before any platform attempt, Cloud SHALL keep reporting that blocker on that obligation and SHALL continue the browsing, like and join segments that the blocker does not itself gate. A single stalled segment MUST NOT become a durable, cross-restart halt of the whole account.

**At most one Edge-facing consumption action SHALL be driven per confirmed view.** When a confirmed view produces a like dispatch, a waiting obligation MUST NOT also be driven in that same round; it SHALL be driven by a later view or by the in-flight recovery sweep. Two Edge-facing actions MUST NOT contend for the same browser at the same moment.

#### Scenario: Active slow start owns the account
- **WHEN** the environment selects consumption mode but the account's authoritative slow-start lifecycle is active
- **THEN** consumption counters do not advance, no consumption action is dispatched and the projection exposes `slow_start_active`

#### Scenario: Unknown policy truth fails closed
- **WHEN** the policy revision or its typed consumption snapshot cannot be read or validated
- **THEN** Cloud starts neither consumption nor a guessed fallback and exposes the named blocker

#### Scenario: Cadence threshold does not bypass approval
- **WHEN** a comment opportunity reaches its threshold but the effective approval policy requires human review
- **THEN** Cloud waits for valid approval and MUST NOT submit merely because the configured threshold was reached

#### Scenario: Persona schedule cannot add a group during consumption
- **WHEN** an independent time-scheduled group-join tick occurs while consumption is the effective mode
- **THEN** that persona-scheduled join is suppressed with a named mode blocker and no consumption counter changes

#### Scenario: Named blocker on one segment leaves the others running
- **WHEN** a comment obligation is held by a named pre-dispatch blocker such as an unavailable group-comment policy or no timing-eligible group
- **THEN** Cloud keeps reporting that blocker on that obligation
- **AND** confirmed views, like opportunities and join opportunities continue under the same active revision

#### Scenario: One Edge-facing action per view
- **WHEN** a confirmed view creates and dispatches a like while a comment obligation is waiting
- **THEN** Cloud MUST NOT drive that comment obligation in the same round
