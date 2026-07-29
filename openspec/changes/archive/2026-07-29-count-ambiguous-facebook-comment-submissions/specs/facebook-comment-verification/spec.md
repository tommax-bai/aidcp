## MODIFIED Requirements

### Requirement: Unconfirmable submission is honestly ambiguous and de-duplicated

When the in-place watch cannot confirm the own+text comment within its bounded window, the edge SHALL report `verification_ambiguous` (submitted, not server-confirmed) rather than claim success or claim a clean hard failure. This outcome MUST continue to mark the target as de-duplicated so the same comment is not re-posted on a later run.

Cloud MUST count each idempotently distinct `verification_ambiguous` Facebook comment receipt as one consumed comment submission in the durable risk-accounting ledger. The consumed submission SHALL appear in the account's existing minute, hour, day, and “按账号·今日” comment usage and SHALL consume one comment from an active automatic session budget. Counting the submission MUST NOT change its terminal state to success, increment a platform-confirmed-success metric, render a success card, or create a completed-comment entry in the interaction activity feed. A replay of the same terminal receipt MUST NOT count twice.

Exception 1: when the edge recognizes a group **participation-approval gate** (see "Participation-approval gate is recognized and reported as pending group approval"), it SHALL report `pending_group_approval` instead of `verification_ambiguous`. Unlike `verification_ambiguous`, `pending_group_approval` means the comment did not go live (it became a participation application), so it MUST NOT be counted as a real submission and MUST NOT be de-duplicated as posted; the same target may be legitimately attempted again after the account is approved.

Exception 2: when the edge recognizes a **platform rejection indicator** on the own+text comment row (see "Platform-rejected comments are an honest terminal outcome"), it SHALL report the rejected outcome instead of `verification_ambiguous`. The comment is known not to be live, so it MUST NOT be de-duplicated as posted or counted as a consumed comment submission.

#### Scenario: Neither confirmed nor classified is honestly ambiguous
- **WHEN** the in-place window expires without ack-gated signals, without a rejection indicator, and without a participation-approval gate
- **THEN** the edge reports `verification_ambiguous`, the target is de-duplicated, and Cloud records exactly one consumed comment submission while keeping the terminal result non-success

#### Scenario: Ambiguous submission appears in daily usage
- **WHEN** Cloud durably applies a distinct `verification_ambiguous` Facebook comment receipt for an account
- **THEN** that account's existing comment usage increases by one in every applicable durable window and “按账号·今日” displays the increased value without adding a completed-comment activity entry

#### Scenario: Ambiguous receipt replay is idempotent
- **WHEN** Cloud receives the same `verification_ambiguous` terminal receipt more than once
- **THEN** the durable comment usage and active session consumption increase exactly once

#### Scenario: Rejection is not collapsed into ambiguous
- **WHEN** the own+text comment row carries a platform rejection indicator
- **THEN** the edge reports the rejected outcome, not `verification_ambiguous`, and the target is neither de-duplicated as posted nor counted as a consumed comment submission

#### Scenario: Participation approval is not counted
- **WHEN** the comment terminal outcome is `pending_group_approval`
- **THEN** Cloud keeps the pending non-success outcome and does not increment comment usage
