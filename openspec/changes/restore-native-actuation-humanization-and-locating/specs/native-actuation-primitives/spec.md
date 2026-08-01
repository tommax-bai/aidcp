## ADDED Requirements

### Requirement: Native command execution MUST consume the cloud timing directives it receives

Every cloud timing directive delivered with a command MUST be honored on the edge before that command acts. Which edge layer honors it — the host projection layer or the Native engine process — is an implementation choice; what MUST hold is that no command dispatches page input without having honored the directives it carries.

For any command carrying a pre-action hesitation value, the edge MUST wait a jittered amount derived from that value before dispatching any page-affecting input of that command. Placing that wait ahead of the whole command rather than immediately ahead of the first input is an accepted approximation: a command body may contain several scroll, probe and click segments, and the layer holding the directive does not know which of them is the acting moment. What is NOT acceptable is dispatching the command's inputs without having waited at all.

For any command carrying a leave-content dwell value, the edge MUST ensure the elapsed time on that content is at least the jittered value before it leaves the content, topping up the remainder when the elapsed time is short. This one MUST be measured from an anchor — the moment the content actually began to be displayed — and MUST NOT be measured from the moment the command started, because the two differ by exactly the reading time this directive exists to protect. When the anchor cannot be read, the edge MUST NOT top up against a wrong origin; it applies its built-in floor instead.

Repeated executions with an identical center value MUST produce different observed waits. The runtime MUST NOT re-scale a cloud-supplied timing value by the risk tempo, because that scaling is already applied by the cloud; re-scaling it would count the risk slowdown twice. When a command carries no timing value, the runtime MUST fall back to a non-zero built-in floor and MUST NOT degrade to zero delay.

#### Scenario: Cloud-supplied value is not multiplied by the tempo tier

- **WHEN** the same command carrying the same pre-action hesitation or leave-content dwell value is executed under a baseline tempo tier and again under a worse tempo tier
- **THEN** the wait center value is the cloud-supplied value in both cases and the tier does not enlarge it

#### Scenario: Interaction command waits before its first page input

- **WHEN** a like, collect, follow, comment, comment-like, note-open, image-browse, comment-scroll, profile-open, feed-refresh, notification or group-join command arrives carrying a pre-action hesitation value
- **THEN** the edge waits a jittered amount derived from that value before dispatching any pointer, wheel or keyboard input of that command
- **AND** the same center value delivered twice produces two different observed waits

#### Scenario: Leaving content tops up the remaining dwell

- **WHEN** a command carrying a leave-content dwell value is executed and the content has been displayed for less than the jittered value
- **THEN** the edge waits out the remainder, measured from the moment the content began to be displayed, before dispatching the navigation or scroll that leaves the content

#### Scenario: Unreadable dwell anchor does not top up against a wrong origin

- **WHEN** a command carries a leave-content dwell value but the moment the content began to be displayed cannot be read
- **THEN** the edge applies its built-in floor rather than treating the command start as the anchor

#### Scenario: Already-satisfied dwell adds no second delay

- **WHEN** the content has already been displayed for longer than the jittered dwell value
- **THEN** the runtime leaves without any additional wait

#### Scenario: Missing timing value does not become zero delay

- **WHEN** a command arrives without any timing value
- **THEN** the runtime applies its non-zero built-in floor for that operation class rather than acting immediately

### Requirement: Forwarding a timing field to Native MUST imply a consumption point

A command kind whose projection forwards a timing field MUST have a corresponding consumption point on the edge. A command kind that has no consumption point MUST NOT forward the field, and a command kind that declares a field nobody forwards MUST NOT keep declaring it.

This correspondence MUST be enforced by an automated check that fails when a forwarded field has no consumer, so that a silently discarded directive is a build-visible regression rather than an invisible behavior loss. The check's consumption leg MUST be derived from observed behaviour — how long the edge actually waited — and MUST NOT be satisfied by any table, registry or source-text scan asserting that a consumer exists, because every one of those can be kept green by editing the table alone.

