## RENAMED Requirements

- FROM: `### Requirement: Facebook rule mode is an explicit account-scoped fixed definition`
- TO: `### Requirement: Facebook rule mode uses a global current policy with an account-adopted immutable numeric revision`
- FROM: `### Requirement: One rule batch is created from ten durable unique confirmed reads`
- TO: `### Requirement: One rule batch is created from the adopted durable unique-read threshold`
- FROM: `### Requirement: The batch like targets the tenth content and remains fully risk-gated`
- TO: `### Requirement: The batch like targets the threshold-closing content and remains fully risk-gated`

## MODIFIED Requirements

### Requirement: Facebook rule mode uses a global current policy with an account-adopted immutable numeric revision

The system SHALL provide a Facebook-only rule mode with a fixed action topology and a versioned numeric policy. The topology SHALL retain an independent compiled `definitionSchemaId` and `definitionSchemaVersion` and SHALL remain: each completed collecting threshold creates exactly one rule round that attempts exactly one like, and each round selected by the join cadence additionally attempts exactly one join-contact chain after the like attempt reaches a terminal state. The published numeric policy revision SHALL contain only validated `1..100` integer `viewThreshold` and `joinEveryNRounds` values. Action types, action counts, action order, Prompt construction and all execution gates MUST NOT be configurable through this policy.

Rule-mode enablement SHALL be persisted with the **environment** as its authoritative key, including the fixed definition identity used when configured, while the numeric policy SHALL have one global current published revision with no customer or environment override. Configuration readback SHALL return that persisted `definitionSchemaId`/`definitionSchemaVersion`; Cloud MUST NOT replace a mismatching stored identity with the compiled identity or a numeric current revision. The ordinary environment/customer rule-mode write MUST accept only `{ enabled: boolean }`; it MUST NOT accept a revision, thresholds, cadence numbers, scripts, prompts, action lists or other execution logic. Missing enablement configuration SHALL mean disabled. Writes MUST validate the target environment's authoritative normalized platform, persist atomically with audit fields and return server readback; unsupported, unknown or non-Facebook environments MUST be rejected without a partial write. Enablement MUST be writable and readable for an environment that currently has no bound account.

Runtime resolution SHALL read enablement and the persisted definition identity from the environment that currently binds the executing account. At a new adoption boundary it SHALL read numeric values from that execution target's atomically applied, fresh current revision; nonzero progress and active rounds SHALL use their own complete persisted numeric snapshots. API owner current, target applied current and the account's adopted immutable revision SHALL be projected as separate facts; Cloud MUST NOT substitute compiled-in numeric constants or relabel one revision as another. When reverse resolution yields no unique environment — binding unknown, binding conflict, cross-customer contention or an unreadable environment registry — when the stored definition identity is unknown/mismatched, when the applied current needed for new adoption is missing, unpublished, structurally invalid, stale or incompatible, or when persisted in-flight snapshots are incomplete, the system MUST fail closed with a named blocker and MUST NOT start or advance rule work.

#### Scenario: Facebook environment enables the global current rule policy
- **WHEN** an operator submits `{ enabled: true }` for an authoritative Facebook environment while the global current rule-policy revision is readable
- **THEN** Cloud changes only environment enablement and returns write-after-read truth with `updatedAt`, `updatedBy`, owner current, target applied current/cursor and any current account-adopted revision

#### Scenario: Numeric policy is managed outside the enable write
- **WHEN** a caller submits a rule-mode enable request containing `viewThreshold`, `joinEveryNRounds`, a policy revision or any field other than `enabled`
- **THEN** Cloud rejects the whole request and changes neither enablement nor the global current policy

#### Scenario: Non-Facebook environment is rejected
- **WHEN** an operator attempts to enable Facebook rule mode for a Xiaohongshu, WeChat Channels or unknown-platform environment
- **THEN** the full write is rejected and no rule configuration or runtime progress is created

#### Scenario: Missing configuration is safely off
- **WHEN** a Facebook environment has no rule-mode enablement row
- **THEN** reads report rule mode disabled and MUST NOT create a row or start rule execution

#### Scenario: Unknown policy identity is not disguised as a current definition
- **WHEN** an environment or account references a rule-policy schema or revision that the serving component cannot resolve compatibly
- **THEN** readback names the mismatch or unavailability and runtime MUST NOT report or execute a guessed current policy

