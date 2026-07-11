## Why

After `facebook-scheduled-comment` shipped unattended commenting on operator-configured containers, the operator wants a self-sustaining Facebook group presence: bulk-configure 2000–5000 target public groups, have a fleet of accounts (dozens) gradually join the ones that allow instant public join, and then cover each account's own joined groups with scheduled comments. This is higher risk than the existing path because bulk joining is a strong platform spam signal, and because the "did this group actually let me in" decision is ambiguous and irreversible (a mis-click on an approval-gated group leaves a permanent pending request). It must therefore be default-off, fail-closed, shadow-first, rate-limited through the existing safety-quota system, and gated by a cloud judgment role whose accuracy is validated in shadow before any real join.

## What Changes

- Add a Facebook group-target catalog (operator bulk-imports group URLs in the console) and a per-account membership ledger. Accounts lazily claim unjoined targets under an atomic one-group-one-account lock; an orphan/TTL reclaimer releases targets held by offline accounts.
- Add a NEW edge `join_group` atomic action (navigate → observe → click once → observe) that only reports what it sees, plus a NEW cloud judgment role that classifies the observation as instant-join / approval-gated / already-member / ambiguous. The edge MUST NOT decide the join gate from whole-page text; the cloud role decides, fail-closed (uncertain → skip, never click a gated group).
- Make Facebook group join a first-class rate-limited action alongside browse/like/collect/comment: it flows through the existing minute/hour/day sliding-window quotas + three tiers + risk-state scaling, and (optionally) the per-session budget. A new account is throttled by selecting the conservative tier, not a bespoke warmup function.
- Add a per-account daily comment-coverage loop that drives the EXISTING Facebook comment pipeline over an account's own joined groups (oldest-covered-first, per-group cooldown floor). The comment-source switch (operator-config → joined-group ledger) is per-account (allowlist), never a global boolean.
- Support two content modes: (a) auto-generated contextual comments run unattended on the existing hard-validator path and MUST NOT carry contact info; (b) contact/lead-gen comments route through the EXISTING human-reviewed lane (contact-info injection + Feishu approval), never the unattended path, with a validator carve-out for the injected contact span and fail-closed when contact is missing.
- Add shadow/dry-run for both loops, honest stop/outcome codes throughout, explicit checkpoint/login → pause-account wiring (not the un-wired risk state machine), and a join-to-first-comment warmup interval.

## Capabilities

### New Capabilities

- `facebook-group-membership`: Group-target catalog + bulk import, lazy-claim assignment with atomic one-group-one-account lock and orphan reclaim, the `join_group` edge action and its honest outcomes, the cloud join-gate judgment role and its fail-closed classification, the membership ledger + per-target state machine, group-level `join_gating` learning (learn once, exclude fleet-wide), default-off + shadow mode, and a distinct `join` capability string that MUST NOT reuse `browse`.
- `facebook-group-comment-coverage`: Per-account daily coverage scheduling over an account's joined groups (oldest-first LRU + per-group cooldown floor), the per-account comment-source gate, the two content modes (unattended auto vs human-reviewed contact) and their routing, join-to-first-comment warmup, reverse-drift protection for ledger demotion, low-membership graceful degrade, and shared per-account single-flight/activity budget with the join loop.

### Modified Capabilities

- `interaction-risk-gating`: Add Facebook group join as a first-class rate-limited action (minute/hour/day windows + tiers + risk-state scaling), counted only after a verified join, sharing per-account single-flight and activity budget with commenting.
- `facebook-scheduled-comment`: Allow the per-account joined-group ledger as an additional container source under a per-account gate, without changing the unattended compose/validate/verify mechanics or weakening the contact-forbidden invariant on the unattended path.

## Impact

- Affected repos: `aidcp-cloud` (catalog/ledger stores, assignment + reclaimer, judgment role, coverage scheduler, risk-action wiring, protocol command dispatch), `aidcp-edge` (`join_group` action, structured observation reporting, `join` capability, onMessage whitelist), `aidcp-console` (group-target management page, "安全" quota page gains the join action column).
- Cloud areas: three new tables (`facebook_group_target`, `facebook_group_membership`, `facebook_group_join_audit`); `RISK_ACTIONS` + quota tiers + `risk_counters` CHECK + migration for `join_group`; a new command-式 judgment role in the role catalog; a per-account coverage scheduler slot on the existing content scheduler instance; protocol four-point sync for `group.join`.
- Edge areas: Facebook `join_group` executor (navigate/observe/click/observe, jsdom-stub testable), scoped group-header observation reporting, `join` capability, `group.join` onMessage active-command whitelist entry.
- Operational impact: starts disabled (`AIDCP_FB_GROUP_JOIN_AUTO=false`); per-profile proxy/egress is configured MANUALLY in the AdsPower environment config and is an operational precondition, NOT built by this change. Rollout is shadow-first with a numeric join-gate accuracy gate before any real join.
- Scale-out boundary: the design is sized for dozens of accounts × thousands of groups (lazy-claim, no consistent-hashing). Contact comments stay human-reviewed and therefore low-volume/selective, not bulk daily coverage. The residual "many accounts' contact strings appearing together at high frequency is a behavioral fingerprint" risk (logged by `feed-hot-lead-auto-group-comment`) is mitigated only by small caps + jitter + human review.