A declared field that is deliberately not consumed MUST be listed as such with its reason, and the declared set MUST be partitioned exactly into consumed and deliberately-unconsumed. Requiring strict equality instead would leave only one way to keep the gate green — deleting the declaration — and that loses the reason along with it.

#### Scenario: Forwarded field without a consumer fails the gate

- **WHEN** a command kind is allowed to forward a timing field but the edge never waits on it for that kind
- **THEN** the automated correspondence check fails and names the offending command kind
- **AND** the mismatch is not reported as a passing build

#### Scenario: Deliberately unconsumed field is declared with its reason

- **WHEN** a command declares a timing field that its path structurally cannot consume
- **THEN** the check requires that field to be listed as deliberately unconsumed together with its reason
- **AND** the consumed and deliberately-unconsumed sets together account for exactly the declared set

#### Scenario: Adding a new command keeps the correspondence explicit

- **WHEN** a new command kind is registered that carries a timing field
- **THEN** the correspondence check requires either a consumption point or removal of the field from the forwarding projection

### Requirement: Native pacing fallbacks MUST stay wired to the handshake snapshot

The Native execution path MUST retain and apply the pacing fallback snapshot delivered at handshake, covering the tempo tier and the floor ranges for those operation classes the path actually samples locally, and MUST apply a mid-session pacing update rather than discarding it. Fallback floors sampled locally MUST be scaled by the currently effective tempo tier so that a worse risk state produces slower local fallbacks. The runtime MUST NOT accept a snapshot that carries content-derived coefficients.

A floor range for an operation class the path has no sampler for MUST NOT be stored. The minimum-interval gating layer that consumes the remaining classes is **not** part of this capability and is not implemented on the Native path; storing its ranges anyway would leave dead fields that any check counting "ranges retained" would read as coverage. That gating layer — its monotonic interval anchor, and the rule that the interval and the pre-action hesitation are folded with a maximum rather than added — is named as an uncovered residual and belongs to a separate change.

The two snapshot entry points MUST stay distinguishable: a reconnect hand-over MAY clear the pacing anchors along with the values, while a mid-session tier refresh MUST NOT touch them. Collapsing them makes a mid-session tier change reset the dwell anchor, which turns the very next leave-content command into the instant bounce this capability exists to prevent.

#### Scenario: Mid-session pacing update takes effect

- **WHEN** the cloud sends a pacing update while a Native browse session is running
- **THEN** the session applies the new tempo tier and floors to its subsequent local fallbacks
- **AND** it does not silently ignore the message

#### Scenario: Worse risk tier slows local fallbacks

- **WHEN** the effective tempo tier is above the baseline and a command arrives without a timing value
- **THEN** the sampled local fallback center is enlarged by that tier before jitter is applied

#### Scenario: Reconnect re-injects the connection-level snapshot

- **WHEN** the edge reconnects and reuses the same Native browse session object while the cloud-side floor configuration has changed
- **THEN** the session adopts the newly handed-over floors and tempo for its subsequent local fallbacks rather than keeping the values captured at process start

### Requirement: Native pointer actuation MUST follow a humanized path

A Native pointer click MUST reach its target through a multi-frame movement whose per-frame delays are non-uniform, and MUST NOT consist of a single move that lands exactly on the target immediately followed by a press. The movement MUST include positional jitter around the sampled path and MAY include an occasional overshoot with a correction pull. Two clicks issued at the same coordinates MUST produce different frame counts or different frame timings.

Where a platform capability requires the pointer origin to stay inside a specific corridor (for example a control-to-flyout corridor), the caller MUST be able to supply that origin and to disable the overshoot, and the primitive MUST honor both. When the caller supplies no origin, the primitive MUST start from the last real landing point if one is known, so that consecutive clicks form a continuous cursor track; it MUST NOT jump the cursor back to a fresh random offset between two clicks that belong to the same interaction.

The scope of "last landing point" MUST be no wider than the session whose track it represents. Where the implementation holds it process-wide, that is sound **only** while one engine process drives one browser and executes commands serially; that invariant MUST be stated where the state lives, because the day it stops holding, one session's cursor position leaks into another's track and the failure is silent — the clicks still land, the track just stops being a track.

