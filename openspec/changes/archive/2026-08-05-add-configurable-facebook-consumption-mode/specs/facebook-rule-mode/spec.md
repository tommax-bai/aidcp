## MODIFIED Requirements

### Requirement: Facebook rule mode is an explicit account-scoped fixed definition

The system SHALL provide a Facebook-only rule mode selected by the authoritative environment-scoped Facebook operation policy. Each rule policy revision SHALL contain an immutable, typed snapshot with `rule.viewsPerLike` as an integer from `1..100` and `rule.joinEveryNRounds` as an integer from `1..20`. The migration snapshot for an existing enabled rule environment SHALL preserve the current behavior with values `5` and `2`. Operators MUST NOT supply scripts, prompts, action lists, arbitrary graphs or other free-form execution logic.

Rule policy writes MUST validate the environment's authoritative normalized platform, use the operation policy's compare-and-swap revision contract, persist the new snapshot atomically with audit fields, and return authoritative write-after-read truth. Unsupported, unknown or non-Facebook environments, stale expected revisions, unknown snapshot schema versions and out-of-range values MUST be rejected without a partial write. A Facebook environment that currently has no bound account MAY be preconfigured.

Configuration readback SHALL report the exact policy revision and snapshot persisted in the authoritative row. Cloud MUST NOT substitute compiled defaults for a missing, unreadable or unsupported snapshot; such a condition SHALL be surfaced as a named projection blocker and MUST prevent new rule execution.

Runtime resolution SHALL read the policy of the environment that currently binds the executing account. When reverse resolution yields no unique environment because of an unknown binding, binding conflict, cross-customer contention or unreadable environment registry, the system MUST fail closed with a named blocker and MUST NOT infer rule admission from an account-keyed legacy value.

#### Scenario: Existing rule environment migrates without a cadence change
- **WHEN** an existing Facebook environment with the fixed rule enabled is migrated to the operation policy
- **THEN** Cloud creates an audited rule policy revision whose snapshot has `rule.viewsPerLike=5` and `rule.joinEveryNRounds=2`
- **AND** runtime cutover follows policy-revision isolation without changing the configured cadence

#### Scenario: Operator stores a bounded rule snapshot
- **WHEN** an operator writes valid rule cadence values with the current expected policy revision for an authoritative Facebook environment
- **THEN** Cloud atomically publishes a new immutable policy revision and returns that exact revision and snapshot

#### Scenario: Stale or invalid write is rejected
- **WHEN** an operator supplies a stale expected revision, an unknown field, a non-integer value or a value outside the server-provided bounds
- **THEN** the full write is rejected and the previously active policy revision remains unchanged

#### Scenario: Non-Facebook environment is rejected
- **WHEN** an operator attempts to select rule mode for a Xiaohongshu, WeChat Channels or unknown-platform environment
- **THEN** the full write is rejected and no rule configuration or runtime progress is created

#### Scenario: Missing or unsupported snapshot fails closed
- **WHEN** an environment selects rule mode but its snapshot is missing, unreadable or uses an unsupported schema version
- **THEN** reads expose a named blocker and Cloud MUST NOT create or advance rule work with compiled fallback values

#### Scenario: Unbound environment can be preconfigured
- **WHEN** an owner publishes a valid rule policy for an owned Facebook environment that has no bound account
- **THEN** Cloud persists the environment policy and reports it as configured but not currently executing
- **AND** Cloud MUST NOT fabricate an account, progress row or effective runtime mode

#### Scenario: Rebinding carries policy but not runtime state
- **WHEN** an environment with a rule policy changes its bound account from A to B
- **THEN** the environment policy remains unchanged and account B is evaluated against it
- **AND** account A's progress and batch state MUST NOT be reassigned to account B

#### Scenario: Ambiguous reverse resolution fails closed
- **WHEN** an executing account resolves to zero or more than one environment or the environment registry is unreadable
- **THEN** rule mode does not start or advance and the named blocker is exposed
- **AND** Cloud MUST NOT fall back to an account-keyed legacy configuration

