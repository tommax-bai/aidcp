# native-locating-gates Specification

## Purpose
TBD - created by archiving change restore-native-actuation-humanization-and-locating. Update Purpose after archive.
## Requirements
### Requirement: Native page writes MUST be validated against the acted-upon target

Every Native command that writes to the page MUST verify, after dispatch, that the intended business result actually occurred on the same target instance it acted on. The absence of that evidence MUST be reported as an honest non-success outcome that distinguishes "never started" from "dispatched but unconfirmed"; it MUST NOT be promoted to success, and a plain "the call returned without an exception" MUST NOT be accepted as validation. Where post-action validation is impossible for a specific command surface, that surface MUST be recorded explicitly as unvalidated rather than defaulting to a success result.

Whether a command satisfies this is a property of its own post-condition, not of which module it is written in: a shared resolve–act–validate orchestration exists and is wired to a first real command, but a command with its own honest post-condition is equally compliant. Which side of that line each command sits on MUST be recorded in a per-surface inventory, and that inventory MUST be mechanically held to the engine's own set of writing commands — every write command appears exactly once, so that adding one without classifying it fails rather than passing silently. **An unlisted surface reads as covered**, which is why completeness is enforced rather than reviewed.

The inventory MUST distinguish "meets the bar" from three things that are **not** the same as having validation: a check that exists but falls short of the strength bar (recorded with where it falls short), a surface with no readable business result at all (recorded with why, and explicitly not therefore defaulting to success), and a surface nobody has read yet. The last category MUST be a monotone budget that only decreases, and the budget MUST equal the actual count so that trimming it leaves no headroom for new entries to refill — a ratchet with slack is not a ratchet. A newly added write command MUST NOT default into it.

Until a surface is recorded as meeting the bar, this guarantee MUST NOT be cited for it.

#### Scenario: Dispatched write without observed effect is not success

- **WHEN** a Native write command dispatches its input and the post-action read does not show the intended state change on the bound target
- **THEN** the command reports an unconfirmed outcome
- **AND** it does not report success and does not fabricate an effect count

#### Scenario: Target lost after dispatch stays indeterminate

- **WHEN** the bound target disappears or changes identity between dispatch and validation
- **THEN** the command reports an indeterminate outcome rather than success or a retryable not-started result

### Requirement: Native locating MUST bound its retries and escalate only on exhaustion

Native target resolution MUST apply an explicit attempt bound. A failed post-action validation within the bound MUST lead to another bounded attempt rather than an immediate terminal verdict, except where the dispatched write is irreversible, in which case the command MUST stop and report the ambiguous outcome without replaying the write. An escalation verdict reached **through a validation retry loop** MUST mean that the attempt bound was exhausted; a single failed attempt MUST NOT be reported as escalated. On exhaustion the command MUST stop and report escalation, and MUST NOT report success. Every escalation verdict MUST carry the number of attempts **actually made**, never a hardcoded one, because reporting the request's shape instead of the measured process leaves the caller unable to tell "retry this" from "stop, the platform changed".

A step whose failure is **structural** — repeating it on the same page cannot produce a different result, such as a page that will not scroll — has no retry loop, and one *is* its measured attempt count. Such a step MUST be named as an exception rather than made to fake extra attempts. A mechanical check MUST therefore be stated over "escalations reached through a retry loop", NOT as a blanket ban on the escalated-with-one-attempt shape: the blanket form would fail a step that is behaving correctly, and the usual way that gets resolved is by loosening the check until it protects nothing.

#### Scenario: One failed attempt is not an escalation

- **WHEN** a locating attempt fails its post-action validation and the attempt bound has not been reached, and the attempted write is replayable
- **THEN** the runtime makes another bounded attempt
- **AND** it does not report an escalation verdict for that first failure

#### Scenario: Exhausted bound stops and escalates

- **WHEN** every attempt within the bound fails its post-action validation
- **THEN** the runtime stops acting and reports escalation with the last failure reason and the number of attempts actually made
- **AND** it does not report success

#### Scenario: Escalation reached through a retry loop carries the measured count

- **WHEN** a production step-execution path escalates after its validation retry loop is exhausted
- **THEN** the reported attempt count equals the number of attempts actually made
- **AND** a path reporting a hardcoded count — whether one or the bound — fails the repository-level contract check and is named by it

#### Scenario: A structurally terminal step is a named exception, not a violation

- **WHEN** a step escalates without a retry loop because repeating it cannot change the outcome
- **THEN** it reports one attempt and is listed as a named exception
- **AND** the contract check does not fail it, and is not loosened to accommodate it

#### Scenario: Irreversible dispatch is never replayed

- **WHEN** a write that cannot be safely repeated has been dispatched and its validation is inconclusive
- **THEN** the runtime reports the ambiguous outcome without a further attempt

