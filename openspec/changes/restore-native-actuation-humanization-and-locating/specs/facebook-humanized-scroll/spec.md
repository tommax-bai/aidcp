## ADDED Requirements

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
