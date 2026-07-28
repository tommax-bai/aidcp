## ADDED Requirements

### Requirement: Native command execution MUST consume the cloud timing directives it receives

The Native page-execution runtime is the edge actuation layer, so every cloud timing directive delivered with a command MUST be honored inside it. For any command carrying a pre-action hesitation value, the runtime MUST wait a jittered amount derived from that value immediately before dispatching the command's first page-affecting input, and MUST NOT dispatch that input earlier. For any command carrying a leave-content dwell value, the runtime MUST ensure the elapsed time on that content is at least the jittered value before it leaves the content, topping up the remainder when the elapsed time is short.

Repeated executions with an identical center value MUST produce different observed waits. The runtime MUST NOT re-scale a cloud-supplied timing value by the risk tempo, because that scaling is already applied by the cloud; re-scaling it would count the risk slowdown twice. When a command carries no timing value, the runtime MUST fall back to a non-zero built-in floor and MUST NOT degrade to zero delay.

#### Scenario: Cloud-supplied value is not multiplied by the tempo tier

- **WHEN** the same command carrying the same pre-action hesitation or leave-content dwell value is executed under a baseline tempo tier and again under a worse tempo tier
- **THEN** the wait center value is the cloud-supplied value in both cases and the tier does not enlarge it

#### Scenario: Interaction command waits before its first page input

- **WHEN** a like, collect, follow, comment, comment-like, note-open, image-browse, comment-scroll, profile-open, feed-refresh, notification or group-join command arrives carrying a pre-action hesitation value
- **THEN** the runtime waits a jittered amount derived from that value before dispatching the first pointer, wheel or keyboard input of that command
- **AND** the same center value delivered twice produces two different observed waits

#### Scenario: Leaving content tops up the remaining dwell

- **WHEN** a command carrying a leave-content dwell value is executed and the content has been displayed for less than the jittered value
- **THEN** the runtime waits out the remainder before dispatching the navigation or scroll that leaves the content

#### Scenario: Already-satisfied dwell adds no second delay

- **WHEN** the content has already been displayed for longer than the jittered dwell value
- **THEN** the runtime leaves without any additional wait

#### Scenario: Missing timing value does not become zero delay

- **WHEN** a command arrives without any timing value
- **THEN** the runtime applies its non-zero built-in floor for that operation class rather than acting immediately

### Requirement: Forwarding a timing field to Native MUST imply a consumption point

A command kind whose host-side projection forwards a timing field into the Native runtime MUST have a corresponding consumption point inside that runtime. A command kind that has no consumption point MUST NOT forward the field. This correspondence MUST be enforced by an automated check that fails when a forwarded field has no consumer, so that a silently discarded directive is a build-visible regression rather than an invisible behavior loss.

#### Scenario: Forwarded field without a consumer fails the gate

- **WHEN** a command kind is allowed to forward a timing field but the Native runtime never reads it for that kind
- **THEN** the automated correspondence check fails and names the offending command kind
- **AND** the mismatch is not reported as a passing build

#### Scenario: Adding a new command keeps the correspondence explicit

- **WHEN** a new command kind is registered that carries a timing field
- **THEN** the correspondence check requires either a consumption point or removal of the field from the forwarding projection

### Requirement: Native pacing fallbacks MUST stay wired to the handshake snapshot

The Native execution path MUST retain and apply the pacing fallback snapshot delivered at handshake, covering the tempo tier and the per-operation floor ranges, and MUST apply a mid-session pacing update rather than discarding it. Fallback floors sampled locally MUST be scaled by the currently effective tempo tier so that a worse risk state produces slower local fallbacks. The runtime MUST NOT accept a snapshot that carries content-derived coefficients.

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

Where a platform capability requires the pointer origin to stay inside a specific corridor (for example a control-to-flyout corridor), the caller MUST be able to supply that origin and to disable the overshoot, and the primitive MUST honor both. When the caller supplies no origin, the primitive MUST start from the last real landing point of the session if one is known, so that consecutive clicks form a continuous cursor track; it MUST NOT jump the cursor back to a fresh random offset between two clicks that belong to the same interaction.

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