> **「锚点先暂存、连续确认才晋升、任一次失败即丢弃」这条要求已从本 delta 摘出**
> （2026-08-01，归档前对账）。
>
> **不是「做不完」，是前提不成立**：Native 引擎里每个定位器都是**编译进二进制的固定选择器**，
> 没有任何「解析结果可能不对、需要先观察几次再采信」的非确定性来源。没有不确定的来源，
> 就没有什么可暂存、可晋升、可反污染的 —— 暂存区在这套架构下**恒为空**。
> 用户 2026-07-30 据此裁定「暂不做，且要重新设计」（原任务 5.4 / 5.5 / 7.16）。
>
> **摘出的同时必须守住一条**：代码里那整套暂存 / 晋升 / 丢弃实现仍在，
> **MUST NOT 因为它存在就把第三道闸读成已生效**。钉住这件事的守卫用例
> （断言暂存区恒为 0）必须保留 —— 删它等于把这层误读重新打开。
>
> 重新设计要动的是「**要不要在 Native 侧重新引入非确定性的定位来源**」这个前提，
> 不是这层代码的写法；那是产品与架构取舍，须先出设计再 propose、另起 change。

### Requirement: Post-action validation criteria MUST meet a minimum strength bar

Having a validation step is not sufficient: the criterion itself MUST be strong enough that it cannot pass on incidental page content. A state-flip criterion MUST accept only whitelisted attributes equal to their affirmative value, and MUST allow a bounded number of ancestor levels to be inspected because the flip may land on a wrapping container rather than on the clicked element. Where a class name is used as a signal, the criterion MUST NOT accept a bare substring match on an obfuscated class name, and MUST NOT read a negated form — a fragment preceded by a negating prefix such as not-, un-, in- or de- — as affirmative evidence, because obfuscated build output routinely contains such substrings by accident and the negated forms are counter-evidence rather than evidence. Reading a whitelisted state attribute instead of the class name satisfies this.

The stronger form of the class-name rule — matching the semantic fragment on a token boundary, together with a match-uniqueness gate that refuses to act when two candidates score alike — is **named as out of scope here** and handed to a separate change (see this change's task 7.14). It MUST NOT be read as delivered by the clause above. A single-character text fallback MUST NOT be used as a success signal. Where no measured anchor for a criterion exists yet, the criterion MUST fail closed and report an honest failure rather than widening until something matches.

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

The evidence a command reads back to confirm its effect MUST NOT be the very text that command just wrote into the page, because reading back one's own write proves only that the write happened, not that the platform accepted it.

Confirmation of a structured result MUST rest on a structural signal produced by the page itself, compared for exact equality after normalization and after stripping any hidden decoration, rather than on a containment test over the whole editor text. A containment test MUST NOT be used where a longer pre-existing value could contain the requested one.

Where the business result is that the platform accepted a submission, the confirmation MUST also require a structural necessary condition that only the platform can produce — the submission editor having been cleared, for instance — and the scan for the submitted content MUST exclude the editor and any container holding it. Without that exclusion the scan reads back the draft still sitting on the page, and the check is unconditionally true.

This binds the surfaces the runtime confirms through its own command specialisations. Mention, location and collection candidates remain on the existing path with a weaker judgement and are **named as an exception** here rather than left implied; closing it requires first measuring each one's structural acceptance signal, which is registered as a real-machine item.

#### Scenario: Plain typed text is not accepted as a committed result

- **WHEN** a command types a marker into an editor and the page produced no structural element for it
- **THEN** the validation reports the result as unconfirmed
- **AND** it does not accept the typed text found in the editor as evidence

#### Scenario: Containment does not stand in for equality

- **WHEN** the page already contains a longer value that includes the requested one as a substring
- **THEN** the validation still reports the requested value as not committed

#### Scenario: The submission's own draft is not scanned as evidence

- **WHEN** a command confirms that a submission arrived by scanning the page for its content
- **THEN** the scan excludes the submission editor and every container that holds it
- **AND** the confirmation additionally requires the platform to have cleared that editor

#### Scenario: Unreadable structural condition is not a negative

- **WHEN** the structural necessary condition cannot be read at all
- **THEN** the command reports an unconfirmed outcome whose reason distinguishes it from having read a definite negative

### Requirement: Native locating parity MUST NOT reintroduce retired page-rule JavaScript

The locating guarantees required above MUST be provided inside the Native engine. The retired TypeScript locating engine, its anchor cache, and their production consumers MUST remain excluded from the distributable production artifact, and the build-time exclusion check MUST NOT be relaxed to satisfy these requirements.

#### Scenario: Production artifact stays free of the retired locating modules

- **WHEN** the production distribution is built after these locating guarantees are implemented
- **THEN** the build-time exclusion check still reports the retired locating engine and anchor cache as absent
- **AND** the build fails if either is reachable from the production entry point

