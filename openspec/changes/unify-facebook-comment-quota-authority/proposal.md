## Why

Facebook automatic comments currently have two conflicting daily-admission authorities: the visible `RiskController` safety quota backed by `risk_counters`, and a hidden environment cap backed by `risk_interactions`. This lets a hidden DEV value reject Nancy at one comment even while the visible normal-tier safety policy allows eight, and it can join a new group before discovering that the comment leg is blocked.

## What Changes

- Make `RiskController` and its visible `quota_config` minute/hour/day limits the only hard safety-quota authority for Facebook automatic comments.
- Remove the hidden `AIDCP_FB_COMMENT_DAILY_CAP` admission path and stop using `risk_interactions` as a daily quota counter; retain `risk_interactions` only for same-target de-duplication.
- Before a Facebook rule round performs an irreversible group join, preflight the comment leg against the same current `RiskController` and session budget that will be re-read immediately before comment submission.
- Preserve conservative accounting: both confirmed and `verification_ambiguous` submissions consume the durable `risk_counters` quota without turning an ambiguous outcome into success.
- Label automatic rule-mode result cards by their real source instead of presenting them as a manual `/comment` command.
- Preserve manual `/comment` override semantics and visible schedule/approval controls.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `interaction-risk-gating`: Establish `risk_counters` plus `RiskController` as the sole hard safety-quota ledger/decision path, while `risk_interactions` remains target de-duplication only.
- `facebook-scheduled-comment`: Remove the hidden Facebook-specific daily cap from automatic targeted comments and retain the visible safety and schedule gates.
- `facebook-rule-mode`: Preflight the comment safety/session gates before joining, re-read them before comment submission, and identify automatic rule receipts truthfully.

## Impact

- `aidcp-cloud` comment scheduler composition, Facebook rule orchestration, result-card source metadata, and focused tests.
- OpenSpec deltas for risk gating, Facebook scheduled comments, and Facebook rule mode.
- DEV runtime configuration cleanup after the integrated code no longer reads `AIDCP_FB_COMMENT_DAILY_CAP`.
- No protocol shape, database schema, Edge package, retry policy, approval policy, or success-verification change.
