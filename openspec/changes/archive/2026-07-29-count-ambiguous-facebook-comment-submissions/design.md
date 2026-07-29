## Context

Edge reports a Facebook comment that received the submit `Enter` but could not be server-confirmed as `action.completed{action:"comment",ok:false,reason:"verification_ambiguous"}`. The Facebook comment scheduler already treats that receipt as submitted for target de-duplication and never retries it, while Cloud's common communication handler currently emits and persists a comment risk fact only when `ok=true`. The result is a split truth: the write is treated as potentially real for retry safety, but the durable usage ledger and “按账号·今日” projection remain zero.

The durable risk-accounting funnel is the single writer for `risk_counters`: the receipt handler first enqueues an idempotent outbox fact keyed by the envelope id, then emits `interaction.occurred`, whose subscriber immediately applies the fact. The active browse session separately derives its consumed comment count from the session budget.

## Goals / Non-Goals

**Goals:**

- Treat `verification_ambiguous` as one consumed Facebook comment submission for durable risk accounting.
- Make the minute, hour, day, and customer-facing daily projections show that consumed submission.
- Consume the active automatic session's comment budget for the same terminal receipt.
- Preserve the existing non-success terminal state, yellow result card, de-duplication, and no-retry behavior.
- Preserve exactly-once durable counting when an envelope is replayed.

**Non-Goals:**

- Do not claim that Facebook server-confirmed or displayed the comment.
- Do not count pre-submit failures, `pending_group_approval`, or `comment_rejected`.
- Do not change the Edge submit/verification algorithm, protocol payload shape, database schema, quotas, cooldowns, or retry policy.
- Do not rebuild or release an Edge installer.

## Decisions

### 1. Count the dispatch fact in the common Cloud receipt handler

The handler will classify a countable comment fact as either `ok=true` or `action="comment" && reason="verification_ambiguous"`. Both cases enter the existing risk-accounting funnel and emit `interaction.occurred`; other failed comments remain outside it.

This is preferable to calling `RiskController.record()` from the comment scheduler because all Facebook comment sources ultimately report through the same `action.completed` receipt, while scheduler-local writes would miss role-driven comments and could double-count confirmed receipts.

### 2. Reuse the scoped Edge receipt identity as the accounting idempotency key

The existing scoped key combines account id, Edge environment id, original envelope timestamp/id, and action. A retransmitted terminal receipt therefore conflicts with the existing outbox uniqueness boundary and cannot increment `risk_counters` twice, while coincident envelope ids from another account, environment, or process epoch do not collide.

Adding a second comment-specific ledger or a new submitted-count column was rejected: the operator asked for the existing comment quantity to include the consumed submission, and a parallel counter would make admission quotas and display disagree.

### 3. Separate consumption from success everywhere

`verification_ambiguous` will consume the active automatic session comment budget, but mandatory-comment outcome reporting remains `unknown`, `comment.done.ok` remains false, and result cards remain warning/non-success. Its risk event omits `targetId`, so the existing `interaction_feed` success/activity projection cannot record it as a completed comment. “Counted” means the account spent one potentially real platform action, not that the comment is confirmed live.

`pending_group_approval` and `comment_rejected` retain their dedicated known-not-live semantics and are not counted. Other `ok=false` reasons remain non-dispatched or unproven and are not counted.

### 4. Let existing projections display the durable result

No table or client renderer change is required. “按账号·今日”, the customer-auth daily usage response, and periodic compatible snapshots already read the durable risk totals; once the fact reaches `risk_counters`, their existing comment field will show it.

## Risks / Trade-offs

- [An ambiguous submission might not ultimately become live] → Keep every success surface non-success and describe the number as consumed/submitted usage; counting is intentionally conservative for account safety.
- [A broad `ok=false` rule could count real failures] → Whitelist only `verification_ambiguous`; retain explicit regression cases for approval, rejection, and pre-submit failures.
- [The shared accounting event could populate a success-oriented activity feed] → Omit `targetId` for ambiguous comment usage events; retain it for confirmed comments and test both cases.
- [Receipt replay could double-count] → Reuse the existing envelope-scoped outbox dedupe key and test duplicate delivery.
- [Session and durable counters could temporarily differ] → Consume the automatic session budget at the same terminal classification; durable daily totals remain authoritative and survive restart.

## Migration Plan

1. Land the Cloud-only change and focused regression tests.
2. Deploy the clean integrated Cloud default branch to DEV after the standard target preflight.
3. Verify service, listener, health, database gates, and deployed SHA without issuing an unauthorized Facebook write.
4. On the next authorized ambiguous real-account comment, verify that the result remains warning/unknown while the account's daily comment count increments once.

Rollback is a normal Cloud source revert. Existing durable counter facts represent actions already dispatched and must not be deleted during rollback.

## Open Questions

None.
