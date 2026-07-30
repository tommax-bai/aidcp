# facebook-rule-mode Specification

## Purpose
TBD - created by archiving change facebook-rule-mode-cadence. Update Purpose after archive.
## Requirements
### Requirement: Facebook rule mode is an explicit account-scoped fixed definition

The system SHALL provide a Facebook-only rule mode with the fixed versioned definition `facebook_browse_5_like_1_join_contact_every_2@2`, expressing a two-tier cadence: every five durable unique confirmed reads open one rule round that attempts one like, and every second round additionally attempts one join-contact. It SHALL be persisted with the **environment** as its authoritative key. The only operator choice SHALL be enabled or disabled; operators MUST NOT supply scripts, prompts, thresholds, cadence numbers, action lists or other free-form execution logic. Missing configuration SHALL mean disabled. Writes MUST validate the target environment's authoritative normalized platform, persist atomically with audit fields and return server readback; unsupported, unknown or non-Facebook environments MUST be rejected without a partial write. Configuration MUST be writable and readable for an environment that currently has no bound account.

Configuration readback SHALL report the definition identity persisted in the authoritative row. Cloud MUST NOT substitute the compiled-in definition constants for a stored row whose definition identity differs; a mismatch SHALL be surfaced as a named projection problem rather than silently rendered as the current definition.

Runtime resolution SHALL read the configuration of the environment that currently binds the executing account. When that reverse resolution yields no unique environment — binding unknown, binding conflict, cross-customer contention or an unreadable environment registry — the system MUST fail closed to "rule mode not enabled" with a named blocker and MUST NOT infer enablement from any account-keyed legacy value.

#### Scenario: Facebook environment enables the fixed rule
- **WHEN** an operator enables rule mode for an authoritative Facebook environment
- **THEN** Cloud persists the fixed definition version against that environment and returns the write-after-read truth with `updatedAt` and `updatedBy`

#### Scenario: Non-Facebook environment is rejected
- **WHEN** an operator attempts to enable Facebook rule mode for a Xiaohongshu, WeChat Channels or unknown-platform environment
- **THEN** the full write is rejected and no rule configuration or runtime progress is created

#### Scenario: Missing configuration is safely off
- **WHEN** a Facebook environment has no rule-mode configuration row
- **THEN** reads report rule mode disabled and MUST NOT create a row or start rule execution

#### Scenario: Stored definition mismatch is not disguised as the current definition
- **WHEN** a stored rule configuration row carries a definition identity other than the current one
- **THEN** readback names the mismatch and MUST NOT report that row as configured for the current definition

#### Scenario: Unbound environment can be preconfigured
- **WHEN** an owner enables rule mode for an owned Facebook environment that has no bound account yet
- **THEN** Cloud persists the environment configuration and reports it as configured but not currently executing, MUST NOT fabricate an account, progress or effective mode

#### Scenario: Rebinding carries configuration to the new account
- **WHEN** an environment with rule mode enabled changes its bound account from A to B
- **THEN** the environment configuration stays byte-for-byte unchanged and account B is admitted under it, while account A is no longer governed by it, MUST NOT require a restart

#### Scenario: Ambiguous reverse resolution fails closed
- **WHEN** the executing account resolves to zero or more than one environment, or the environment registry is unreadable
- **THEN** rule mode does not start or advance and the named blocker is exposed, MUST NOT fall back to any account-keyed legacy configuration

### Requirement: Active slow start has absolute precedence over rule mode

Cloud SHALL resolve the effective browse mode from the authoritative slow-start projection before starting or advancing Facebook rule mode. `slowStart.state=active` MUST prevent rule-mode session start, unique-view progress and new rule action dispatch regardless of `binding`. `state=off` or `state=graduated` MAY allow rule mode only when its account configuration, active window and all other admission gates pass. A slow-start projection with `binding_unknown`, `binding_conflict`, `platform_unknown` or `platform_unsupported` MUST fail closed and MUST NOT be interpreted as slow start being off.

#### Scenario: Active slow start suppresses rule mode
- **WHEN** a Facebook account has rule mode enabled and its authoritative slow-start state is `active`
- **THEN** slow start owns the account, rule mode does not start or advance, and the UI reports `slow_start_active`

