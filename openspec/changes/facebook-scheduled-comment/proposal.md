## Why

After the platform abstraction and Facebook browser Phase-0 probes pass, aidcp needs a first Facebook business capability: scheduled automatic comments on operator-specified Pages/Groups/posts. This path is higher risk than xhs manual-reviewed comments because it is unattended, so it must be default-off, fail-closed, quota-gated, and verified by server-confirmed posting signals.

## What Changes

- Add a Facebook scheduled-comment pipeline that selects posts only from operator-configured targets, triggered through the existing two comment entry points (schedule-driven comment action and Feishu `/comment`) routed by account platform; no separate Facebook cron is added.
- Add Facebook driver targeted-comment capabilities for targeted post discovery, controlled-editor input, and server-confirmed post verification (the Facebook targeted flow MUST NOT reuse the `browse` capability string, which would attach the xhs browse session on a Facebook edge).
- Add unattended composition path using deterministic validators instead of xhs human review, without weakening xhs comment approval behavior.
- Route the existing comment entry points by `accounts.platform`, respecting account status, kill switch, quotas, and daily caps for Facebook accounts; provision `accounts.platform` at handshake insert-time so new Facebook accounts are not deadlocked.
- Capture Facebook account display names from verified login identity and persist them as account nicknames for operator-facing labels, without ever using the display name as the stable identity.
- Add shadow/dry-run mode that logs candidate/text/validator outcomes but never posts or records risk.
- Add honest stop outcomes for login loss, checkpoint, no target, no strong candidate, validator rejection, ambiguous verification, quota/cooldown denial, and kill switch.

## Capabilities

### New Capabilities

- `facebook-scheduled-comment`: Defines Facebook target configuration, scheduled cron, unattended composition validators, post execution, server-confirmed verification, shadow mode, and kill switch behavior.

### Modified Capabilities

- `comment-interaction`: Facebook automatic comments use a separate validator-gated path and MUST NOT weaken xhs manual approval.
- `interaction-risk-gating`: Facebook automatic comments must be pre-gated and counted only after verified success.
- `llm-output-honesty`: Facebook unattended comment text must pass deterministic hard validators and fail closed rather than being auto-fixed into posting.

(Cooldown stays global/uniform: accounts run on separate environments and one account never runs xhs and Facebook simultaneously, so per-account isolation suffices and the existing global comment cooldown is reused as-is — no `interaction-cooldown` delta in this change.)

## Impact

- Affected repos: `aidcp-cloud`, `aidcp-edge`, likely `aidcp-console` only if target configuration UI is included in this change.
- Cloud areas: comment entry-point routing by account platform, handshake insert-time platform provisioning, target storage/API, validators, shadow mode, kill switch, risk integration, per-trigger audit rows and stall/login alerts.
- Edge areas: Facebook targeted post extraction, comment editor execution, pre-submit block check, server-confirmed verification.
- Operational impact: starts disabled by default (`AIDCP_FB_COMMENT_AUTO=false` or equivalent); production rollout requires shadow, single disposable account, small quota, and multi-day observation.
- Scale-out boundary: before operating more than ~3 Facebook accounts, the following MUST be solved first and are explicitly out of v1 scope — automated platform provisioning beyond the handshake insert-time write, per-profile proxy/egress management (re-evaluate before productionization; not gated in v1), and cooldown/daily-count persistence (currently in-memory, reset on restart). v1 is a single disposable account with shadow-first rollout.