### Requirement: One rule batch is created from ten durable unique confirmed reads

Rule-mode progress SHALL count only confirmed Facebook `view` facts that include an authoritative account, stable canonical content key, occurrence time, source dedupe key, policy revision and server-injected execution target. Mounted cards, loading placeholders, navigation-only opens, duplicate content within the collecting set, duplicate message delivery and views observed while another effective mode owns the account MUST NOT advance progress. Progress and facts SHALL be durable across Cloud restart and Edge reconnect.

For the immutable snapshot value `N=rule.viewsPerLike`, one atomic transition SHALL cause the Nth unique confirmed read to close the current set, create exactly one rule round with that content as `triggerContentKey`, and reset collection for the next round under the same policy revision. A repeated apply or competing worker MUST NOT create a second round.

#### Scenario: Configured number of unique confirmed reads creates one round
- **WHEN** the Nth distinct eligible confirmed view for one account, execution target and policy revision is applied
- **THEN** Cloud creates exactly one round, binds it to the Nth content and resets the next collecting count to zero

#### Scenario: Duplicate content does not advance progress
- **WHEN** Edge reconnects or reports a content key already counted in the active collecting set
- **THEN** the durable uniqueness constraint keeps the view count unchanged and no extra round is created

#### Scenario: Restart resumes exact configured progress
- **WHEN** Cloud restarts with `K` eligible views durably recorded for a snapshot whose `rule.viewsPerLike` is `N` and `K < N`
- **THEN** the account resumes at `K/N` for that account, execution target and policy revision
- **AND** exactly `N-K` new unique confirmed views create the next round

#### Scenario: Cards without read proof do not count
- **WHEN** a card is mounted or scrolled past but no platform-specific confirmed-view evidence is produced
- **THEN** rule progress does not advance

### Requirement: The batch like targets the tenth content and remains fully risk-gated

Every rule round SHALL attempt its like first and SHALL bind the intent to the Nth confirmed content selected by its immutable `rule.viewsPerLike=N` snapshot while that target is current. It MUST NOT search for a better target, revisit an earlier content in the collecting set or ask a persona appraiser. Immediately before dispatch Cloud MUST enforce the existing `RiskController.explain('like')`, like/view ratio, cooldown, session budget, platform capability, current-target and already-liked gates. Only a platform-confirmed new like SHALL be recorded as confirmed.

#### Scenario: Allowed like is sent to the configured trigger content
- **WHEN** the Nth content remains current and every like gate allows the action
- **THEN** Cloud sends one like intent for that exact content and waits for the platform receipt before reporting confirmation

#### Scenario: Like risk rejection is terminal for the round attempt
- **WHEN** the Nth content creates a round but `RiskController.explain('like')` rejects it
- **THEN** the like attempt ends as `risk_suppressed`, no like command is sent and no like debt is carried to a later content

#### Scenario: Already-liked target is not retargeted
- **WHEN** target observation shows the Nth content was already liked
- **THEN** the like attempt ends with the named structural outcome and the system MUST NOT pick another content to satisfy the round

### Requirement: Join-contact follows like serially with independent risk decisions

Rule rounds SHALL be numbered by a durable, gap-free sequence within one account, execution target and policy revision. For the immutable snapshot value `M=rule.joinEveryNRounds`, after the like attempt reaches a terminal state every Mth round SHALL invoke the existing Facebook join-contact orchestrator with `injectContact=true`, `joinFirst=true`, automatic priority, the account's effective approval mode, no manual override and no force flag. Other rounds in the M-round cycle MUST NOT invoke that orchestrator.

Cycle position SHALL be derived from the round sequence within the policy revision, NOT from the number of platform-confirmed likes. A like that ends as `risk_suppressed`, `structural_skip`, `not_started`, `already_satisfied`, `submitted_unknown`, `ambiguous`, `rejected` or `failed` SHALL consume its round position exactly as a confirmed like does, so like-side quota exhaustion MUST NOT silently stop all join and contact-comment opportunities.