#### Scenario: Binding false does not weaken precedence
- **WHEN** slow start reports `state=active` and `binding=false` because the current risk tier is already equally or more restrictive
- **THEN** rule mode remains inactive because precedence is based on the active lifecycle state, not the numeric clamp delta

#### Scenario: Graduated slow start allows rule admission
- **WHEN** a Facebook account's slow-start state changes from `active` to `graduated` while rule mode remains enabled
- **THEN** subsequent active-window admission MAY start rule mode without counting any views observed while slow start was active

#### Scenario: Unknown slow-start truth fails closed
- **WHEN** the slow-start projection is unavailable, stale, binding-unknown or binding-conflicted
- **THEN** Cloud starts neither rule mode nor a guessed fallback mode and exposes the named blocker

### Requirement: Rule browsing does not use persona relevance or interaction preference

For an account admitted to Facebook rule mode, Cloud SHALL select structurally eligible unseen Facebook content in reported order without reading Soul identity, interests, like affinity or `mandatory_interactions`, and without invoking the persona relevance or persona interaction appraisers. The account MUST still satisfy the existing bound-persona admission requirement. Login/challenge/consent checks, canonical content identity, duplicate/visited checks, a Soul-free prohibited-content safety gate, platform capability, pacing, target validation and post-action verification MUST remain in force.

#### Scenario: Persona mismatch does not skip a rule-mode card
- **WHEN** the next safe, structurally valid unseen Facebook content is unrelated to the bound persona's interests
- **THEN** rule mode MAY browse it without calling the persona content evaluator

#### Scenario: Mandatory persona rule does not redirect selection
- **WHEN** the bound Soul contains a `mandatory_interactions` rule and rule mode is active
- **THEN** that rule does not prioritize a card, create an interaction intent or alter the fixed rule cadence

#### Scenario: Safety rejection still blocks a card
- **WHEN** a structurally visible card fails the Soul-free prohibited-content or page-identity safety gate
- **THEN** rule mode rejects it with a named reason and does not count it or act on it

#### Scenario: Unbound account remains rejected
- **WHEN** a Facebook account has rule mode enabled but no bound persona
- **THEN** the existing persona admission gate rejects session start and the system MUST NOT substitute a default persona

### Requirement: One rule batch is created from ten durable unique confirmed reads

Rule-mode progress SHALL count only confirmed Facebook `view` facts that include an authoritative account, stable canonical content key, occurrence time, source dedupe key, rule definition version and server-injected execution target. Mounted cards, loading placeholders, navigation-only opens, duplicate content within the active round, duplicate message delivery and views observed while another mode owns the account MUST NOT advance progress. Progress and facts SHALL be durable across Cloud restart and Edge reconnect.

In one atomic transition, the **fifth** unique confirmed read SHALL close the current set, create exactly one rule round with the fifth content as `triggerContentKey`, and advance the progress row to a new round sequence. A repeated apply or competing worker MUST NOT create a second round.

#### Scenario: Five unique confirmed reads create one round
- **WHEN** the fifth distinct eligible confirmed view for one account, target and definition version is applied
- **THEN** Cloud creates exactly one round, binds it to that fifth content and resets the next collecting sequence to zero

#### Scenario: Duplicate content does not advance progress
- **WHEN** Edge reconnects or reports a content key already counted in the active round
- **THEN** the durable uniqueness constraint keeps the view count unchanged and no extra round is created

#### Scenario: Restart resumes exact progress
- **WHEN** Cloud restarts after three eligible views
- **THEN** the account resumes at `3/5` for that rule revision and two new unique confirmed views create the next round

#### Scenario: Cards without read proof do not count
- **WHEN** a card is mounted or scrolled past but no platform-specific confirmed-view evidence is produced
- **THEN** rule progress does not advance

### Requirement: The batch like targets the tenth content and remains fully risk-gated

Every rule round SHALL attempt its like first and SHALL bind the intent to the **fifth** confirmed content while that target is current. It MUST NOT search for a better target, revisit one of the preceding four, or ask a persona appraiser. Immediately before dispatch Cloud MUST enforce the existing `RiskController.explain('like')`, like/view ratio, cooldown, session budget, platform capability, current-target and already-liked gates. Only a platform-confirmed new like SHALL be recorded as confirmed.