#### Scenario: Stored definition mismatch is not replaced by policy identity
- **WHEN** a stored environment rule configuration carries a `definitionSchemaId` or `definitionSchemaVersion` different from the compiled fixed topology
- **THEN** readback and runtime expose a named definition mismatch and fail closed
- **AND** Cloud MUST NOT overwrite it in projection with the compiled definition or the global numeric policy revision

#### Scenario: Unbound environment can be preconfigured
- **WHEN** an owner configures enablement for an owned Facebook environment that has no bound account
- **THEN** Cloud persists and reports enablement plus owner current and the target applied current a future account could adopt, without fabricating an account, adopted revision, progress or effective mode

#### Scenario: Rebinding adopts for the new account without moving old work
- **WHEN** an enabled environment changes its bound account from A to B
- **THEN** account B starts from zero and adopts its execution target's readable applied current revision before its first collecting fact, while account A's in-flight round settles under A and its already-adopted revision
- **AND** neither account inherits or rewrites the other's progress, visited-content set or batch

#### Scenario: Ambiguous reverse resolution fails closed
- **WHEN** the executing account resolves to zero or more than one environment, or the environment registry is unreadable
- **THEN** rule mode does not start or advance and the named blocker is exposed, MUST NOT fall back to any account-keyed legacy configuration or compiled numeric policy

### Requirement: One rule batch is created from the adopted durable unique-read threshold

Rule-mode progress SHALL count only confirmed Facebook `view` facts that include an authoritative account, stable canonical content key, occurrence time, source dedupe key, independent `definitionSchemaId`/`definitionSchemaVersion`, adopted immutable numeric policy revision, snapped `viewThreshold` and `joinEveryNRounds`, and server-injected execution target. Mounted cards, loading placeholders, navigation-only opens, duplicate content within the active round, duplicate message delivery and views observed while another mode owns the account MUST NOT advance progress. Progress, numeric snapshots and facts SHALL be durable across Cloud restart and Edge reconnect.

In one atomic transition, the distinct confirmed read whose ordinal equals the collecting progress row's snapped `viewThreshold` SHALL close the current set, create exactly one rule round with that threshold-closing content as `triggerContentKey`, snapshot the adopted revision and both numeric values onto the round, and advance the progress row to a new round sequence. A repeated apply or competing worker MUST NOT create a second round.

An account with zero collecting progress and no active round SHALL compare its adopted revision with the current revision atomically applied by its execution target before admitting the next view and SHALL atomically adopt that readable applied current when they differ. An API owner publish MAY precede target snapshot application; until the target applies the new snapshot, a still-fresh older applied current remains its honest adoption authority. Once a collecting sequence has accepted any view, it MUST finish that sequence and its resulting round under the existing persisted snapshots; a current change MUST NOT reinterpret the count, move the threshold, alter the round cadence or migrate an active round. Only after that round is terminal and its active pointer is cleared MAY the next zero-progress sequence adopt a newer applied current. An unknown, unpublished, stale, structurally invalid or incompatible applied current needed for adoption, or an incomplete/invalid persisted snapshot needed to resume work, MUST block new collection with a named reason rather than fall back to compiled numbers or require the old policy definition to remain in the current mirror.

#### Scenario: Adopted threshold creates one round
- **WHEN** the distinct eligible confirmed view whose ordinal equals the progress row's snapped `viewThreshold` is applied for one account, target and adopted revision
- **THEN** Cloud creates exactly one round, binds it to that threshold-closing content and resets the next collecting sequence to zero

#### Scenario: Duplicate content does not advance progress
- **WHEN** Edge reconnects or reports a content key already counted in the active collecting sequence
- **THEN** the durable uniqueness constraint keeps the view count unchanged and no extra round is created

#### Scenario: Restart resumes the exact numeric snapshot
- **WHEN** Cloud restarts while an account has nonzero progress below its snapped `viewThreshold`
- **THEN** the account resumes with the same count, adopted revision and threshold, and only the remaining number of unique confirmed views can create that round

#### Scenario: Cards without read proof do not count
- **WHEN** a card is mounted or scrolled past but no platform-specific confirmed-view evidence is produced
- **THEN** rule progress does not advance