#### Scenario: Click is not a coordinate teleport

- **WHEN** the Native runtime clicks a resolved page coordinate
- **THEN** it dispatches more than one move event along a path ending at the target, with varying inter-frame delays, before pressing
- **AND** it does not dispatch a press as the second event of the sequence

#### Scenario: Repeated clicks are not identical

- **WHEN** the same coordinate is clicked twice in one session
- **THEN** the two dispatched movement sequences differ in frame count or per-frame delays

#### Scenario: Caller-supplied origin is honored

- **WHEN** a capability supplies a pointer origin that must be preserved
- **THEN** the movement starts from that origin and does not overshoot outside the requested corridor

#### Scenario: Consecutive clicks keep a continuous cursor track

- **WHEN** a second click follows a first click in the same interaction and the caller supplies no explicit origin
- **THEN** the second movement starts from the first click's actual landing point rather than from a new random offset near the second target

### Requirement: Native pointer press and release MUST be paired on every path

Once a Native pointer press is attempted, the primitive MUST attempt the matching release before returning, on both the success and the failure path, so the left button is never left held. A failure of the release attempt MUST NOT replace or mask the original error. The primitive MUST NOT return a successful actuation result when the press itself did not complete.

#### Scenario: Failure after press still releases

- **WHEN** the press is dispatched and a later step of the same click fails
- **THEN** the primitive still attempts the release before propagating the failure
- **AND** the propagated error is the original failure, not the release failure

#### Scenario: Press failure does not leave the button held

- **WHEN** the press dispatch itself fails
- **THEN** the primitive still attempts a release and reports the press failure
- **AND** it does not report the click as actuated

### Requirement: The press-to-release window MUST be a non-interruptible atomic region

Cancellation and deadline checks in the pointer primitive MUST occur before the press. Between press and release the primitive MUST NOT observe a cancellation signal, a deadline expiry, or any other early-return path. A cancellation raised inside that window MUST take effect only after the release has been attempted.

A failure that arrives after the press MUST NOT be reported as a not-started outcome, because the click was in fact actuated and the page may already have changed. It MUST be reported as dispatched-with-undetermined-result, so that the caller and the cloud treat it as an ambiguous write rather than as safe to replay. Only a failure observed before the press may be reported as not started.

Because every cancellation and deadline check is hoisted ahead of the press, "cancelled inside the atomic region" is structurally unreachable and the live form of this rule is a dispatch failure of the press or the release. That does not make the rule decorative — it makes it load-bearing in a place that is easy to miss: **the honest wording of the error is not enough**, since the caller reads the outcome's phase, not its prose. Wherever the command layer treats a set of error codes as meaning not-started (that is, safe to replay), a post-press failure MUST NOT be able to carry one of those codes, whatever the underlying transport error called itself. That set MUST be a single named source of truth referenced by both the phase mapping and the post-press translation; keeping a second copy of it is how the seam silently reopens.

#### Scenario: Cancellation during the atomic region completes the pair

- **WHEN** the cancellation signal is raised after the press has been dispatched
- **THEN** the primitive completes the release first and reports cancellation afterwards

#### Scenario: Cancellation after the press is not reported as not-started

- **WHEN** the cancellation signal is raised after the press has been dispatched and the release has been attempted
- **THEN** the reported outcome marks the actuation as dispatched with an undetermined result
- **AND** it is not reported as not started and the caller does not treat it as replayable

#### Scenario: Cancellation before the press skips actuation entirely

- **WHEN** the cancellation signal is already raised when the movement finishes and before the press
- **THEN** the primitive returns without dispatching press or release
- **AND** it reports the command as not started

### Requirement: Native text entry MUST be hardware-level and character-paced on every platform

Text a command writes into a page MUST be entered through the browser's real input channel one grapheme at a time, with a non-uniform inter-character delay. A command MUST NOT enter text by assigning the whole string to an element's value or text content and then dispatching synthesized input events, because such events are not trusted input and the resulting timing carries no typing rhythm at all.

