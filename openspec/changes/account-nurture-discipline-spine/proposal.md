## Why

Before Facebook is fully connected (automatic browse / like / publish), aidcp must first wire up the account-nurture discipline spine. Two "blueprints drawn but never connected" bridges are currently broken, and both accelerate account bans once Facebook writes at volume:

1. **Account age → quota ramp is dead code.** `ColdStartPlanner` already defines Day1–7 nurture bands plus a `quotaOverride(createdAt)`, but `effectiveQuotas()` never reads `created_at`. A brand-new account on Day 1 therefore consumes the full `normal` allotment (view 150 / like 50 / comment 8 / follow 15 / publish 1) — exactly the burst signature platforms flag as a nurtured-farm account.
2. **Platform throttling → backoff never fires.** The risk state machine's only automatic `applySignal` entry point is the captcha overlay. Facebook's primary throttling surfaces — inline "Action Blocked" / "we limit how often you can do this" / "misusing this feature" / "you can't use this feature right now" toasts, and comments silently hidden seconds after posting — are never sensed. A throttled account keeps dispatching at `normal` volume and drives itself deeper into a ban.

Two secondary gaps compound this: write operations over an untrusted egress (China IP / datacenter range) are high-risk yet the cloud has zero visibility into the session's real exit IP; and the per-action minimum-interval cooldown plus per-session search counters are in-memory only, so a process restart zeroes them and lets the first post-restart batch burst past the pacing floor.

## What Changes

- Wire the cold-start quota ramp into `effectiveQuotas()` as a **downward** clamp (min semantics): daily effective quota = `min(age-band cold-start quota, risk-scaled quota)`, so age ramp and risk backoff (warned/restricted) compose instead of one silently overriding the other.
- Give Facebook a **more conservative** cold-start curve than xiaohongshu (D1–3 browse + minimal likes only, comments from D3, publish/group-join from D5).
- Add a per-Facebook-account **daily online-minutes budget** (reusing the existing daily online budget + active-window machinery).
- Add **egress visibility**: on Facebook session start the edge reports the session's real exit IP/geo (reusing the fingerprint WebRTC = proxy probe); the cloud raises an operations alert on risky egress but, per the approved v1 decision, **only warns — it never blocks any action**.
- Escalate Facebook **soft-block throttling signals** into an aggressive risk backoff: the account is driven to `restricted` (browse-only) via the existing `applySignal` input.
- Add a **post-restart cold-start quiet period** that suppresses action bursts for a few minutes after process start.

All defaults point in the safe direction. This change does NOT touch the protocol, does NOT add any new risk action, and does NOT change the risk state-machine transition table.

## Capabilities

### New Capabilities

- `account-nurture-discipline`: Defines account-age cold-start quota clamping (min semantics), a more conservative Facebook cold-start curve, per-Facebook-account daily online-minutes budget, and egress-visibility warn-only alerting.

### Modified Capabilities

- `captcha-incident-handling`: Adds Facebook soft-block throttling signals (inline block toasts, silently-hidden comments, N consecutive post-check failures) as inputs that escalate the account to `restricted` via the existing cloud-single-writer `applySignal`.
- `interaction-cooldown`: Adds a post-restart cold-start quiet period so the in-memory min-interval cooldown and per-session search counters cannot be bypassed by a process restart.

## Impact

- **Affected repos**: `aidcp-cloud` (primary), `aidcp-edge` (minimal), `aidcp-console` (read-only display), `aidcp` (this change).
- **Cloud areas**: risk `effectiveQuotas()` wired to cold-start age quota; platform-selected cold-start curve; overlay text library extended + fed into `applySignal`; per-restart cold-start quiet period; per-account daily online-minutes budget; egress-risk alerting.
- **Edge areas** (minimal): report egress IP/geo on Facebook session start (reuse fingerprint WebRTC = proxy probe); extend Facebook throttling-overlay text recognition and report it as a throttling signal.
- **Console areas** (read-only): surface egress alerts and current risk state; no write path.
- **Config / env**: cold-start ramp and Facebook backoff ship default-on because they are safe-direction; every knob is env-gated for A/B and instant rollback. Egress alerting is observe-only.
- **NOT touched**: `protocol.ts` (either copy), `RISK_ACTIONS`, the risk state-machine transition table.
- **Reuse-first**: reuse `ColdStartPlanner` (existing dead code, now connected), the existing `applySignal` / overlay reporting channel, the existing daily online budget (`dailyCaps.maxMinutes`) + active-window machinery, and the existing egress fingerprint probe.
- **Deployment**: ol (isolation window); ramp + backoff default-on as safe direction, egress alerting in observe mode.