#### Scenario: Allowed like is sent to the trigger content
- **WHEN** the fifth content remains current and every like gate allows the action
- **THEN** Cloud sends one like intent for that content and waits for the platform receipt before reporting confirmation

#### Scenario: Like risk rejection is terminal for the round attempt
- **WHEN** the fifth content creates a round but `RiskController.explain('like')` rejects it
- **THEN** the like attempt ends as `risk_suppressed`, no like command is sent and no like debt is carried to a later content

#### Scenario: Already-liked target is not retargeted
- **WHEN** target observation shows the fifth content was already liked
- **THEN** the like attempt ends with the named structural skip and the system MUST NOT pick another content to satisfy the round

### Requirement: Join-contact follows like serially with independent risk decisions

Rule rounds SHALL be numbered by a durable, gap-free round sequence. After the like attempt reaches a terminal state, a round whose position in the fixed two-round cycle is the second SHALL invoke the single Facebook join-contact orchestrator with `injectContact=true`, `joinFirst=true`, automatic priority, the account's effective approval mode, no manual override and no force flag. A round in the first position of the cycle MUST NOT invoke the join-contact orchestrator.

Round-cycle position SHALL be derived from the round sequence, NOT from the number of platform-confirmed likes. A like that ends as `risk_suppressed`, `structural_skip`, `not_started`, `already_satisfied`, `submitted_unknown`, `ambiguous`, `rejected` or `failed` SHALL advance the cycle exactly as a confirmed like does, so that like-side quota exhaustion MUST NOT silently stop all join and contact-comment work.

`join_group` and `comment` MUST each pass their own just-in-time RiskController, session, daily, contact, approval, dedupe and target gates. The comment stage MUST NOT begin unless the exact group has a platform-confirmed `joined` or `already_member` result.

The like and join-contact outcomes SHALL remain independent and the round MUST support truthful partial completion. A gate rejection, approval rejection, no-target, offline/not-started, ambiguous receipt, failure or submitted-unknown result SHALL terminate that action attempt without creating work debt. While a round is non-terminal, no next round may accumulate for the account.

#### Scenario: Second round of the cycle runs join-contact
- **WHEN** a round in the second cycle position reaches a terminal like state
- **THEN** Cloud invokes the join-contact orchestrator exactly once for that round

#### Scenario: Suppressed like still advances the cycle
- **WHEN** the like of a first-position round is rejected by the like gate
- **THEN** the round records the like suppression, performs no join-contact, and the next round is the second cycle position and remains eligible for join-contact

#### Scenario: Like suppressed but join-contact allowed
- **WHEN** the like gate rejects a second-position round but the later join and comment gates allow their actions
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

### Requirement: Rule mode inherits the active window and account single-flight

Facebook rule mode SHALL use the account's effective weekly active window for session start, resume and safe termination. It MUST NOT use content-active hour cells, hash-minute offsets or the content scheduler's hour-cell idempotency as the view-count trigger. Browse, like and join-contact work SHALL share the account's existing logical single-flight and browser task ownership; round approval waits MAY release the physical browser but MUST retain logical round ownership.

#### Scenario: Sleeping schedule prevents rule start
- **WHEN** rule mode is enabled but the account's effective weekly active cell is sleeping
- **THEN** no rule session starts and progress remains unchanged

#### Scenario: Entering a sleep cell stops at a safe boundary
- **WHEN** a running rule session crosses into a sleeping active-window cell
- **THEN** Cloud stops new reads and undispatched actions at the existing safe boundary without rewriting dispatched outcomes

#### Scenario: Pending round blocks another periodic source
- **WHEN** a rule round is waiting for approval or another terminal result
- **THEN** the account retains logical ownership and another schedule or rule tick MUST NOT create concurrent work

### Requirement: Configuration, progress and platform outcomes are projected separately

The account automation view SHALL expose server-authoritative rule configuration, effective mode, `0..4/5` collecting progress, the current round's position in the fixed two-round cycle, whether the current round includes join-contact, current round action states, named blockers and last update time as separate facts. Trigger creation, command acceptance and notification delivery MUST NOT be displayed as a confirmed like, membership or comment. A stale or unavailable configuration/progress projection MUST be shown as unknown/unavailable and MUST stop new rule work rather than fabricate disabled, zero or success.

