## ADDED Requirements

### Requirement: Facebook rule mode is an explicit account-scoped fixed definition

The system SHALL provide a Facebook-only account rule mode with the fixed versioned definition `facebook_browse_10_like_1_join_contact_1@1`. The only v1 operator choice SHALL be enabled or disabled; operators MUST NOT supply scripts, prompts, thresholds, action lists or other free-form execution logic. Missing configuration SHALL mean disabled. Writes MUST validate the account's authoritative normalized platform, persist atomically with audit fields and return server readback; unsupported, unknown or non-Facebook accounts MUST be rejected without a partial write.

#### Scenario: Facebook account enables the fixed rule
- **WHEN** an operator enables rule mode for an authoritative Facebook account
- **THEN** Cloud persists the fixed definition version and returns the write-after-read truth with `updatedAt` and `updatedBy`

#### Scenario: Non-Facebook account is rejected
- **WHEN** an operator attempts to enable Facebook rule mode for a Xiaohongshu, WeChat Channels or unknown-platform account
- **THEN** the full write is rejected and no rule configuration or runtime progress is created

#### Scenario: Missing configuration is safely off
- **WHEN** a Facebook account has no rule-mode configuration row
- **THEN** reads report rule mode disabled and MUST NOT create a row or start rule execution

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
- **THEN** that rule does not prioritize a card, create an interaction intent or alter the fixed ten-view cadence

#### Scenario: Safety rejection still blocks a card
- **WHEN** a structurally visible card fails the Soul-free prohibited-content or page-identity safety gate
- **THEN** rule mode rejects it with a named reason and does not count it or act on it

#### Scenario: Unbound account remains rejected
- **WHEN** a Facebook account has rule mode enabled but no bound persona
- **THEN** the existing persona admission gate rejects session start and the system MUST NOT substitute a default persona

### Requirement: One rule batch is created from ten durable unique confirmed reads

Rule-mode progress SHALL count only confirmed Facebook `view` facts that include an authoritative account, stable canonical content key, occurrence time, source dedupe key, rule definition version and server-injected execution target. Mounted cards, loading placeholders, navigation-only opens, duplicate content within the active batch, duplicate message delivery and views observed while another mode owns the account MUST NOT advance progress. Progress and facts SHALL be durable across Cloud restart and Edge reconnect.

In one atomic transition, the tenth unique confirmed read SHALL close the current set, create exactly one rule batch with the tenth content as `triggerContentKey`, and advance the progress row to a new batch sequence. A repeated apply or competing worker MUST NOT create a second batch.

#### Scenario: Ten unique confirmed reads create one batch
- **WHEN** the tenth distinct eligible confirmed view for one account, target and definition version is applied
- **THEN** Cloud creates exactly one batch, binds it to that tenth content and resets the next collecting sequence to zero

#### Scenario: Duplicate content does not advance progress
- **WHEN** Edge reconnects or reports a content key already counted in the active batch
- **THEN** the durable uniqueness constraint keeps the view count unchanged and no extra batch is created

#### Scenario: Restart resumes exact progress
- **WHEN** Cloud restarts after seven eligible views
- **THEN** the account resumes at `7/10` for that rule revision and three new unique confirmed views create the next batch

#### Scenario: Cards without read proof do not count
- **WHEN** a card is mounted or scrolled past but no platform-specific confirmed-view evidence is produced
- **THEN** rule progress does not advance

### Requirement: The batch like targets the tenth content and remains fully risk-gated

The batch SHALL attempt its like first and SHALL bind the intent to the tenth confirmed content while that target is current. It MUST NOT search for a better target, revisit one of the preceding nine, or ask a persona appraiser. Immediately before dispatch Cloud MUST enforce the existing `RiskController.explain('like')`, like/view ratio, cooldown, session budget, platform capability, current-target and already-liked gates. Only a platform-confirmed new like SHALL be recorded as confirmed.

#### Scenario: Allowed like is sent to the trigger content
- **WHEN** the tenth content remains current and every like gate allows the action
- **THEN** Cloud sends one like intent for that content and waits for the platform receipt before reporting confirmation

#### Scenario: Like risk rejection is terminal for the batch attempt
- **WHEN** the tenth content creates a batch but `RiskController.explain('like')` rejects it
- **THEN** the like attempt ends as `risk_suppressed`, no like command is sent and no like debt is carried to a later content

