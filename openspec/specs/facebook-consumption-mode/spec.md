# facebook-consumption-mode Specification

## Purpose
TBD - created by archiving change add-configurable-facebook-consumption-mode. Update Purpose after archive.
## Requirements
### Requirement: Facebook consumption mode uses a typed revisioned policy

The system SHALL provide Facebook consumption mode as one explicit value of the authoritative environment-scoped Facebook operation policy. A consumption policy snapshot SHALL contain:

- `consumption.viewsPerLike`, an integer from `1..100` with default `5`;
- `consumption.confirmedLikesPerJoin`, an integer from `1..20` with default `2`;
- `consumption.confirmedJoinsPerComment`, an integer from `1..20` with default `2`.

These values SHALL be immutable within one `policy_revision`. Writes MUST use `expectedRevision` compare-and-swap, with `expectedRevision=0` for first creation, and MUST atomically persist audit identity, time, schema version and the complete snapshot. Unknown fields, missing required fields, decimals, stale expected revisions and out-of-range values MUST be rejected without a partial write. Operators MUST NOT supply scripts, prompts, arbitrary action lists or a free-form execution graph.

The join-to-first-comment wait SHALL come from the independent target-scoped group-comment policy field `joinToFirstCommentHours`. It MUST NOT be copied into or revisioned with the Facebook operation-policy snapshot.

#### Scenario: New environment receives the requested defaults
- **WHEN** an operator selects consumption mode for an authoritative Facebook environment without overriding its values
- **THEN** the published operation-policy snapshot contains cadence `5/2/2`
- **AND** readback returns the new `policy_revision`, audit fields and those exact cadence values

#### Scenario: Group timing is independent of cadence revision
- **WHEN** an operator changes `joinToFirstCommentHours` without changing Facebook operation mode or cadence
- **THEN** the group-comment policy revision changes independently
- **AND** the active Facebook operation `policy_revision` and its consumption counters remain unchanged

#### Scenario: Valid cadence update creates a new revision
- **WHEN** an operator supplies valid typed values and the current `expectedRevision`
- **THEN** Cloud atomically publishes one new immutable revision and returns authoritative write-after-read truth

#### Scenario: Stale or invalid write has no partial effect
- **WHEN** a write has a stale `expectedRevision`, an unknown field, a decimal or a value outside the declared bounds
- **THEN** Cloud rejects the full write and keeps the prior policy revision and snapshot unchanged

#### Scenario: Unsupported environment cannot select consumption mode
- **WHEN** an operator selects consumption mode for a Xiaohongshu, WeChat Channels or unknown-platform environment
- **THEN** Cloud rejects the full write and creates no consumption runtime state

### Requirement: Consumption runtime is target-scoped and idempotent

Consumption counters, confirmed facts, selected targets, action opportunities, terminal outcomes and active ownership SHALL be persisted and deduplicated by `account_id + execution_target + policy_revision`. Every applied view, like or join result MUST carry a stable source dedupe key and MUST match the account, execution target, revision, action opportunity and exact target that produced it. Results from manual actions, persona scheduling, rule mode, another execution target or another policy revision MUST NOT advance consumption counters.

Threshold crossing, counter consumption and creation of the resulting action opportunity SHALL occur in one transaction under account/revision ownership. Repeated event delivery, competing workers, Cloud restart and Edge reconnect MUST produce at most one counter effect and at most one action opportunity. While an opportunity is non-terminal, account single-flight SHALL prevent another consumption opportunity from being accumulated or dispatched.

#### Scenario: Duplicate receipt changes a counter once
- **WHEN** the same confirmed like or join receipt is delivered more than once
- **THEN** its source dedupe identity advances the matching consumption counter at most once

#### Scenario: Other-source action does not advance consumption
- **WHEN** a manual or persona-scheduled like or join succeeds while consumption mode is configured
- **THEN** the platform outcome remains truthful for its own source but no consumption counter changes

#### Scenario: Competing threshold applies create one opportunity
- **WHEN** two workers concurrently apply the fact that reaches a consumption threshold
- **THEN** one atomic transition consumes the threshold and creates exactly one next-stage opportunity

#### Scenario: Execution targets never share runtime progress
- **WHEN** DEV and OL observe data for the same account and policy revision
- **THEN** each target reads and writes only its own counters, facts, opportunities and outcomes

### Requirement: Confirmed unique views create one like opportunity without debt

Consumption browsing SHALL count only confirmed Facebook `view` facts with an authoritative account, stable canonical content key, occurrence time, source dedupe key, matching policy revision and server-injected execution target. Mounted cards, placeholders, navigation-only opens, duplicate content within the current collecting set, duplicate deliveries and views observed while another effective mode owns the account MUST NOT count.