`join_group` and `comment` MUST each pass their existing independent just-in-time RiskController, session, daily, contact, approval, dedupe and exact-target gates. The comment stage MUST NOT begin unless the exact group has a platform-confirmed `joined` or `already_member` result.

The like and join-contact outcomes SHALL remain independent and the round MUST support truthful partial completion. A gate rejection, approval rejection, no-target, offline/not-started, ambiguous receipt, failure or submitted-unknown result SHALL terminate that action attempt without creating work debt. While a round is non-terminal, no next round may accumulate for the account.

#### Scenario: Configured cycle position runs join-contact
- **WHEN** a round whose sequence is divisible by `rule.joinEveryNRounds` reaches a terminal like state
- **THEN** Cloud invokes the join-contact orchestrator exactly once for that round

#### Scenario: Other cycle positions do not run join-contact
- **WHEN** a round whose sequence is not divisible by `rule.joinEveryNRounds` reaches a terminal like state
- **THEN** Cloud persists join and comment as not applicable and does not invoke the join-contact orchestrator

#### Scenario: Suppressed like still consumes its cycle position
- **WHEN** a round's like is rejected by the like gate
- **THEN** the round preserves the like suppression and its sequence still determines whether that same round includes join-contact

#### Scenario: Like suppressed but join-contact allowed
- **WHEN** the like gate rejects a round that is due for join-contact but the later join and comment gates allow their actions
- **THEN** the round records the like suppression and MAY complete the join-contact path without relabeling the like as successful

#### Scenario: Join ambiguity prevents comment
- **WHEN** the join stage returns pending, ambiguous, gated, failed or unconfirmed
- **THEN** the comment stage does not start and the round preserves that honest join outcome

#### Scenario: Join confirmed but comment fails
- **WHEN** platform membership is confirmed but the comment is rejected, fails or becomes submitted-unknown
- **THEN** the membership remains confirmed, the comment keeps its own outcome and the overall round is partial rather than successful

#### Scenario: Suppressed round is not replayed after quota reset
- **WHEN** any round action is risk-suppressed and the relevant quota later becomes available
- **THEN** the old action is not replayed and another opportunity requires the configured cadence to produce a new round

### Requirement: Configuration, progress and platform outcomes are projected separately

The account automation view SHALL expose the server-authoritative rule policy revision and snapshot, effective mode, `collectedViews/rule.viewsPerLike` progress, the current round's position within `rule.joinEveryNRounds`, whether the current round includes join-contact, current round action states, named blockers and last update time as separate facts. Trigger creation, command acceptance and notification delivery MUST NOT be displayed as a confirmed like, membership or comment. A stale or unavailable policy/progress projection MUST be shown as unknown or unavailable and MUST stop new rule work rather than fabricate disabled, zero or success.

An action that the configured cadence does not schedule for the current round MUST be rendered as not applicable to this round. It MUST NOT be rendered as pending, in progress, not started, skipped or failed.

#### Scenario: Active slow start is visible without fake zero progress
- **WHEN** rule mode is configured but slow start owns the account
- **THEN** the UI shows the configured policy revision plus `slow_start_active`
- **AND** it does not pretend an actively collecting rule is at zero

#### Scenario: Like-only round is not rendered as two failures
- **WHEN** a round not due for join-contact completes its like and terminates
- **THEN** the UI shows join and comment as not applicable to that round
- **AND** it MUST NOT show them as pending, not started or failed

#### Scenario: Partial round is rendered truthfully
- **WHEN** like is confirmed, join is confirmed and comment is submitted-unknown
- **THEN** the UI shows each distinct outcome and MUST NOT collapse the round to a green success

#### Scenario: Projection failure is not disabled state
- **WHEN** Cloud cannot read the current rule policy snapshot or runtime progress
- **THEN** the UI shows unavailable or unknown and the runtime refuses new rule work until the authority is readable

### Requirement: Rounds without join-contact still reach a terminal state and release ownership