This requirement binds the text-entry surfaces the runtime drives through its own command specialisations: comment bodies, publish fields, and topic candidate keywords. Three surfaces are **named exceptions** rather than silent gaps, and each MUST be recorded with its reason rather than quietly satisfied by a weaker write:

- **Segmented date-time controls** (scheduled publishing). Typing a whole string into a control whose segments each own part of the value is not equivalent to filling it, and would break the feature. Hardware-level entry there requires per-segment key handling whose key semantics cannot be established without measuring the real control; until then the native value assignment stands.
- **Mention, location and collection candidates.** These have no calibrated structural signal for "the platform accepted the selection", so moving their typing without their judgement would relocate a self-proving confirmation into new code. They stay on the existing path until that signal is measured.
- **The retired ordered-step compatibility path.** Its gap is typing realism, not a lying judgement — its own guard already rejects non-editable targets, and "the text is in the field" is what an input step means. The path is deprecated and intercepting one step of it is structurally impossible without relocating the whole step loop.

Each exception MUST remain visible as an exception. A future change that closes one MUST remove it from this list rather than leave the list overstating the gap.

For long text the runtime MAY cap the number of write round-trips and the total accumulated pause so that a single step stays inside its deadline, but every character MUST still be written: the cap may only shorten time and round-trips and MUST NOT drop content. The only cancellation seam MUST be the moment after a character's wait has elapsed and before that character's write is dispatched; text already written stays in the editor and the caller is responsible for clearing it, and a takeover MUST surface as a takeover rather than as a generic failure.

#### Scenario: Whole-string assignment is not accepted as text entry

- **WHEN** a command writes a comment body, a publish field or a topic candidate keyword into a page
- **THEN** the runtime dispatches one real input write per grapheme with varying delays between them
- **AND** it does not set the element's value or text content in a single assignment followed by synthesized input events

#### Scenario: A named exception stays named

- **WHEN** a text surface is excluded from hardware-level entry
- **THEN** it appears in this capability's exception list with the reason it is excluded
- **AND** it is not left as an unrecorded gap that reads as covered

#### Scenario: Long text is capped in time but not in content

- **WHEN** the text is long enough that per-character round-trips would exceed the step deadline
- **THEN** the runtime reduces round-trips and total pause to stay inside the deadline
- **AND** the concatenation of everything written still equals the requested text

#### Scenario: Cancellation lands between characters

- **WHEN** a takeover is signalled while text entry is in progress
- **THEN** the runtime stops after the pending character's wait and before that character's write is dispatched
- **AND** it reports the takeover rather than a generic input failure

### Requirement: Rich-text newlines MUST be a separate paragraph primitive with bounded caret confirmation

Where a page's body editor treats a newline as a paragraph-structure transaction rather than as a character, the runtime MUST split the body into two kinds of primitive: plain text writes that never carry a carriage return or line feed, and standalone bare newline key presses that let the editor perform its own paragraph split. After each newline the runtime MUST perform a bounded confirmation that the already-written prefix is still present, that the paragraph count reached the expected value, and that the caret sits at the end; the confirmation MUST require consecutive successful observations rather than a single one, because a delayed selection transaction can move the caret back. A command acknowledgement MUST NOT be accepted in place of that editor-state confirmation. If the confirmation does not stabilize within its bound, the runtime MUST clear the body and fail honestly instead of continuing to write.

#### Scenario: Body text never carries a newline character

- **WHEN** a multi-paragraph body is written into a paragraph-structured editor
- **THEN** every text write is free of carriage returns and line feeds
- **AND** each paragraph break is dispatched as a standalone bare newline key press

#### Scenario: Caret is confirmed at the end after each newline

- **WHEN** a newline key press has been dispatched
- **THEN** the runtime confirms the written prefix, the paragraph count and the end-of-content caret position on consecutive observations before writing the next paragraph

#### Scenario: Unstable newline clears and fails honestly