A cancellation that arrives after the press MUST NOT be reported as a not-started outcome, because the click was in fact actuated and the page may already have changed. It MUST be reported as dispatched-with-undetermined-result, so that the caller and the cloud treat it as an ambiguous write rather than as safe to replay. Only a cancellation observed before the press may be reported as not started.

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

Text a command writes into a page MUST be entered through the browser's real input channel one grapheme at a time, with a non-uniform inter-character delay, on every platform the runtime drives. A command MUST NOT enter text by assigning the whole string to an element's value or text content and then dispatching synthesized input events, because such events are not trusted input and the resulting timing carries no typing rhythm at all.

For long text the runtime MAY cap the number of write round-trips and the total accumulated pause so that a single step stays inside its deadline, but every character MUST still be written: the cap may only shorten time and round-trips and MUST NOT drop content. The only cancellation seam MUST be the moment after a character's wait has elapsed and before that character's write is dispatched; text already written stays in the editor and the caller is responsible for clearing it, and a takeover MUST surface as a takeover rather than as a generic failure.

#### Scenario: Whole-string assignment is not accepted as text entry

- **WHEN** a command writes a comment, a publish field, a candidate keyword or a schedule value into a page
- **THEN** the runtime dispatches one real input write per grapheme with varying delays between them
- **AND** it does not set the element's value or text content in a single assignment followed by synthesized input events

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

Any command that advances a list, a detail body or a comment area MUST scroll by dispatching the shared humanized wheel gesture — a cursor move onto the scrollable region followed by multiple wheel frames with non-uniform per-frame delays and a distance sampled around a baseline. A command MUST NOT scroll by calling the page's own scrolling API, because that dispatches no wheel event at all and, on layouts whose scrollable element is not the document, silently does nothing while still reporting an advance. A dispatch failure during the gesture MUST abort only the current scroll and MUST NOT propagate an exception that ends the browsing loop.

#### Scenario: List paging dispatches a real wheel gesture

- **WHEN** a command advances the content list on any platform
- **THEN** it moves the cursor onto the scrollable region and dispatches multiple wheel frames with non-uniform delays
- **AND** it does not advance by calling the page's own scrolling API

#### Scenario: Transient dispatch failure does not end the session

- **WHEN** one wheel frame dispatch fails during a gesture
- **THEN** the runtime abandons the remainder of that gesture and reports the measured movement honestly
- **AND** it does not propagate a failure that terminates the browsing loop

### Requirement: Injected click helpers MUST NOT move the page or fabricate pointer events

A helper used by injected page scripts to click a resolved element MUST NOT scroll that element into view as part of the click, because that jumps the scroll position outside the pacing layer entirely. Bringing a target into view is the responsibility of the humanized scroll gesture before the click. The helper MUST NOT dispatch pointer events whose coordinates are unrelated to the element's real landing point. This MUST be enforced by a static contract check over the injected script text so that a reintroduced teleport fails the build rather than reaching a runtime.

#### Scenario: Click helper contains no teleport scroll

- **WHEN** the injected click helper of any platform router is checked
- **THEN** the static contract check reports no scroll-into-view call inside the helper
- **AND** the check fails and names the helper if one is reintroduced

#### Scenario: Off-screen target is brought into view by the gesture

- **WHEN** a target to be clicked is outside the viewport
- **THEN** the runtime advances to it with the humanized scroll gesture before clicking
- **AND** the click itself changes no scroll position

### Requirement: Captcha assist actuation MUST run on a dedicated high-scrutiny pacing tier

Synthetic clicks issued for captcha assistance MUST NOT reuse the default browsing pointer parameters. That path MUST apply its own tier: a look-and-aim pause inserted after the movement completes and before the press, a sampled pause between consecutive landing points rather than a constant one, landing-point jitter, per-frame delay jitter, and an overshoot probability. Each subsequent point MUST start from the previous point's actual landing position so the cursor track stays continuous across the whole assist sequence.

#### Scenario: Aiming pause precedes the press

- **WHEN** the assist path moves the cursor onto a landing point
- **THEN** it waits a sampled look-and-aim interval before dispatching the press

#### Scenario: Inter-point pause is sampled, not constant

- **WHEN** an assist sequence dispatches several landing points
- **THEN** the observed pauses between consecutive points differ from each other
- **AND** the cursor track of point N+1 starts at the actual landing position of point N

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
