## MODIFIED Requirements

### Requirement: Native pointer actuation MUST follow a humanized path

A Native pointer click MUST reach its target through a multi-frame movement whose per-frame delays are non-uniform, and MUST NOT consist of a single move that lands exactly on the target immediately followed by a press. The movement MUST include positional jitter around the sampled path and MAY include an occasional overshoot with a correction pull. Two clicks issued at the same coordinates MUST produce different frame counts or different frame timings.

This guarantee is conditioned on the remaining command budget affording it, and that condition MUST be stated rather than implied. The primitive derives a frame budget from the remaining wall-clock budget and clamps the frame count to it, so that humanization can never turn an otherwise-successful click into a timeout. Two consequences follow and MUST be treated as in-scope behavior rather than as violations:

- Where the derived budget falls below the humane frame floor, the movement carries fewer frames than the floor.
- Where the derived budget affords a single frame, the movement collapses to one frame followed by a press — that is, to the very shape the first paragraph forbids under normal budget.

Both are permitted **only** as budget-driven degradations, **only** while the click's business result stays truthful, and **only** while each is distinguishable and leaves a trace as required below. Trading humanization for budget is permitted; doing it invisibly is not.

Where a platform capability requires the pointer origin to stay inside a specific corridor (for example a control-to-flyout corridor), the caller MUST be able to supply that origin and to disable the overshoot, and the primitive MUST honor both. When the caller supplies no origin, the primitive MUST start from the last real landing point if one is known, so that consecutive clicks form a continuous cursor track; it MUST NOT jump the cursor back to a fresh random offset between two clicks that belong to the same interaction.

The scope of "last landing point" MUST be no wider than the session whose track it represents. Where the implementation holds it process-wide, that is sound **only** while one engine process drives one browser and executes commands serially; that invariant MUST be stated where the state lives, because the day it stops holding, one session's cursor position leaks into another's track and the failure is silent — the clicks still land, the track just stops being a track.

#### Scenario: Click is not a coordinate teleport

- **WHEN** the Native runtime clicks a resolved page coordinate with a remaining budget that affords the humane frame floor
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

#### Scenario: Budget below the humane floor

- **WHEN** the remaining command budget derives a frame budget below the humane frame floor
- **THEN** the movement is permitted to carry fewer frames than the floor
- **AND** the reduction is recorded as a budget-driven degradation rather than passing as an ordinary humanized path

## ADDED Requirements

### Requirement: Pointer path degradation MUST be distinguishable from a target already under the cursor

A single-frame pointer path has two causes that MUST NOT share one return shape:

- the target is already within the degenerate-distance threshold of the cursor, in which case a single frame is the **correct** movement and is not a degradation;
- the derived frame budget affords only one frame, in which case the single frame is a **degradation**.

The planned path MUST carry which of these applies, in three states: no degradation, frame count reduced below the humane floor, and collapsed to a single frame. Collapsing the causes into one shape is not permitted, because it makes correct behavior and degraded behavior indistinguishable to every consumer including the trace itself.

#### Scenario: Target already under the cursor

- **WHEN** the click target lies within the degenerate-distance threshold of the current pointer position
- **THEN** the planned path carries a single frame reported as no degradation

#### Scenario: Budget affords one frame

- **WHEN** the derived frame budget is one and the target is farther than the degenerate-distance threshold
- **THEN** the planned path carries a single frame reported as collapsed-to-single-frame

#### Scenario: Budget affords fewer than the humane floor

- **WHEN** the derived frame budget is above one but below the humane frame floor
- **THEN** the planned path reports frame count reduced below the floor, naming the achieved count and the floor

### Requirement: Pointer degradation MUST leave a trace at a single dispatch point

Where a planned path reports a degradation, the engine MUST emit a diagnostic recording it. The diagnostic MUST be produced from a pure function over the planned path, so that its content is assertable without dispatching input.

Emission MUST occur at the single pointer dispatch entry point rather than at each calling capability. Threading the degradation out to the dispatch entry's many call sites — nearly all of which discard the success value today — would create one omissible site per capability and would edit a serial single-writer file at every one of them.

The diagnostic MUST NOT attempt to name which command or which page surface the click belonged to; the engine cannot establish that. That attribution is supplied by the host when the line is forwarded, and the two parts MUST be read as one mechanism: either alone yields half a fact.

#### Scenario: Degraded path emits a diagnostic

- **WHEN** a pointer click dispatches a path reporting a budget-driven degradation
- **THEN** the engine emits a diagnostic naming the degradation state, achieved frame count, and humane floor

#### Scenario: Healthy path emits nothing

- **WHEN** a pointer click dispatches a path reporting no degradation
- **THEN** no degradation diagnostic is emitted

#### Scenario: Diagnostic content is assertable offline

- **WHEN** the diagnostic function is applied to a planned path in a unit test
- **THEN** it returns the diagnostic text without requiring a browser, a dispatch, or a running engine process

### Requirement: Pointer degradation MUST NOT change the receipt's business truth

A degraded pointer path still moves to the target, presses, and releases. The click's business result is real, so the receipt MUST continue to report success and the effect phase MUST continue to reflect what actually happened.

Degradation MUST NOT be carried in the command receipt and MUST NOT be reported to Cloud by this capability. The harm being addressed is an anti-detection quality loss that is invisible in production, not a false success; treating it as a failure signal would convert a truthful success into a false failure, which is the more damaging of the two errors.

#### Scenario: Degraded click still succeeds

- **WHEN** a click executes with a budget-driven degraded path and the press and release both dispatch
- **THEN** the receipt reports success with its normal effect phase
- **AND** the receipt carries no degradation field

#### Scenario: Budget genuinely exhausted

- **WHEN** the remaining budget is insufficient to dispatch the click at all
- **THEN** the existing honest deadline refusal applies unchanged and no success is reported