- **WHEN** the caret confirmation does not stabilize within its bound
- **THEN** the runtime clears the body and reports an honest failure naming the unstable newline
- **AND** it does not continue writing the remaining paragraphs

### Requirement: Page scrolling MUST use the shared humanized wheel gesture on every platform

A command that advances a list, a detail body or a comment area through the runtime's own command specialisations MUST scroll by dispatching the shared humanized wheel gesture — a cursor move onto the scrollable region followed by multiple wheel frames with non-uniform per-frame delays and a distance sampled around a baseline. A command MUST NOT scroll by calling the page's own scrolling API, because that dispatches no wheel event at all and, on layouts whose scrollable element is not the document, silently does nothing while still reporting an advance. A dispatch failure during the gesture MUST abort only the current scroll and MUST NOT propagate an exception that ends the browsing loop.

Two scroll sites are **named exceptions** and remain on the page's own scrolling API: the scroll step of the retired ordered-step compatibility path (deprecated, and not interceptable one step at a time), and the in-page scroll inside notification clearing (deliberately left out of scope). Both MUST stay listed here rather than read as covered.

Whether the scroll advanced MUST be decided by measured position, and the measurement MUST count movement in **both** directions: a lazily re-rendered list can swap its scroll container, and a refresh can jump the position back to the top. Counting only forward movement reports those real movements as "did not move", which upstream combines with "at the end and did not move" into an early stop.

#### Scenario: List paging dispatches a real wheel gesture

- **WHEN** a command advances the content list on any platform
- **THEN** it moves the cursor onto the scrollable region and dispatches multiple wheel frames with non-uniform delays
- **AND** it does not advance by calling the page's own scrolling API

#### Scenario: Transient dispatch failure does not end the session

- **WHEN** one wheel frame dispatch fails during a gesture
- **THEN** the runtime abandons the remainder of that gesture and reports the measured movement honestly
- **AND** it does not propagate a failure that terminates the browsing loop

> **两条要求已从本 delta 摘出（2026-08-01，归档前对账）**，因为它们对应的任务被**显式弃守**，
> 而规格只能写「已实现」那一列 —— 留着就是往主 spec 里并进两条实装明知违反的 MUST。
>
> - **注入点击助手不得移动页面 / 不得伪造指针事件**（原任务 3.7）：弃守理由是它要的是**反检测质量**、
>   不消除任何假成功（瞬移之后的点击结果是真的），且消费面有几支已被引擎截走、实际不可达。
>   小红书那一半另由任务 7.11 具名交接给单写区属主 `restore-native-xiaohongshu-action-honesty`。
> - **验证码协助专用高审查节奏档**（原任务 2.9）：同上，且它所在的验证码协助链路是**人工介入的低频路径**。
>
> **两条都不是「不该做」，是「本 change 不交付」。** 兑现时机是下次反检测专项，届时连同这两条
> 一并立项并把要求写回规格。**注意任务 2.10 不随之弃守** —— 那条查的是「轨迹字段被静默丢弃 +
> 回放模式硬编码」，属诚实性缺口，仍在下面。

### Requirement: Assist click receipts MUST report the actual replay mode and MUST NOT silently discard a supplied trajectory

The replay mode reported in an assist click receipt MUST reflect how the click was actually driven and MUST NOT be a constant. When the caller supplies an operator trajectory that the runtime cannot use — because the field is not forwarded, not accepted by the execution layer, or fails validation — the discard MUST leave an observable record and the receipt MUST state that the synthetic path was used. Claiming a trajectory-driven replay while running the synthetic path, or dropping the field with no trace at all, is a dishonest receipt.

#### Scenario: Unusable trajectory is discarded observably

- **WHEN** the cloud supplies an operator trajectory and the runtime cannot use it
- **THEN** the discard is recorded observably with its reason
- **AND** the receipt reports the synthetic replay mode

#### Scenario: Replay mode is not a hardcoded constant

- **WHEN** the assist click receipt is produced
- **THEN** its replay mode is derived from the path actually taken
- **AND** a receipt whose replay mode cannot vary fails the repository contract check