An action that the cadence does not schedule for the current round MUST be rendered as not applicable to this round. It MUST NOT be rendered as pending, in progress, not started, skipped or failed.

#### Scenario: Active slow start is visible without fake zero progress
- **WHEN** rule mode is configured but slow start owns the account
- **THEN** the UI shows the configured rule plus `slow_start_active` and does not pretend an actively collecting rule is at `0/5`

#### Scenario: Like-only round is not rendered as two failures
- **WHEN** a first-position round completes its like and terminates without join-contact
- **THEN** the UI shows join and comment as not applicable to this round and MUST NOT show them as pending, not started or failed

#### Scenario: Partial round is rendered truthfully
- **WHEN** like is confirmed, join is confirmed and comment is submitted-unknown
- **THEN** the UI shows each distinct outcome and MUST NOT collapse the round to a green success

#### Scenario: Projection failure is not disabled state
- **WHEN** Cloud cannot read current rule configuration or progress
- **THEN** the UI shows unavailable/unknown, and the runtime refuses new rule work until the authority is readable

### Requirement: Rounds without join-contact still reach a terminal state and release ownership

A rule round whose cycle position does not schedule join-contact SHALL reach a durable terminal state through the same normal completion path as a join-contact round. Its join and comment legs SHALL be persisted with the dedicated not-applicable action state, and the account's active-round pointer SHALL be cleared in the same transition so that subsequent confirmed views resume counting.

Terminating a like-only round MUST NOT overwrite the blocker recorded by its like stage. Cloud MUST NOT leave a like-only round non-terminal, and MUST NOT depend on session-boundary reconciliation or process restart recovery as its normal termination path.

#### Scenario: Like-only round terminates and browsing continues
- **WHEN** a first-position round's like reaches any terminal state
- **THEN** the round is persisted as terminal with join and comment marked not applicable, the active-round pointer is cleared, and the next confirmed view advances the new round's view count

#### Scenario: Like blocker survives round termination
- **WHEN** a first-position round's like ends as `risk_suppressed` with a named blocker
- **THEN** the terminal round still exposes that like blocker and MUST NOT replace it with a cadence-related reason

#### Scenario: Like-only round does not deadlock browsing
- **WHEN** many consecutive first-position rounds complete for one account
- **THEN** no round remains non-terminal, view counting never stalls, and recovery paths are not required to unblock the account

### Requirement: The rule round comment leg distinguishes contact comments from fallback plain comments

When a Facebook rule round reaches its comment stage for an account with no configured contact info, Cloud SHALL declare the plain-comment fallback explicitly and SHALL record the resulting comment as a distinguishable outcome. A confirmed fallback comment MUST NOT be projected as a confirmed contact comment.

The rule round SHALL preserve which of the two happened across restart and reconnect, and the account automation view, panel API and client MUST render the distinction. A stale or unreadable projection MUST be shown as unknown rather than resolved to either outcome.

Declaring the fallback SHALL NOT weaken any other gate: join and comment MUST each still pass their own just-in-time risk, session, daily, approval, dedupe and target gates, and the comment stage MUST still require a platform-confirmed `joined` or `already_member` result for the exact group.

#### Scenario: Fallback comment is not reported as a contact comment
- **WHEN** a rule round's comment stage posts a plain comment because the account has no contact info
- **THEN** the round records a fallback-comment outcome and the projection MUST NOT show a confirmed contact comment

#### Scenario: Contact comment keeps its own outcome
- **WHEN** a rule round's comment stage posts a comment with the account's configured contact info
- **THEN** the round records a contact-comment outcome distinct from the fallback outcome

#### Scenario: Fallback still requires confirmed membership
- **WHEN** the fallback is declared but the join stage returns pending, ambiguous, gated, failed or unconfirmed
- **THEN** the comment stage does not start and the round preserves the honest join outcome

#### Scenario: Fallback does not bypass approval
- **WHEN** the fallback comment's effective approval mode requires human review
- **THEN** the round waits for approval and MUST NOT post on the strength of the contact-comment lane's authorization