For `N=consumption.viewsPerLike`, the Nth unique confirmed view SHALL atomically reset the view counter and create exactly one like opportunity bound to that Nth content. Cloud MUST NOT search for a different target or carry a missed like to later content. Immediately before dispatch, the like MUST pass all existing content-safety, RiskController, ratio, cooldown, session, daily, platform-capability, current-target, already-liked and postcondition gates.

The like opportunity SHALL permit only one bounded platform attempt. While its receipt is pending, the same opportunity SHALL remain in flight, add no credit and MUST NOT be redispatched. `already_liked`, `already_reacted`, ambiguous, submitted-unknown, gated, not-started, structural, rejected and failed terminal outcomes MUST NOT be recorded as a newly produced like and MUST NOT create retry debt; after a terminal outcome, subsequent confirmed unique views begin the next N-view collection.

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

### Requirement: Only confirmed newly produced likes create standalone join opportunities

Consumption mode SHALL increment its confirmed-like counter only when the exact matching consumption like opportunity returns platform-confirmed proof that this attempt newly changed the target to liked. `already_liked`, `already_reacted`, pending, ambiguous, submitted-unknown, gated, not-started, rejected and failed outcomes MUST NOT increment the counter.

For `L=consumption.confirmedLikesPerJoin`, the Lth confirmed new like SHALL atomically reset the confirmed-like counter and create exactly one standalone group-join opportunity. That opportunity SHALL execute only the existing join action and MUST NOT invoke a comment, contact injection or `joinFirst` comment workflow. It SHALL pass the existing join RiskController, session, daily, platform, target, membership and postcondition gates immediately before irreversible dispatch.

If no join target is currently available before any platform attempt, the join opportunity SHALL remain durable as `waiting_target`; it MUST retain one obligation without restoring the L confirmed-like credits or creating a duplicate opportunity. Once an exact target is bound, the opportunity SHALL permit only one platform join attempt. A pending receipt keeps that same opportunity in flight and non-counting without redispatch. A gated, ambiguous, already-member, rejected or failed terminal result SHALL consume the opportunity without retry debt. Another join opportunity then requires L later confirmed new likes under the same active revision.

#### Scenario: Configured confirmed-like threshold creates one join
- **WHEN** the Lth platform-confirmed new like for the active consumption revision settles
- **THEN** Cloud resets the confirmed-like counter and creates one standalone group-join opportunity

#### Scenario: Ambiguous like does not create a join
- **WHEN** a consumption like returns submitted-unknown or verification-ambiguous at the would-be threshold
- **THEN** Cloud records the unknown like outcome and does not advance the confirmed-like counter or create a join

#### Scenario: Join action never comments in the newly joined group
- **WHEN** a consumption join opportunity is dispatched and membership becomes confirmed
- **THEN** that join opportunity terminates after recording membership
- **AND** it MUST NOT open or submit a comment in that newly joined group

#### Scenario: Pending join remains the same non-counting attempt
- **WHEN** a join created from L confirmed likes has been dispatched and its receipt remains pending
- **THEN** Cloud keeps that opportunity in flight, restores no like credits, adds no confirmed join and does not redispatch it

#### Scenario: Failed join consumes the opportunity without debt
- **WHEN** a join created from L confirmed likes becomes ambiguous, already-member, rejected or failed after its one attempt
- **THEN** Cloud records the truthful terminal outcome, restores no like credits and does not retry that opportunity

#### Scenario: Missing join target preserves one obligation
- **WHEN** no eligible join target is available before a join opportunity reaches platform dispatch
- **THEN** the opportunity remains `waiting_target` with the L like credits already consumed
- **AND** later target discovery resumes that same opportunity rather than creating or charging another one

### Requirement: Only confirmed newly joined groups create historical-group comment opportunities

Consumption mode SHALL increment its confirmed-join counter only when the exact matching standalone consumption join opportunity produces platform-confirmed proof of a newly joined group. `already_member`, pending approval, ambiguous, observation-only, gated, not-started, rejected and failed outcomes MUST NOT increment the counter. Membership created manually, by persona scheduling, by rule mode or under another revision MUST NOT count toward this cadence.

For `J=consumption.confirmedJoinsPerComment`, the Jth confirmed newly joined group SHALL atomically reset the confirmed-join counter and create exactly one separate historical-group comment opportunity. The new membership result SHALL be recorded before comment target selection. Candidate eligibility SHALL be determined solely by the authoritative `joined_at` wait and per-group re-comment cooldown predicates; Cloud MUST NOT add a source- or threshold-based exclusion for the triggering group.

