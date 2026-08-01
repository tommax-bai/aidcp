# facebook-humanized-scroll Specification

## Purpose
TBD - created by archiving change facebook-humanized-scroll. Update Purpose after archive.
## Requirements
### Requirement: Facebook feed scroll is an inertial wheel gesture

The edge SHALL turn each Facebook feed scroll request into one downward wheel gesture with a target distance sampled within +/-20% of a 650 CSS-pixel baseline. The gesture SHALL use the shared scroll-physics sequence, dispatch 8 to 15 `Input.dispatchMouseEvent` wheel frames at the viewport centre, and honor the generated per-frame delay. The sequence SHALL preserve the sampled total distance and SHALL not alter cloud-directed dwell timing.

#### Scenario: Feed wheel gesture has a humanized shape
- **WHEN** the Facebook browse session requests its next feed page
- **THEN** the edge dispatches a cursor move followed by 8 to 15 non-uniform wheel frames whose total equals the sampled target and whose peak is not at either endpoint

### Requirement: Facebook wheel fallback never doubles a successful gesture

The edge SHALL observe document scroll position before and after each Facebook wheel gesture. It SHALL execute at most one JavaScript `window.scrollBy` fallback only when the observed position did not change; it SHALL not execute that fallback after any measured movement, including a partially completed wheel sequence.

#### Scenario: Wheel movement suppresses JavaScript fallback
- **WHEN** the Facebook document scroll position changes after the wheel gesture
- **THEN** the edge does not execute `window.scrollBy`

#### Scenario: Wheel input makes no movement
- **WHEN** the Facebook document scroll position is unchanged after a completed or interrupted wheel gesture
- **THEN** the edge executes one bounded JavaScript fallback and continues the browse command without reporting a fabricated action result

### Requirement: Facebook comment-editor scrolling shares the gesture boundary

The edge SHALL use the same Facebook viewport gesture helper when scrolling to reveal a comment editor. It SHALL preserve the existing bounded editor-probe loop and honest `editor_not_found` / `permission_gated` outcomes.

#### Scenario: Comment editor becomes visible after scroll
- **WHEN** the editor is absent on the first probe and becomes available after one scroll gesture
- **THEN** the executor focuses the editor and the gesture uses multi-frame wheel input rather than a single fixed wheel event

### Requirement: Facebook pre-action alignment scrolling shares the humanized gesture boundary

When the edge scrolls to bring a target control into the viewport before a Facebook write action, it MUST use the same shared wheel gesture used for feed paging: a cursor move followed by multiple non-uniform wheel frames with the established per-frame delay range. It MUST NOT dispatch a single wheel frame whose delta is computed directly from the measured offset between the control and the viewport, because that makes the dispatched distance an exact function of the target's position. The wait between one alignment gesture and the following re-probe MUST vary rather than being a constant.

Alignment MUST remain bounded and MUST keep re-resolving the exact target and its control after each gesture. When the bound is exhausted without the control entering the eligible viewport band, the edge MUST return a truthful not-visible outcome and MUST NOT act on whatever is currently in view.

#### Scenario: Alignment before a feed like is a multi-frame gesture

- **WHEN** the exact target's post-level reaction control is outside the eligible viewport band before a feed like
- **THEN** the edge dispatches a cursor move plus multiple non-uniform wheel frames, then re-resolves the exact target and control
- **AND** it does not dispatch one wheel frame whose delta equals the measured control offset

#### Scenario: Alignment settle wait is not a fixed constant

- **WHEN** two consecutive alignment rounds occur in one session
- **THEN** the observed waits between gesture and re-probe differ

#### Scenario: Bound exhausted without visibility stays honest

- **WHEN** the alignment bound is reached and the control is still outside the eligible band
- **THEN** the edge returns a not-visible not-started outcome and dispatches neither the primary actuation nor a fallback click

### Requirement: Pre-action alignment MUST be able to see a takeover

The cancellation signal and the absolute deadline MUST be passed into the alignment loop and observed between its rounds, and the wait between a gesture and the following re-probe MUST be interruptible by that signal.

This is not a matter of yielding a little sooner. A like is a **write** command, and the host deliberately does not race writes against cancellation — tearing a write mid-dispatch is worse than letting it finish. The alignment loop is therefore the **only** place on this path where a takeover can be seen at all. Without the wiring the outcome is not a slow hand-over: the coordinator has already called the action off, and the loop scrolls on to the target and dispatches the like anyway — an action that was cancelled still leaves a new trace on the platform under that account.

Cancellation observed in the loop MUST be reported as not-dispatched, because scrolling is not an irreversible write and nothing has been left on the page at that point.

#### Scenario: Takeover during alignment stops before the write

- **WHEN** the cancellation signal is raised while the alignment loop is still bringing the control into view
- **THEN** the edge abandons the alignment and reports a not-dispatched outcome
- **AND** it does not dispatch the like it was aligning for

### Requirement: Facebook Reels fallback scrolling shares the humanized gesture boundary

The wheel fallback used to advance the Facebook short-video surface, after trusted key input produced no measured movement, MUST use the same shared humanized gesture including the preceding cursor move. Its distance MUST come from the gesture's own sampling around a baseline and MUST NOT be derived from wall-clock arithmetic. The fallback MUST keep its existing movement check and MUST NOT report advancement that was not measured.

#### Scenario: Reels fallback wheel is a humanized gesture

- **WHEN** trusted key input leaves the short-video surface unmoved and the edge falls back to wheel input
- **THEN** it dispatches a cursor move followed by multiple non-uniform wheel frames over the video area
- **AND** the sampled distance is not a function of the current wall-clock value

#### Scenario: Unmoved surface after fallback is reported honestly

- **WHEN** the fallback gesture completes and the measured surface identity is unchanged
- **THEN** the edge reports the honest no-movement outcome rather than a fabricated advance

