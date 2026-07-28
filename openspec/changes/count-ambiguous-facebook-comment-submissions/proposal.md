## Why

Facebook `verification_ambiguous` already means the comment submit action was dispatched and must not be retried, but Cloud currently excludes that receipt from durable risk counters and session usage. Operators therefore see `0` comments in “按账号·今日” even though the account has consumed a potentially real platform write.

## What Changes

- Count a Facebook comment receipt with `reason=verification_ambiguous` as one consumed comment submission in the durable minute, hour, and day risk windows.
- Consume one comment from the active session budget for the same receipt so the session and durable usage projections remain aligned.
- Keep the outcome non-success: result cards and terminal state remain “submitted but not server-confirmed”, with no platform-success claim.
- Keep pre-submit failures, participation approval, and explicit platform rejection outside the comment count.
- Preserve idempotent accounting so a replayed terminal receipt cannot count twice.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-comment-verification`: Extend the existing submitted-but-unconfirmed contract so an ambiguous submission consumes and appears in comment usage without becoming confirmed success.

## Impact

- `aidcp-cloud` communication receipt accounting and Facebook session-budget handling.
- Durable `risk_counter_outbox` / `risk_counters` projections used by “按账号·今日” and client daily usage.
- Focused Cloud protocol, risk-accounting, and dispatcher tests.
- No protocol shape, database schema, Edge package, or success-card contract changes.
