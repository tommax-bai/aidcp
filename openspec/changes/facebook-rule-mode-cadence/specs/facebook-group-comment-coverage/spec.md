## MODIFIED Requirements

### Requirement: An account does not comment in a group the day it joined it

The ordinary coverage loop SHALL enforce a join-to-first-comment warmup interval: a group becomes eligible for unpinned coverage only after a bounded delay following its `joined_at`, so ordinary coverage, persona-mode comments and standalone automatic joins do not join and immediately comment in the same group on the same day.

The sole exception SHALL be a caller-pinned group joined by the same fixed Facebook rule batch. After the join stage returns platform-confirmed `joined` or `already_member` for the exact group, slow start is confirmed not active, and every comment/contact/approval/risk gate passes, that batch MAY continue to a contact comment without waiting for ordinary coverage warmup. The exception MUST NOT make the group generally warmup-eligible, MUST NOT apply to an ambiguous/pending/failed join, and MUST NOT be inferred from a bare group URL or membership row without the rule batch correlation.

#### Scenario: Same-day ordinary coverage is not commented
- **WHEN** an account joined a group earlier the same day and an unpinned coverage run considers it
- **THEN** the coverage loop does not select that group until the warmup interval has elapsed

#### Scenario: Confirmed rule batch may continue in its pinned group
- **WHEN** the same Facebook rule batch joined exact group G with a platform-confirmed result, slow start is not active and all comment gates allow
- **THEN** the batch may select and contact-comment in pinned group G without making G available to ordinary coverage

#### Scenario: Slow start prevents the scoped exception
- **WHEN** slow start becomes active before the rule batch's comment dispatch
- **THEN** the comment is not dispatched and the same-day warmup exception is not applied

#### Scenario: Unconfirmed join never receives the exception
- **WHEN** the rule batch's join result is pending, ambiguous, gated, failed or lacks the exact confirmed group identity
- **THEN** no comment starts and ordinary warmup behavior remains unchanged