#### Scenario: Already-liked target is not retargeted
- **WHEN** target observation shows the tenth content was already liked
- **THEN** the like attempt ends with the named structural skip and the system MUST NOT pick another content to satisfy the batch

### Requirement: Join-contact follows like serially with independent risk decisions

After the like attempt reaches a terminal state, the batch SHALL invoke the single Facebook join-contact orchestrator with `injectContact=true`, `joinFirst=true`, automatic priority, the account's effective approval mode, no manual override and no force flag. `join_group` and `comment` MUST each pass their own just-in-time RiskController, session, daily, contact, approval, dedupe and target gates. The comment stage MUST NOT begin unless the exact group has a platform-confirmed `joined` or `already_member` result.

The like and join-contact outcomes SHALL remain independent and the batch MUST support truthful partial completion. A gate rejection, approval rejection, no-target, offline/not-started, ambiguous receipt, failure or submitted-unknown result SHALL terminate that action attempt without creating work debt. While a batch is non-terminal, no next batch may accumulate for the account.

#### Scenario: Like suppressed but join-contact allowed
- **WHEN** the like gate rejects the batch but the later join and comment gates allow their actions
- **THEN** the batch records the like suppression and MAY complete the join-contact path without relabeling the like as successful

#### Scenario: Join ambiguity prevents comment
- **WHEN** the join stage returns pending, ambiguous, gated, failed or unconfirmed
- **THEN** the comment stage does not start and the batch preserves that honest join outcome

#### Scenario: Join confirmed but comment fails
- **WHEN** platform membership is confirmed but the comment is rejected, fails or becomes submitted-unknown
- **THEN** the membership remains confirmed, the comment keeps its own outcome and the overall batch is partial rather than successful

#### Scenario: Suppressed batch is not replayed after quota reset
- **WHEN** any batch action is risk-suppressed and the relevant quota later becomes available
- **THEN** the old action is not replayed; another opportunity requires ten new unique confirmed views

### Requirement: Rule mode inherits the active window and account single-flight

Facebook rule mode SHALL use the account's effective weekly active window for session start, resume and safe termination. It MUST NOT use content-active hour cells, hash-minute offsets or the content scheduler's hour-cell idempotency as the ten-view trigger. Browse, like and join-contact work SHALL share the account's existing logical single-flight and browser task ownership; batch approval waits MAY release the physical browser but MUST retain logical batch ownership.

#### Scenario: Sleeping schedule prevents rule start
- **WHEN** rule mode is enabled but the account's effective weekly active cell is sleeping
- **THEN** no rule session starts and progress remains unchanged

#### Scenario: Entering a sleep cell stops at a safe boundary
- **WHEN** a running rule session crosses into a sleeping active-window cell
- **THEN** Cloud stops new reads and undispatched actions at the existing safe boundary without rewriting dispatched outcomes

#### Scenario: Pending batch blocks another periodic source
- **WHEN** a rule batch is waiting for approval or another terminal result
- **THEN** the account retains logical ownership and another schedule or rule tick MUST NOT create concurrent work

### Requirement: Configuration, progress and platform outcomes are projected separately

The account automation view SHALL expose server-authoritative rule configuration, effective mode, `0..9/10` collecting progress, current batch action states, named blockers and last update time as separate facts. Trigger creation, command acceptance and notification delivery MUST NOT be displayed as a confirmed like, membership or comment. A stale or unavailable configuration/progress projection MUST be shown as unknown/unavailable and MUST stop new rule work rather than fabricate disabled, zero or success.

#### Scenario: Active slow start is visible without fake zero progress
- **WHEN** rule mode is configured but slow start owns the account
- **THEN** the UI shows the configured rule plus `slow_start_active` and does not pretend an actively collecting rule is at `0/10`

#### Scenario: Partial batch is rendered truthfully
- **WHEN** like is confirmed, join is confirmed and comment is submitted-unknown
- **THEN** the UI shows each distinct outcome and MUST NOT collapse the batch to a green success

#### Scenario: Projection failure is not disabled state
- **WHEN** Cloud cannot read current rule configuration or progress
- **THEN** the UI shows unavailable/unknown, and the runtime refuses new rule work until the authority is readable
