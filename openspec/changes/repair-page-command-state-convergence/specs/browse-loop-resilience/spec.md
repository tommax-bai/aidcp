## ADDED Requirements

### Requirement: Recoverable list-surface transitions SHALL use bounded immediate recovery
Cloud MUST distinguish a confirmed list-surface transition whose semantic content is still rendering from an ordinary scroll failure and MUST attempt bounded recovery without waiting for the generic idle watchdog.

#### Scenario: Pending Reels transition receives bounded retry
- **WHEN** Edge reports `reels_pending` after Cloud authorized an empty-Feed fallback
- **THEN** Cloud SHALL retain pending authorization and issue a surface-aware retry through existing admission and quota gates within a bounded number of attempts

#### Scenario: Reels cards confirm the transition
- **WHEN** Cloud receives `page.cards` identified as Reels during a pending fallback
- **THEN** Cloud SHALL mark the fallback confirmed and stop transition retries

#### Scenario: Unconfirmed transition remains eligible after terminal failure
- **WHEN** the bounded transition attempt fails without confirming a Reels route or card
- **THEN** Cloud SHALL return the authorization state to retryable rather than treating the fallback as permanently consumed