If no eligible group exists, the comment opportunity SHALL remain durable as `waiting_target`; it MUST retain one comment obligation without restoring the J confirmed-join credits or creating a duplicate opportunity. Once an eligible group is bound, approval or another reversible pre-dispatch gate MAY leave that same obligation waiting without a platform attempt. After one bounded platform comment attempt is dispatched, a pending receipt keeps it in flight and non-counting without redispatch; an ambiguous, submitted-unknown or failed terminal outcome consumes the opportunity without retry debt. Another comment opportunity then requires J later confirmed new group joins under the same active revision.

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

### Requirement: Historical-group selection strictly enforces membership timing

For a consumption comment opportunity, Cloud SHALL select only from the account's durable membership ledger rows whose membership is platform-confirmed `joined`, whose `joined_at` is no later than `selection_time - joinToFirstCommentHours`, and whose existing per-group re-comment cooldown has expired at `selection_time`. Missing, invalid or unreadable timestamps SHALL make a row ineligible. Selection MUST NOT use a relaxed fallback that drops the join wait, last-comment or cooldown predicates.

Cloud SHALL atomically bind one eligible group and its timing evidence to the comment opportunity before opening the group. The selection policy MAY choose among strictly eligible rows, but reconnect, restart or repeated delivery MUST reuse the already-bound group rather than select another one. A recently joined group SHALL become eligible naturally when its persisted `joined_at` satisfies the independent group-comment policy's wait; no migration or rewritten timestamp is allowed.

#### Scenario: Group inside the join wait is ineligible
- **WHEN** a joined membership row is newer than `joinToFirstCommentHours`
- **THEN** Cloud excludes that group even when no other group is available

#### Scenario: Re-comment cooldown remains authoritative
- **WHEN** a previously joined group satisfies the join wait but its per-group re-comment cooldown has not expired
- **THEN** Cloud excludes that group from the consumption comment opportunity

#### Scenario: Strict selection has no relaxed fallback
- **WHEN** every joined group fails the join wait or re-comment cooldown predicate
- **THEN** the same comment opportunity remains durable as `waiting_target`
- **AND** Cloud MUST NOT select a recent or cooling-down group

#### Scenario: Waiting selection resumes when timestamps become eligible
- **WHEN** a `waiting_target` comment opportunity reaches the next authoritative eligibility time
- **THEN** Cloud re-evaluates strict ledger predicates and binds at most one eligible group to that same obligation

#### Scenario: Bound group is stable across reconnect
- **WHEN** Cloud or Edge reconnects after a group has been bound but before comment submission
- **THEN** the same opportunity resumes with that exact group and MUST NOT choose a different eligible group

### Requirement: Consumption comments target the first commentable discussion item

After binding an eligible historical group, consumption mode SHALL use the existing explicit `first_commentable_group_post` selection strategy. Edge SHALL inspect the group's discussion stream in current top-to-bottom order and bind the first structurally commentable content to a stable canonical content key. This path MUST NOT use account keywords, persona relevance, semantic search, random post selection or a join-first target.

Once the first commentable content is bound, Cloud MUST NOT substitute a later item to satisfy the opportunity if dedupe, approval, risk, target freshness or submission fails. If no structurally commentable item is found within the bounded inspection, the opportunity SHALL terminate with a named no-target outcome and no retry debt.

The resulting action SHALL be an ordinary group comment without contact injection and without another group join. It MUST pass the existing comment RiskController, session and daily budgets, effective approval policy, content safety, dedupe, group-membership freshness, exact-target validation and post-submission verification. Only platform-confirmed submission SHALL be reported as a confirmed comment and update the group's confirmed re-comment timestamp; pending, ambiguous, submitted-unknown, rejected and failed outcomes MUST remain distinct from success.

#### Scenario: First commentable item is selected explicitly
- **WHEN** the bound group discussion contains non-commentable content followed by two commentable items
- **THEN** Edge binds the first commentable item in displayed top-to-bottom order
- **AND** it does not invoke keyword or persona selection

#### Scenario: Exact first item is not replaced after a gate rejection
- **WHEN** the bound first-commentable item later fails dedupe, approval, risk or target freshness
- **THEN** the opportunity records the named blocker and MUST NOT comment on a later item

#### Scenario: Consumption comment is neither join-first nor contact injection
- **WHEN** a consumption comment passes selection and all gates
- **THEN** Cloud submits one ordinary comment to the exact historical-group content
- **AND** it dispatches no group join and injects no contact information merely because of the consumption source

#### Scenario: Ambiguous submission is not confirmed success
- **WHEN** comment submission is verification-ambiguous or submitted-unknown
- **THEN** Cloud records the unknown outcome, consumes the opportunity and MUST NOT mark a confirmed comment or confirmed re-comment timestamp

