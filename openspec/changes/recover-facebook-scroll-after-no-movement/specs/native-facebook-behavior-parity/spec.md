## ADDED Requirements

### Requirement: Automatic Facebook scroll foreground activation is watchdog- or movement-scoped

The Native Facebook runtime SHALL keep ordinary automatic list scrolling background-first. It MAY invoke `Page.bringToFront` for an automatic `page.scroll` only when the reason is exactly `idle_recover_nudge`, or after a completed background Feed-list wheel has bounded same-document proof of no movement on a ready, scrollable, non-terminal surface. Each command MUST activate the exact already-bound target at most once and MUST NOT switch targets. No-target, pre-input rejection, loading, terminal, context-drift, and already-moved paths MUST remain background-only. Explicit operator foreground actions and non-Facebook commands retain their existing independent behavior.

#### Scenario: Watchdog recovery activates before input once

- **WHEN** Native receives `page.scroll.reason = "idle_recover_nudge"`
- **THEN** it activates the exact bound target once before scroll actuation
- **AND** any later no-movement classification in that command cannot activate it again

#### Scenario: Ordinary movement remains fully backgrounded

- **WHEN** an ordinary Facebook list scroll completes with measured movement
- **THEN** Native invokes no foreground activation for that command

#### Scenario: Ordinary proven no-movement activates once after input

- **WHEN** an ordinary background wheel completes and bounded readback proves eligible same-document no movement
- **THEN** Native activates the exact bound target once before the single recovery wheel

#### Scenario: No target or context drift never covers the desktop

- **WHEN** an ordinary scroll has no target, dispatches no wheel input, or changes document or surface before recovery
- **THEN** Native does not invoke `Page.bringToFront` through adaptive recovery

#### Scenario: Explicit operator foreground action is unchanged

- **WHEN** the operator explicitly requests to show a browser or enter guided login
- **THEN** the existing explicit foreground behavior remains available independently of the automatic scroll rule
