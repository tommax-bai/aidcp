## RENAMED Requirements

- FROM: `### Requirement: Automatic Facebook scroll foreground activation is watchdog-scoped`
- TO: `### Requirement: Automatic Facebook scroll foreground activation is watchdog- or movement-scoped`

## MODIFIED Requirements

### Requirement: Automatic Facebook scroll foreground activation is watchdog- or movement-scoped

The Native Facebook runtime SHALL keep ordinary automatic list scrolling background-first. It MAY invoke `Page.bringToFront` for an automatic `page.scroll` in exactly two cases, and no others: when the reason is exactly `idle_recover_nudge`, or after a completed background Feed-list wheel has bounded same-document proof of no movement on a ready, scrollable, non-terminal surface. Each command MUST activate the exact already-bound target at most once and MUST NOT switch targets.

**Reason alone never authorizes activation beyond the watchdog reason.** A `page.scroll` carrying `feed_scroll`, `search_scroll`, `resume_redrive`, `feed_continuation_unconfirmed`, any other non-watchdog reason, or no reason at all MUST NOT invoke `Page.bringToFront` on the strength of its reason, whether it reaches Feed, Search, Reels, a no-target result, a resume path, a continuation path, or another recovery path. The second case above is not a reason-based exception: it is earned only by measured proof of no movement after input was actually dispatched, and it MUST NOT be widened into a reason.

No-target, pre-input rejection, loading, terminal, context-drift, and already-moved paths MUST remain background-only.

This requirement applies only to automatic Facebook `page.scroll`. Explicit operator actions that show a browser, guided login, and non-Facebook commands retain their existing independent foreground behavior.

#### Scenario: Watchdog recovery activates before input once

- **WHEN** Native receives `page.scroll.reason = "idle_recover_nudge"`
- **THEN** it activates the exact bound target once before scroll actuation
- **AND** it does not switch to another target
- **AND** any later no-movement classification in that command cannot activate it again

#### Scenario: Routine scroll remains in the background on reason alone

- **WHEN** Native receives a Facebook `page.scroll` with `feed_scroll`, `search_scroll`, `resume_redrive`, `feed_continuation_unconfirmed`, another non-watchdog reason, or no reason
- **THEN** it preserves the existing bounded page inspection and input gates
- **AND** it does not invoke `Page.bringToFront` on the strength of that reason, whether or not those gates ultimately dispatch input

#### Scenario: Ordinary movement remains fully backgrounded

- **WHEN** an ordinary Facebook list scroll completes with measured movement
- **THEN** Native invokes no foreground activation for that command

#### Scenario: Ordinary proven no-movement activates once after input

- **WHEN** an ordinary background wheel completes and bounded readback proves eligible same-document no movement
- **THEN** Native activates the exact bound target once before the single recovery wheel

#### Scenario: Ordinary no-target result does not cover the desktop

- **WHEN** a non-watchdog Facebook `page.scroll` resolves to no target or is rejected before input
- **THEN** it invokes neither `Page.bringToFront` nor scroll input

#### Scenario: No target or context drift never covers the desktop

- **WHEN** an ordinary scroll has no target, dispatches no wheel input, or changes document or surface before recovery
- **THEN** Native does not invoke `Page.bringToFront` through adaptive recovery

#### Scenario: Explicit operator foreground action is unchanged

- **WHEN** the operator explicitly requests to show a browser or enter guided login
- **THEN** the existing explicit foreground behavior remains available independently of the automatic scroll rule and of `page.scroll.reason`
