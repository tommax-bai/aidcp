## ADDED Requirements

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