#### Scenario: Desired revision changes during collection
- **WHEN** target-applied current revision changes while an account has nonzero collecting progress or an active round
- **THEN** that sequence and round retain the old adopted revision and numeric snapshots through terminal settlement
- **AND** the newer applied revision is adopted only before the next view of a zero-progress sequence after the active-round pointer is clear

#### Scenario: Unknown adoption input or persisted snapshot blocks collection
- **WHEN** Cloud cannot resolve the target applied current needed at an adoption boundary, or the stored definition identity/revision/numeric snapshots are incomplete when resuming nonzero progress
- **THEN** no view is counted and no round is created until the adoption input or exact persisted snapshots are complete and compatible

### Requirement: The batch like targets the threshold-closing content and remains fully risk-gated

Every rule round SHALL attempt its like first and SHALL bind the intent to the threshold-closing confirmed content while that target is current. It MUST NOT search for a better target, revisit an earlier content item from the collecting sequence, or ask a persona appraiser. Immediately before dispatch Cloud MUST enforce the existing `RiskController.explain('like')`, like/view ratio, cooldown, session budget, platform capability, current-target and already-liked gates. Only a platform-confirmed new like SHALL be recorded as confirmed.

#### Scenario: Allowed like is sent to the trigger content
- **WHEN** the threshold-closing content remains current and every like gate allows the action
- **THEN** Cloud sends one like intent for that content and waits for the platform receipt before reporting confirmation

#### Scenario: Like risk rejection is terminal for the round attempt
- **WHEN** the threshold-closing content creates a round but `RiskController.explain('like')` rejects it
- **THEN** the like attempt ends as `risk_suppressed`, no like command is sent and no like debt is carried to a later content

#### Scenario: Already-liked target is not retargeted
- **WHEN** target observation shows the threshold-closing content was already liked
- **THEN** the like attempt ends with the named structural skip and the system MUST NOT pick another content to satisfy the round

### Requirement: Join-contact follows like serially with independent risk decisions

Rule rounds SHALL be numbered by a durable, gap-free, one-based round sequence. After the like attempt reaches a terminal state, a round selected by its snapped adopted policy — `roundSequence` is evenly divisible by `joinEveryNRounds` — SHALL invoke the single Facebook join-contact orchestrator exactly once with `injectContact=true`, `joinFirst=true`, automatic priority, the account's effective approval mode, no manual override and no force flag. A round not selected by that cadence MUST NOT invoke the join-contact orchestrator. The policy MUST NOT configure additional actions, change either action count, reorder join-contact before like, or alter Prompt construction.

Cadence selection SHALL be derived from the durable round sequence and the round's immutable `joinEveryNRounds` snapshot, NOT from the number of platform-confirmed likes or a later owner/applied current revision. A like that ends as `risk_suppressed`, `structural_skip`, `not_started`, `already_satisfied`, `submitted_unknown`, `ambiguous`, `rejected` or `failed` SHALL advance the round sequence exactly as a confirmed like does, so that like-side quota exhaustion MUST NOT silently stop all join and contact-comment work.

`join_group` and `comment` MUST each pass their own just-in-time RiskController, session, daily, contact, approval, dedupe and target gates. The comment stage MUST NOT begin unless the exact group has a platform-confirmed `joined` or `already_member` result.

The like and join-contact outcomes SHALL remain independent and the round MUST support truthful partial completion. A gate rejection, approval rejection, no-target, offline/not-started, ambiguous receipt, failure or submitted-unknown result SHALL terminate that action attempt without creating work debt. While a round is non-terminal, no next round may accumulate for the account.

#### Scenario: Cadence-selected round runs join-contact
- **WHEN** a round selected by its snapped `joinEveryNRounds` reaches a terminal like state
- **THEN** Cloud invokes the join-contact orchestrator exactly once for that round

#### Scenario: Suppressed like still advances the sequence
- **WHEN** the like of a cadence-unscheduled round is rejected by the like gate
- **THEN** the round records the like suppression, performs no join-contact, and the next round's eligibility is derived from its own sequence and adopted policy snapshot

#### Scenario: Like suppressed but join-contact allowed
- **WHEN** the like gate rejects a cadence-selected round but the later join and comment gates allow their actions
- **THEN** the round records the like suppression and MAY complete the join-contact path without relabeling the like as successful

#### Scenario: Join ambiguity prevents comment
- **WHEN** the join stage returns pending, ambiguous, gated, failed or unconfirmed
- **THEN** the comment stage does not start and the round preserves that honest join outcome

