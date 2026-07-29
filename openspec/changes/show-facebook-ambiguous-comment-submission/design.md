## Context

`FacebookCommentExecutor` returns `verification_ambiguous` only after it dispatched submit and bounded verification could not confirm the comment on Facebook. Cloud already treats that outcome as a consumed, de-duplicated submission while preserving `ok=false`. The join-comment receipt formatter currently sends every non-`commented` outcome through one “未评论 / 未发出” branch, erasing the dispatched-vs-not-dispatched distinction in Feishu notifications for both rule mode and manual join-comment flows.

## Goals / Non-Goals

**Goals:**

- Project `verification_ambiguous` as “joined, submitted, publication result unconfirmed”.
- Keep the card warning/non-success so submission is not confused with platform confirmation.
- Cover the title, message, and neighboring known-not-live outcomes with focused tests.

**Non-Goals:**

- Do not change Edge submission or verification.
- Do not change protocol payloads, risk accounting, session budgets, de-duplication, retries, or interaction activity.
- Do not claim that the comment is visible on Facebook.

## Decisions

### Branch on the typed terminal outcome in the receipt formatter

`joinCommentReceipt` will add one explicit branch for `comment.outcome === 'verification_ambiguous'` before the generic failure branch. That is the narrowest point with both join context and the typed comment result, and it automatically serves the rule-mode and manual notification sources without duplicating display logic.

Using text returned by `commentOutcomeReason()` to infer submission state was rejected because presentation strings are not a stable outcome contract. Changing the executor result was rejected because the executor already reports the correct evidence.

### Preserve warning status while using positive action wording

The card will remain `ok=false` and `level=warning`, but its title will state “已加群，已评论，未确认发布结果” and its message will state that the comment was submitted while Facebook visibility remains unconfirmed. “已评论” here names the dispatched comment action, not platform-confirmed publication; the same card immediately states the confirmation boundary.

Confirmed `commented` remains the only success branch. `pending_group_approval`, `comment_rejected`, pre-submit failures, and unexpected failures remain on the generic non-submitted branch.

## Risks / Trade-offs

- [Readers may interpret “已评论” as server-confirmed] → Keep the same title and message explicit about “未确认发布结果 / 是否上墙尚未确认”, and keep warning styling.
- [A broad refactor could change unrelated outcomes] → Add only one typed branch and retain focused assertions for a known pre-submit failure.
- [A source-only Cloud change could be mistaken for a released client fix] → Deploy only the integrated Cloud change to DEV and report that no Edge installer or OL release is involved.