### Requirement: Rule-mode configuration surfaces the fallback consequence at write time

The Facebook rule-mode configuration write path SHALL accept an account with no configured contact info rather than rejecting it, and its authoritative readback SHALL carry a named note stating that this account's join-contact leg will fall back to a plain comment. The note SHALL be derived from server-side truth at read time and MUST NOT be cached client-side as a configuration value.

#### Scenario: Enabling rule mode without contact info is allowed but annotated
- **WHEN** an operator enables rule mode for a Facebook account that has no contact info configured
- **THEN** the write succeeds and the readback names the plain-comment fallback consequence

#### Scenario: Adding contact info clears the note
- **WHEN** contact info is later configured for that account
- **THEN** a subsequent readback no longer carries the fallback note

### Requirement: Rule-mode join-contact preflights comment capacity before joining

Before a Facebook rule round dispatches its join-contact orchestrator, Cloud SHALL preflight both the comment `RiskController` decision and the active session comment budget. If either is unavailable, blocked or exhausted, the round MUST terminate without dispatching a group join and MUST persist a truthful partial outcome with `join_state=not_started`, `comment_state=risk_suppressed` and the stable blocker.

The preflight MUST NOT reserve quota or replace the existing just-in-time comment gates. After membership is confirmed and immediately before comment submission, Cloud SHALL re-read the comment gate so a state or quota change fails closed.

#### Scenario: Daily comment quota is full before join

- **WHEN** a rule round reaches its join-contact position and `RiskController.explain('comment')` returns `quota:day`
- **THEN** Cloud MUST NOT dispatch the group join
- **AND** the round records `join_state=not_started`, `comment_state=risk_suppressed` and `blocker=quota:day`

#### Scenario: Comment session budget is exhausted before join

- **WHEN** the durable safety quota allows comment but the active session has no remaining comment budget
- **THEN** Cloud MUST NOT dispatch the group join
- **AND** the round records the stable `comment_session_budget` blocker

#### Scenario: Admission changes after preflight

- **WHEN** the comment preflight allowed the round but the just-in-time comment gate rejects after membership confirmation or before submission
- **THEN** Cloud MUST preserve the confirmed join outcome, MUST NOT submit the comment and MUST report the current rejection reason

### Requirement: Rule-mode result notifications identify their real source

Combined join-comment result notifications created by `facebook_rule_batch` SHALL identify themselves as `Facebook 规则模式`. They MUST NOT use the default manual `/comment` command label. Manual `/comment` result notifications SHALL retain their existing command label.

#### Scenario: Automatic rule result is not presented as a manual command

- **WHEN** a Facebook rule batch produces a combined join-comment terminal notification
- **THEN** the notification source is `Facebook 规则模式`
- **AND** the card MUST NOT claim that an operator issued `/comment`

#### Scenario: Manual command keeps its label

- **WHEN** an operator-issued `/comment --join` produces a combined result notification
- **THEN** the notification continues to identify the manual `/comment` source

### Requirement: Rule progress, view dedupe and batch outcomes remain account-keyed

Rule collecting progress, unique-view dedupe facts and batch terminal states SHALL continue to be persisted and deduplicated per account, execution target and rule definition version. They MUST NOT be migrated to, mirrored onto, or resolved through the environment key. When an environment's bound account changes, the new account SHALL start collecting from zero and SHALL NOT inherit the previous account's visited-content set or in-flight batch.

#### Scenario: New account starts from zero after rebinding
- **WHEN** an environment with rule mode enabled rebinds from account A part-way through a collecting round to account B
- **THEN** account B begins at zero collected reads with an empty visited-content set and MUST NOT skip content solely because account A had already viewed it

#### Scenario: In-flight batch does not survive rebinding
- **WHEN** account A has an open rule batch at the moment its environment rebinds to account B
- **THEN** account A's batch settles under its own account key with a truthful terminal state and MUST NOT be continued, reassigned or reported under account B

#### Scenario: Progress is not resolved through the environment
- **WHEN** progress or dedupe is read for an executing account
- **THEN** the lookup uses the account key directly and MUST NOT depend on environment reverse resolution succeeding

