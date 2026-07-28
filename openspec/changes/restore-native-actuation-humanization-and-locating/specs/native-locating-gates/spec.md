## ADDED Requirements

### Requirement: Native page writes MUST be validated against the acted-upon target

Every Native command that writes to the page MUST verify, after dispatch, that the intended business result actually occurred on the same target instance it acted on. The absence of that evidence MUST be reported as an honest non-success outcome that distinguishes "never started" from "dispatched but unconfirmed"; it MUST NOT be promoted to success, and a plain "the call returned without an exception" MUST NOT be accepted as validation. Where post-action validation is impossible for a specific command surface, that surface MUST be recorded explicitly as unvalidated rather than defaulting to a success result.

#### Scenario: Dispatched write without observed effect is not success

- **WHEN** a Native write command dispatches its input and the post-action read does not show the intended state change on the bound target
- **THEN** the command reports an unconfirmed outcome
- **AND** it does not report success and does not fabricate an effect count

#### Scenario: Target lost after dispatch stays indeterminate

- **WHEN** the bound target disappears or changes identity between dispatch and validation
- **THEN** the command reports an indeterminate outcome rather than success or a retryable not-started result

### Requirement: Native locating MUST bound its retries and escalate only on exhaustion

Native target resolution MUST apply an explicit attempt bound. A failed post-action validation within the bound MUST lead to another bounded attempt rather than an immediate terminal verdict, except where the dispatched write is irreversible, in which case the command MUST stop and report the ambiguous outcome without replaying the write. An escalation verdict MUST mean that the attempt bound was exhausted; a single failed attempt MUST NOT be reported as escalated. On exhaustion the command MUST stop and report escalation, and MUST NOT report success. An escalation verdict MUST carry the number of attempts actually made, so that a verdict claiming escalation after one attempt is mechanically detectable rather than indistinguishable from a legitimate one.

#### Scenario: One failed attempt is not an escalation

- **WHEN** a locating attempt fails its post-action validation and the attempt bound has not been reached, and the attempted write is replayable
- **THEN** the runtime makes another bounded attempt
- **AND** it does not report an escalation verdict for that first failure

#### Scenario: Exhausted bound stops and escalates

- **WHEN** every attempt within the bound fails its post-action validation
- **THEN** the runtime stops acting and reports escalation with the last failure reason and the number of attempts actually made
- **AND** it does not report success

#### Scenario: Escalation claimed after a single attempt is rejected by a gate

- **WHEN** any production step-execution path reports an escalation verdict while its reported attempt count is one
- **THEN** the repository-level contract check fails and names that path

#### Scenario: Irreversible dispatch is never replayed

- **WHEN** a write that cannot be safely repeated has been dispatched and its validation is inconclusive
- **THEN** the runtime reports the ambiguous outcome without a further attempt

### Requirement: Native anchor learning MUST stage before promoting and drop on failure

When Native resolution obtains a new element anchor from a non-deterministic source such as a cloud or model-backed selector, that anchor MUST first enter a staging area. It MUST be promoted into the primary anchor cache only after a configured number of consecutive attempts in which the post-action validation succeeded. Any single post-action validation failure involving a staged anchor MUST drop it from staging. A newly obtained anchor MUST NOT be written directly into the primary cache, and a dropped anchor MUST NOT be reused as if it had been confirmed.

#### Scenario: New anchor is not trusted on first success

- **WHEN** a model-backed selector supplies a new anchor and the first validated action using it succeeds, with the promotion threshold set above one
- **THEN** the anchor remains staged and is not yet served from the primary cache

#### Scenario: Repeated validated success promotes the anchor

- **WHEN** the staged anchor reaches the configured number of consecutive validated successes
- **THEN** it is promoted into the primary cache and served on subsequent resolutions

#### Scenario: Any validation failure drops the staged anchor

- **WHEN** an action using a staged anchor fails its post-action validation
- **THEN** the anchor is dropped from staging
- **AND** it is neither promoted nor reused on the next resolution

### Requirement: Post-action validation criteria MUST meet a minimum strength bar

Having a validation step is not sufficient: the criterion itself MUST be strong enough that it cannot pass on incidental page content. A state-flip criterion MUST accept only whitelisted attributes equal to their affirmative value, and MUST allow a bounded number of ancestor levels to be inspected because the flip may land on a wrapping container rather than on the clicked element. Where a class name is used as a signal, the criterion MUST match the semantic fragment on a token boundary — the fragment being the whole class token or delimited by a hyphen or underscore — and MUST NOT accept a loose substring match, because obfuscated build output routinely contains such substrings by accident. A single-character text fallback MUST NOT be used as a success signal. Where no measured anchor for a criterion exists yet, the criterion MUST fail closed and report an honest failure rather than widening until something matches.

#### Scenario: Loose substring class match is rejected

- **WHEN** the clicked element carries an obfuscated class name that merely contains an affirmative-looking fragment while the business state did not change
- **THEN** the validation reports the action as unconfirmed
- **AND** it does not treat the substring as evidence of the state flip

#### Scenario: Flip on the wrapping container is still detected

- **WHEN** the affirmative attribute appears on an ancestor of the clicked element within the allowed depth
- **THEN** the validation detects the flip

#### Scenario: Uncalibrated criterion fails closed

- **WHEN** a command surface has no measured anchor for its post-action criterion
- **THEN** the command reports an honest failure and is recorded as unvalidated
- **AND** it does not fall back to a broad match that would report success

### Requirement: Post-action evidence MUST NOT be the command's own input

The evidence a command reads back to confirm its effect MUST NOT be the very text that command just wrote into the page, because reading back one's own write proves only that the write happened, not that the platform accepted it. Confirmation of a structured result MUST rest on a structural signal produced by the page itself, compared for exact equality after normalization and after stripping any hidden decoration, rather than on a containment test over the whole editor text. A containment test MUST NOT be used where a longer pre-existing value could contain the requested one.

#### Scenario: Plain typed text is not accepted as a committed result

- **WHEN** a command types a marker into an editor and the page produced no structural element for it
- **THEN** the validation reports the result as unconfirmed
- **AND** it does not accept the typed text found in the editor as evidence

#### Scenario: Containment does not stand in for equality

- **WHEN** the page already contains a longer value that includes the requested one as a substring
- **THEN** the validation still reports the requested value as not committed

### Requirement: Native locating parity MUST NOT reintroduce retired page-rule JavaScript

The locating guarantees required above MUST be provided inside the Native engine. The retired TypeScript locating engine, its anchor cache, and their production consumers MUST remain excluded from the distributable production artifact, and the build-time exclusion check MUST NOT be relaxed to satisfy these requirements.

#### Scenario: Production artifact stays free of the retired locating modules

- **WHEN** the production distribution is built after these locating guarantees are implemented
- **THEN** the build-time exclusion check still reports the retired locating engine and anchor cache as absent
- **AND** the build fails if either is reachable from the production entry point
