# Design — account-nurture-discipline-spine

## Context

The system splits into an edge execution end (aidcp-edge) and a cloud decision end (aidcp-cloud), with the risk final state written only by the cloud `RiskController` (state machine `normal → warned → restricted → frozen`). Before Facebook is fully connected for automatic browse / like / publish, two nurture-discipline bridges are "drawn but never connected", and both accelerate bans once Facebook writes at volume:

1. **Account age → quota ramp is dead code.** `ColdStartPlanner` defines Day1–7 nurture bands and a `quotaOverride(createdAt)`, but `effectiveQuotas()` never reads `created_at`. A Day-1 account consumes the full `normal` allotment (view 150 / like 50 / comment 8 / follow 15 / publish 1) — the burst signature of a nurtured-farm account.
2. **Platform throttling → backoff never fires.** `applySignal`'s only automatic entry is the captcha overlay. Facebook's main throttling surfaces (inline "Action Blocked" / rate-limit / "misusing this feature" toasts, and comments hidden seconds after posting) are never sensed, so a throttled account keeps running at `normal` and digs itself deeper.

Two secondary gaps compound this: write operations over an untrusted egress (China IP / datacenter range) are high-risk yet the cloud has zero egress visibility; and the per-action min-interval cooldown plus per-session search counters are in-memory only, so a restart zeroes them and lets the first batch burst past pacing.

## Decisions

- **Min semantics, so the ramp cannot architect-around the risk backoff.** Effective quota = `min(ageQuota(created_at), riskScaledQuota)`. Using `min` (not "cold-start replaces risk-scaled") guarantees that a young + `warned`/`restricted` account is bounded by whichever limit is lower, so age ramp and risk backoff stack. This is the decisive choice: any other combinator could let the newly-wired cold-start path silently relax an existing risk backoff, which is a self-harm regression the red lines forbid.
- **Aggressive backoff only feeds the existing `applySignal` input; it does not touch the transition table.** Facebook soft-block signals are routed through the same single-writer path the captcha overlay already uses. We add new *inputs* (recognized phrases, N consecutive post-check failures) but change neither `RISK_ACTIONS` nor the `normal → warned → restricted → frozen` transitions. The edge only recognizes and reports; the cloud `RiskController` remains the sole writer of the final state.
- **No-proxy egress is warn-only.** Per the approved v1 decision, an untrusted egress (China / datacenter / same subnet as the real machine) raises an operations alert but never sets a hard gate — it must not block, delay, or downgrade any action. A failed egress probe is reported as `unknown`, never silently assumed clean (honoring the never-silently-fake-success red line). A hard egress gate is explicitly deferred past v1.
- **Facebook gets a strictly more conservative cold-start curve than xiaohongshu.** Facebook throttles unattended write behavior harder, so D1–3 is browse + minimal likes only, comments open from D3, publish/group-join from D5. The xiaohongshu curve is left byte-for-byte unchanged so this change is zero-regression for the live platform.
- **Nurture-day is computed from `created_at` at decision time — no maturity field, no per-account maturity state machine.** Adding a persisted maturity column or a second state machine would be over-engineering (YAGNI): the ramp is a pure function of `created_at` and the current date, and reusing `ColdStartPlanner` keeps the surface tiny and reversible via an env knob.
- **Post-restart quiet period protects only the in-memory pacing state.** Daily quotas are already persisted in PostgreSQL and replayed on restart, so they are untouched. The quiet period exists solely to stop the in-memory min-interval cooldown / search-counter reset from letting the first post-restart batch burst.

## Open Questions

- **N for "consecutive post-check failures → systemic throttling".** What value of N balances fast backoff against transient-failure noise (e.g. 3 vs 5), and should N differ per action class (comment vs like vs publish)? Tune during ol observation.
- **Egress risk-feature source.** Where does the mainland-China / datacenter / same-subnet range table come from (bundled static ranges vs a maintained list vs an external lookup), and how often is it refreshed? v1 can ship a conservative static table; the maintenance path is deferred.