### Requirement: Consumption mode preserves all admission and action blockers

Cloud SHALL start or advance consumption mode only when it is the authoritative effective operation mode for the uniquely bound Facebook environment. Active slow start SHALL have absolute precedence. An unknown or conflicted environment binding, unreadable or unsupported policy snapshot, sleeping weekly active window, offline account, account single-flight conflict, platform mismatch or stale projection MUST fail closed with a named blocker.

Consumption browsing, like, join and comment SHALL retain all applicable existing safety, RiskController, ratio, cooldown, session, daily, capability, membership, approval, dedupe, exact-target and postcondition gates. Configured cadence values create opportunities only; they MUST NOT reserve quota, bypass approval, authorize an action, turn ambiguity into confirmation or weaken truthful partial outcomes. Independent persona-scheduled automatic group joining MUST NOT run while consumption is the effective mode.

A terminal admission rejection encountered before irreversible dispatch SHALL end the current opportunity without dispatch and without debt. Target absence and approval waiting are non-terminal states explicitly covered by their own contracts. A pending receipt after dispatch SHALL remain non-counting and in flight without redispatch; an ambiguous or failed terminal receipt SHALL preserve its exact state and MUST NOT be automatically retried.

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

### Requirement: Policy revisions and mode switches do not reinterpret consumption progress

Publishing a new `policy_revision` SHALL stop new collection and new action creation under the previous revision. Partial view, confirmed-like and confirmed-join counters MUST NOT carry into the new revision. An already dispatched old-revision action SHALL settle truthfully under its original target and snapshot, but every old-revision intent that has not reached irreversible dispatch, including one waiting for approval, SHALL terminate as `policy_superseded` and MUST NOT start a downstream action.

The new revision SHALL start all consumption counters at zero after prior account single-flight ownership is terminal. Switching from consumption to `persona`, `slow_start` or `rule` SHALL apply the same settlement rule and MUST NOT leave consumption work running behind the newly effective mode. Switching back to consumption SHALL require a new policy revision and MUST NOT resume progress from an older consumption revision.

#### Scenario: Cadence edit starts from zero
- **WHEN** an account has partial consumption counters and an operator publishes a new consumption cadence revision
- **THEN** the new revision begins with view, confirmed-like and confirmed-join counters at zero
- **AND** old facts remain historical without being reinterpreted

#### Scenario: Dispatched action settles but creates no downstream work
- **WHEN** a consumption join has been irreversibly dispatched and the environment switches modes before its receipt arrives
- **THEN** Cloud records the truthful join result under the old revision
- **AND** it MUST NOT create a historical-group comment opportunity after the switch

#### Scenario: Undispatched or approval-waiting work is superseded
- **WHEN** a policy revision changes before an action reaches irreversible dispatch
- **THEN** the old opportunity terminates as `policy_superseded` and no command is sent

#### Scenario: Returning to consumption does not resume an old counter
- **WHEN** an environment leaves consumption mode and later selects it again
- **THEN** the newly published revision starts from zero and MUST NOT reactivate an old revision's partial progress

### Requirement: Consumption configuration, counters and outcomes are projected separately

The authoritative account automation projection SHALL expose configured mode, effective mode, `policy_revision`, typed snapshot values, view progress, confirmed-like progress, confirmed-join progress, active opportunity and stage, exact bound group and content when available, independent action outcomes, named blockers and last update time as separate facts. It SHALL distinguish configured consumption from effective slow start or another blocker.

Trigger creation, command acceptance, click actuation, notification delivery, `already_liked`, `already_member`, pending approval, ambiguity and submitted-unknown MUST NOT be rendered as a confirmed new like, confirmed new group join or confirmed comment. A stale or unavailable policy/runtime projection SHALL be shown as unknown or unavailable and MUST stop new work rather than fabricate disabled, zero or success.

#### Scenario: Partial counters remain visible
- **WHEN** an account has `3/5` views, `1/2` confirmed likes and `1/2` confirmed joins with no active action
- **THEN** the projection reports all three counters independently with their policy revision

#### Scenario: Unknown join is not a confirmed new membership
- **WHEN** a join was clicked but its platform result is pending or ambiguous
- **THEN** the projection shows the exact pending or unknown outcome and leaves confirmed-join progress unchanged

#### Scenario: Configured mode differs from effective mode
- **WHEN** consumption is configured but active slow start owns the account
- **THEN** the projection shows both configured consumption and effective slow start with its blocker

#### Scenario: Projection failure is not zero progress
- **WHEN** Cloud cannot read current consumption runtime state
- **THEN** the UI shows unavailable or unknown and MUST NOT render all counters as zero

