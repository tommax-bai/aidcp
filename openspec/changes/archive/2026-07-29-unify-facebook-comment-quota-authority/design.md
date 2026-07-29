## Context

Facebook targeted comments currently pass the account `RiskController`, then pass a second feature-local daily cap read from `AIDCP_FB_COMMENT_DAILY_CAP`. The first authority counts durable action facts in `risk_counters` and uses the visible `quota_config`; the second counts rows in `risk_interactions`, whose primary purpose is same-target de-duplication. On DEV the visible normal-tier comment limit is eight while the hidden environment value is one, so the hidden gate vetoes the visible policy.

The Facebook rule pipeline checks join risk before invoking the join-contact orchestrator, but it does not preflight comment risk or comment session budget until after the new group has been joined. The combined result card also omits its automatic source and is therefore rendered as the default manual `/comment` command.

The preceding `count-ambiguous-facebook-comment-submissions` change already routes future `verification_ambiguous` comment receipts through the idempotent `risk_counter_outbox` / `risk_counters` funnel. This change consumes that authority; it does not create another counter or backfill historical rows.

## Goals / Non-Goals

**Goals:**

- Make the visible `RiskController` quota the only hard safety quota for Facebook automatic comments.
- Keep `risk_interactions` solely as the durable same-target de-duplication ledger.
- Avoid an irreversible rule-mode group join when the comment leg is already blocked by current safety quota or session budget.
- Re-read comment admission immediately before submission so a preflight never becomes a stale authorization.
- Identify rule-mode result cards as automatic rule results.
- Preserve confirmed-versus-ambiguous outcome honesty.

**Non-Goals:**

- Do not change quota values, quota tiers, risk-state transitions, or cooldowns.
- Do not remove visible content-schedule enablement, approval mode, or schedule-level daily planning controls.
- Do not change manual `/comment` override behavior.
- Do not add a table, protocol field, retry, fallback, or compatibility branch.
- Do not backfill or delete historical `risk_interactions` or `risk_counters` rows.

## Decisions

### 1. Remove the feature-local cap instead of synchronizing it

Cloud will remove the `facebookDailyCap` and `facebookCommentedToday` scheduler dependencies and the `AIDCP_FB_COMMENT_DAILY_CAP` composition-root read. Automatic Facebook comments will continue to call the account `RiskController`, whose effective quota is sourced from visible `quota_config` and whose usage is sourced from durable `risk_counters`.

Synchronizing the environment value to the visible value was rejected because it would retain two authorities that can drift again and would still require a service restart for an otherwise hot-loaded policy.

The existing content-schedule daily cap remains a visible scheduling control at its existing entry point. It is not a second hard safety authority inside the Facebook targeted-comment pipeline.

### 2. Preserve the two-ledger separation

`risk_interactions` will still record a confirmed or `verification_ambiguous` target so the same account does not retry the same post. It will no longer be queried by the Facebook scheduler to decide daily capacity.

`risk_counters` remains the append-only consumed-action ledger. Confirmed and `verification_ambiguous` submissions enter it through the existing envelope-scoped outbox identity; pre-submit failures, participation approval, and explicit platform rejection remain outside it.

### 3. Preflight comment admission before rule-mode join and re-read before submit

At the single rule-mode join-contact entry, Cloud will check:

1. current `RiskController.explain('comment')`; and
2. the active session's remaining comment budget.

If either rejects, the round terminates with `join_state=not_started`, `comment_state=risk_suppressed`, and the stable blocker; no join command is dispatched. This preflight reduces avoidable irreversible joins but is not an authorization lease.

The existing `actionGate('comment')` read after membership confirmation and immediately before submission remains. A quota/state change between preflight and submit therefore fails closed.

Moving the check only into the comment scheduler was rejected because the `RoleDispatcher` owns the active session budget and the durable rule-batch terminal projection.

### 4. Propagate the automatic source to the combined result card

The join-comment flow will pass a stable human-readable source for `facebook_rule_batch` to `postResultCard`. Manual calls continue to omit the source and render as `/comment`; scheduled rule rounds render as `Facebook 规则模式`.

Adding a protocol field was rejected because this is Cloud-local notification metadata and the existing structured-notification port already accepts a source string.

## Risks / Trade-offs

- [A minute/hour quota can release shortly after preflight] → The rule round remains a truthful terminal no-op with no debt; existing rule cadence may create a later independent round.
- [Quota can become exhausted after preflight] → Keep both post-join and pre-submit `actionGate` reads; never treat the preflight as reserved capacity.
- [Removing the hidden cap increases automatic comment capacity from one to the visible policy] → This is the intended visible configuration authority; current safety quotas, state scaling, slow-start clamp, session budget, approval, target and verification gates remain.
- [Historical ambiguous submissions are absent from `risk_counters`] → Do not synthesize facts without their original idempotency identity; only future receipts use the corrected accounting path.
- [The DEV environment line could mislead future operators even after code removal] → Back up the runtime environment and remove only `AIDCP_FB_COMMENT_DAILY_CAP` after the integrated revision is deployed.

## Migration Plan

1. Land the Cloud implementation and regression coverage.
2. Deploy only the clean integrated Cloud default branch to DEV after the standard preflight and backup.
3. Remove the obsolete DEV environment line after backing up `.env`, restart only `aidcp-cloud.service`, and verify source hashes, schema gates, writer lock, listeners, health, Feishu, PostgreSQL, and unrelated service isolation.
4. Verify through read-only source/config inspection that the deployed runtime no longer reads `AIDCP_FB_COMMENT_DAILY_CAP`.
5. Do not issue an unauthorized Facebook write. The next authorized rule round is the real-account acceptance boundary.

Rollback restores the previous Cloud revision and the backed-up environment file together. Existing durable action facts MUST NOT be deleted.

## Open Questions

None.
