## ADDED Requirements

### Requirement: Automatic Facebook scroll foreground activation is watchdog-scoped

The Native Facebook runtime SHALL treat `page.scroll.reason = "idle_recover_nudge"` as the sole automatic scroll intent authorized to activate the exact already-bound Facebook target. Each such command SHALL invoke `Page.bringToFront` exactly once and MUST retain the same target identity. A `page.scroll` with a missing reason or any other reason MUST NOT invoke `Page.bringToFront`, regardless of whether it reaches Feed, Search, Reels, a no-target result, a resume path, a continuation path, or another recovery path.

This requirement applies only to automatic Facebook `page.scroll`. Explicit operator actions that show a browser, guided login, and non-Facebook commands retain their existing foreground behavior.

#### Scenario: Watchdog recovery scroll activates once

- **WHEN** Native receives a Facebook `page.scroll` whose reason is exactly `idle_recover_nudge`
- **THEN** it activates the exact bound target exactly once before scroll actuation
- **AND** it does not switch to another target

#### Scenario: Routine scroll remains in the background

- **WHEN** Native receives a Facebook `page.scroll` with `feed_scroll`, `search_scroll`, `resume_redrive`, `feed_continuation_unconfirmed`, another non-watchdog reason, or no reason
- **THEN** it preserves the existing bounded page inspection and input gates
- **AND** it does not invoke `Page.bringToFront`, whether or not those gates ultimately dispatch input

#### Scenario: Ordinary no-target result does not cover the desktop

- **WHEN** a non-watchdog Facebook `page.scroll` resolves to no target or is rejected before input
- **THEN** it invokes neither `Page.bringToFront` nor scroll input

#### Scenario: Explicit operator foreground action is unchanged

- **WHEN** the operator explicitly requests to show a browser or enter guided login
- **THEN** the existing explicit foreground behavior remains available independently of `page.scroll.reason`