#### Scenario: Join confirmed but comment fails
- **WHEN** platform membership is confirmed but the comment is rejected, fails or becomes submitted-unknown
- **THEN** the membership remains confirmed, the comment keeps its own outcome and the overall round is partial rather than successful

#### Scenario: Suppressed round is not replayed after quota reset
- **WHEN** any round action is risk-suppressed and the relevant quota later becomes available
- **THEN** the old action is not replayed; another opportunity requires the cadence to produce a new round

### Requirement: Configuration, progress and platform outcomes are projected separately

The account automation view SHALL expose server-authoritative environment enablement and persisted definition identity, API owner current revision, execution-target applied current revision/cursor/lag, account adopted immutable revision, effective mode, the adopted `viewThreshold` and `joinEveryNRounds` snapshots, dynamic collecting progress in the range zero through one less than `viewThreshold`, the current round's cadence position, whether the current round includes join-contact, current round action states, named blockers and last update time as separate facts. Trigger creation, command acceptance and notification delivery MUST NOT be displayed as a confirmed like, membership or comment. A stale, incompatible or unavailable configuration, revision or progress projection MUST be shown as unknown/unavailable and MUST stop new rule work rather than fabricate disabled, zero, legacy numbers or success.

An action that the adopted cadence does not schedule for the current round MUST be rendered as not applicable to this round. It MUST NOT be rendered as pending, in progress, not started, skipped or failed. When owner current differs from target applied current, the view SHALL identify propagation pending; when applied current differs from the account adopted revision, it SHALL identify safe-boundary adoption pending. Neither state may claim that an in-progress sequence or round has switched.

#### Scenario: Active slow start is visible without fake zero progress
- **WHEN** rule mode is configured but slow start owns the account
- **THEN** the UI shows the configured rule plus `slow_start_active` and does not invent an actively collecting count under either the global current or adopted threshold

#### Scenario: Cadence-unscheduled round is not rendered as two failures
- **WHEN** a round not selected by its snapped `joinEveryNRounds` completes its like and terminates without join-contact
- **THEN** the UI shows join and comment as not applicable to this round and MUST NOT show them as pending, not started or failed

#### Scenario: Pending revision adoption is explicit
- **WHEN** target applied current differs from the revision adopted by a nonzero collecting sequence or active round
- **THEN** the UI shows both identities and the pending-safe-boundary state without recalculating current progress from the applied-current numbers

#### Scenario: Partial round is rendered truthfully
- **WHEN** like is confirmed, join is confirmed and comment is submitted-unknown
- **THEN** the UI shows each distinct outcome and MUST NOT collapse the round to a green success

#### Scenario: Projection failure is not disabled state
- **WHEN** Cloud cannot read current rule configuration, the exact referenced policy revision or progress
- **THEN** the UI shows unavailable/unknown, and the runtime refuses new rule work until the authority is readable

### Requirement: Rounds without join-contact still reach a terminal state and release ownership

A rule round not selected for join-contact by its snapped adopted `joinEveryNRounds` SHALL reach a durable terminal state through the same normal completion path as a join-contact round. Its join and comment legs SHALL be persisted with the dedicated not-applicable action state, and the account's active-round pointer SHALL be cleared in the same transition so that subsequent confirmed views may begin a new collecting sequence.

Terminating a like-only round MUST NOT overwrite the blocker recorded by its like stage. Cloud MUST NOT leave a like-only round non-terminal, and MUST NOT depend on session-boundary reconciliation or process restart recovery as its normal termination path.

#### Scenario: Like-only round terminates and browsing continues
- **WHEN** a cadence-unscheduled round's like reaches any terminal state
- **THEN** the round is persisted as terminal with join and comment marked not applicable, the active-round pointer is cleared, and the next eligible confirmed view advances a new sequence under the revision adopted at that safe boundary

#### Scenario: Like blocker survives round termination
- **WHEN** a cadence-unscheduled round's like ends as `risk_suppressed` with a named blocker
- **THEN** the terminal round still exposes that like blocker and MUST NOT replace it with a cadence-related reason

#### Scenario: Like-only rounds do not deadlock browsing
- **WHEN** many consecutive cadence-unscheduled rounds complete for one account
- **THEN** no round remains non-terminal, view counting never stalls, and recovery paths are not required to unblock the account
