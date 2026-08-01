## MODIFIED Requirements

### Requirement: Facebook wheel fallback never doubles a successful gesture

The edge SHALL observe the real Facebook list scroll-container position before and after each completed Native wheel gesture. Any measured movement, including a partially completed gesture, MUST suppress foreground recovery and additional wheel input. When a completed background gesture leaves that position unchanged on the same ready, scrollable, non-terminal document, the edge MAY activate the exact already-bound target at most once, SHALL re-probe the same document and list surface, and MAY dispatch exactly one fresh humanized Native wheel recovery gesture. An eager watchdog activation consumes that same one-activation allowance. The edge MUST NOT use JavaScript `window.scrollBy` or DOM-dispatched wheel events as the fallback. If the foreground recovery still makes no movement, the edge SHALL return an ambiguous scroll outcome before confirming any already-readable cards.

#### Scenario: Wheel movement suppresses foreground recovery

- **WHEN** the real Facebook list scroll-container position changes after the background wheel gesture
- **THEN** the edge does not invoke `Page.bringToFront` and does not dispatch a recovery wheel

#### Scenario: Eligible background no-movement gets one foreground recovery

- **WHEN** a completed background wheel leaves a ready, scrollable, non-terminal Facebook list unchanged on the same document and surface
- **THEN** the edge activates the exact bound target once, re-probes that same context, and dispatches exactly one fresh humanized wheel gesture
- **AND** it does not execute JavaScript scrolling

#### Scenario: Non-actionable no-movement remains background-safe

- **WHEN** the scroll position is unchanged because the list is loading, at bottom, blocked, no longer scrollable, or changed document or surface
- **THEN** the edge does not activate the browser through the adaptive recovery path

#### Scenario: Foreground recovery still makes no movement

- **WHEN** the one foreground recovery gesture completes and the same non-terminal list position remains unchanged
- **THEN** the edge returns an ambiguous `scroll_movement_unconfirmed` outcome
- **AND** already-readable cards do not confirm the failed scroll

#### Scenario: Watchdog activation is not repeated

- **WHEN** `idle_recover_nudge` already activated the exact target before its wheel gesture
- **THEN** the no-movement path does not invoke `Page.bringToFront` again