A rule round whose configured cycle position does not schedule join-contact SHALL reach a durable terminal state through the same normal completion path as a join-contact round. Its join and comment legs SHALL be persisted with the dedicated not-applicable action state, and the account's active-round pointer SHALL be cleared in the same transition so subsequent confirmed views resume counting.

Terminating a like-only round MUST NOT overwrite the blocker recorded by its like stage. Cloud MUST NOT leave a like-only round non-terminal and MUST NOT depend on session-boundary reconciliation or process restart recovery as its normal termination path.

#### Scenario: Like-only round terminates and browsing continues
- **WHEN** a round not due for join-contact reaches any terminal like state
- **THEN** the round is persisted as terminal with join and comment marked not applicable
- **AND** the active-round pointer is cleared so the next confirmed view advances the new collecting count

#### Scenario: Like blocker survives round termination
- **WHEN** a like-only round ends as `risk_suppressed` with a named blocker
- **THEN** the terminal round still exposes that like blocker and MUST NOT replace it with a cadence-related reason

#### Scenario: Like-only rounds do not deadlock browsing
- **WHEN** many consecutive rounds not due for join-contact complete for one account
- **THEN** no round remains non-terminal, view counting never stalls and recovery paths are not required to unblock the account

## ADDED Requirements

### Requirement: Rule runtime is isolated by immutable policy revision

Rule progress, confirmed-view facts, round sequences, active-round ownership and terminal outcomes SHALL be keyed and deduplicated by `account_id + execution_target + policy_revision`. The runtime SHALL retain the exact immutable snapshot used to create each round and MUST NOT reinterpret old facts or an active round with values from a newer revision.

Publishing a new rule policy revision SHALL stop new collection under the old revision. Partial collecting progress from the old revision MUST NOT carry forward. An already dispatched old-revision action SHALL settle truthfully under its old snapshot. Any old-revision intent that has not reached irreversible dispatch SHALL terminate as `policy_superseded` and MUST NOT start another stage. The new revision SHALL begin at zero only after the old round is terminal and account single-flight ownership is released.

#### Scenario: Partial collection is not reinterpreted
- **WHEN** an account has three confirmed views under a revision with `rule.viewsPerLike=5` and an operator publishes a revision with value `7`
- **THEN** the new revision begins at `0/7`
- **AND** the three old-revision facts remain historical and MUST NOT count toward the new threshold

#### Scenario: Active old round settles before new collection
- **WHEN** a rule round is active under revision R1 while revision R2 is published
- **THEN** any already dispatched R1 action settles truthfully while every undispatched R1 intent becomes `policy_superseded`
- **AND** R2 starts at zero only after the R1 round is terminal and releases ownership

#### Scenario: Duplicate fact cannot cross revisions
- **WHEN** the same view fact or round transition is delivered more than once around a policy revision change
- **THEN** source and transition idempotency produce at most one effect within the matching account, execution target and revision
- **AND** no delivery advances both revisions

### Requirement: Configurable rule cadence does not weaken existing safety gates

Changing rule cadence values SHALL affect only when a rule opportunity is created. Active slow-start precedence, authoritative environment binding, weekly active-window admission, account single-flight, content safety, RiskController, ratio, cooldown, session and daily budgets, platform capability, contact requirements, approval, dedupe, exact-target validation and truthful platform outcome handling SHALL remain in force. A policy value MUST NOT reserve quota, authorize an action or convert an unknown outcome into success.

#### Scenario: Active slow start still suppresses configured rule mode
- **WHEN** a valid rule policy exists but the account's authoritative slow-start lifecycle is active
- **THEN** rule progress and new rule action dispatch remain stopped with the named slow-start blocker

#### Scenario: Threshold completion does not bypass a risk gate
- **WHEN** configured progress reaches an action threshold while its just-in-time RiskController decision rejects the action
- **THEN** Cloud records the truthful rejection, dispatches no prohibited action and creates no retry debt

#### Scenario: Configured join-contact still obeys approval
- **WHEN** a configured join-contact round reaches a comment whose effective approval mode requires review
- **THEN** Cloud waits for valid approval and MUST NOT submit the comment merely because the cadence threshold was reached
