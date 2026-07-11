# Design: Facebook public-group bulk-join + per-account group-comment coverage

> Two cloud loops sharing one membership ledger; edge only performs atomic actions and reports what it sees. Default-off, shadow-first. Grounded on `origin/main` (contact-info, hot-lead, FB scheduled-comment already merged + deployed dev).

## 1. Architecture

Two independent-tempo cloud loops connected by one ledger:

- **Acquisition loop (join)**: assign 2000–5000 target groups across accounts, each account joins a few *public instant-join* groups per day under the rate limit. Cloud selects/limits/judges; edge navigates, clicks Join once, and reports the observed page state.
- **Activation loop (comment coverage)**: each account each day covers a slice of ITS joined groups, one contextual comment per covered group, reusing the existing Facebook comment pipeline; comment source = the joined-group ledger, not operator config.
- **Membership ledger** is the only coupling point: the join loop writes it, the coverage loop reads it and writes back coverage progress.

Cloud/edge split (边轻云重): all planning, assignment, rate-limiting, coverage scheduling, the join-gate judgment, dedup, and audit are in cloud (single-writer). Edge does only: navigate / click Join / dismiss modal / submit comment, plus honest structured observation reporting. Edge never concludes whether a join succeeded — it reports observations; the cloud judgment role and the server-confirmed comment verifier conclude.

Red line: the ledger's `joined_at` is written only on a real `joined` receipt confirmed by the judgment role. `count||1` and fake `ok` are forbidden — one fake success poisons both the membership ledger and the rate-limit budget.

## 2. Data model (self-create in store `init()`, no migrator)

- **`facebook_group_target`** — shared catalog (~5000 rows). `group_url PK`, `group_name`, `join_gating IN ('unknown','instant','gated')` (learned once per group, fleet-wide exclusion), `priority` (v1 all 0), `enabled`, `import_batch`. Named `join_gating` NOT `publicness`, because "content is public" and "click-Join makes you a member now" are orthogonal; the field must key on join behavior, not visibility.
- **`facebook_group_membership`** — ledger + assignment + coverage (the only junction). `status IN ('assigned','joining','joined','pending','gated','no_button','checkpoint','failed','left')`, `assigned_at` (orphan-reclaim TTL basis), `joined_at` (only on real joined), `last_attempt_at`, `attempts`, `last_reason`, `last_commented_at` (coverage cursor), `cooldown_until`, `comments_total`. `UNIQUE(group_url)` makes one-group-one-account a DB hard lock so lazy-claim `INSERT … ON CONFLICT DO NOTHING` is atomic. Overlap is a clean seam (drop the constraint + add `max_members`).
- **`facebook_group_join_audit`** — append-only attempt log (clone of the comment audit store, best-effort never-throws). Readable audit + shadow records; join rate counting itself flows through `risk_counters` once join is a rate-limited action.
- Reused unchanged: `facebook_comment_audit`; `accounts.contact_info` (per-account verbatim contact string, already platform-agnostic); `risk_counters` (join joins this after §5).

## 3. Acquisition loop

- **Assignment = lazy-claim** (work-stealing), no static sharding at dozens×thousands scale. An account with join budget and no pending `assigned` row atomically claims the next available `unknown|instant` target via `INSERT … SELECT … ON CONFLICT (group_url) DO NOTHING RETURNING`. Idempotent + race-safe by construction; free rebalance (paused/offline accounts stop claiming). **Orphan reclaimer is MVP** (not optional): an `assigned`/`joining` row idle past a TTL is released, else an offline account's claim locks the target fleet-wide.
- **Edge `join_group` action** (mirrors the comment executor; CDP IIFE, jsdom-stub testable): URL guard → navigate+settle → fresh overlay probe (login/captcha fail-closed) → collect scoped group-header observation and report → (only if the judgment role returns instant-join) click Join once → collect post-click observation and report → dismiss an optional post-join survey modal / do NOT submit a required questionnaire. Honest outcomes: `joined | already_member | pending | questionnaire_required | no_button | not_facebook | login_required | blocked_by_captcha | nav_error | join_failed`. Receipt reuses `action.completed{action:'join_group'}`; `ok=true` only on a real join.
- **Join-gate judgment role** (see §4) decides instant-join vs gated at two decision points; fail-closed: uncertain → skip, never click.
- **State machine**: group-level terminal (`pending`/`gated`/`no_button`) also flips `join_gating='gated'` → fleet-wide exclusion; account-transient (checkpoint/login/captcha) pauses that account's join loop, leaves the group retryable; retryable failures back off with an attempt cap.
- **Trigger**: reuse the existing content scheduler (per-minute tick + per-account deterministic offset + weekly-active mask + single-flight + risk gate), adding a `join` action slot doing one atomic join per slot. Not a second cron.

## 4. Join-gate judgment role

The core of the operator's "add a judgment role" decision, and the fix for the review's #1 risk (the join-gate detector was brittle edge regex). Access / click / dismiss are atomic edge actions; the JUDGMENT (public-instant vs approval-gated vs already-member; did the click make me a member) is a cloud role.

- Input = the edge's structured observation (group-header main CTA text/aria, presence+content of any modal, membership signals, optional screenshot). Output = a JSON verdict at two points: pre-click (`instant_join | gated_skip | already_member | ambiguous_skip`) and post-click (`joined | pending/gated | failed`).
- Deterministic gates short-circuit obvious cases (logged-out, captcha, clearly-member); only genuine ambiguity reaches the model. Fail-closed throughout.
- Wired as a **command-式 role** (like the `/comment` roles): declared in the role-name enum + registered in the role catalog for model config, constructed by the join scheduler, NOT dispatcher-runtime-registered. Template shape: the follow-decision role (structured observation → deterministic gate + LLM verdict). This minimizes hotspot surface.
- **Shadow accuracy gate**: Phase 1 runs the role over hundreds of real targets in shadow; a numeric classification-accuracy threshold (with denominator) must be met before any real join, because a mis-classification is irreversible (a permanent pending request). Cost is negligible because joins are rate-limited to single digits/day.
- Observability: the role records input observation + verdict + reason, so the console can show why each join happened/was skipped — more auditable than an edge result code.

## 5. Rate-limit integration (operator adjustment 1)

Facebook group join becomes a first-class rate-limited action, NOT a bespoke counter. Add `join_group` to the action union → it inherits the existing minute/hour/day sliding windows, the three tiers, and risk-state scaling (warned → all actions slow; restricted/frozen → join stops). A young account is throttled by selecting the conservative tier; no bespoke age-ramp function (which the review found buggy). The "安全" quota console page gains a join column automatically. Per-session ("单场") applies only if joins batch within one browser session — an open decision (default: one join per scheduled slot, so per-session is 1).

Coupled edit set (typecheck-enforced, serialize the migration): action union + three-tier quotas + `risk_counters` CHECK + migration + the `interaction.occurred` action union + console enum/label. The risk **state machine** keys on status, not action — it does NOT change.

**Shared budget with commenting**: join and comment on the same account compete for the same daily activity tolerance. Join must be added to the SAME scheduler instance's SAME action array so it inherits the per-account single-flight (edge is physically single-slot). The worst-case aggregate daily action count (join_cap + comment_cap) must be written out and checked against FB tolerance; the shared risk-state scaling brakes both.

## 6. Activation loop (comment coverage) + two content modes

- **Coverage** = oldest-covered-first over the account's joined groups, past a per-group cooldown floor, with a small random window to break lock-step ordering. Guarantees eventual coverage (~`ceil(M/K)` days) without hammering the same groups.
- **Comment-source gate is per-account (allowlist), never a global boolean** — switching all FB accounts' comment source at once contradicts single-account staged rollout.
- **Mode (a) auto contextual**: runs unattended on the existing hard-validator path; MUST NOT contain contact info (the existing FB validators reject contact/URLs/spam). This is the scalable daily-coverage mode.
- **Mode (b) contact/lead-gen**: routes through the EXISTING human-reviewed lane (contact-info verbatim injection + Feishu approval, reusing `gated-auto-comment` + `compose-approve`), extended with an FB submit closure and a validator carve-out for the injected contact span. Fail-closed if the account's contact string is missing. Because it needs human approval it is selective/low-volume, not bulk daily coverage. Proxy/egress is a manual operational precondition for running the fleet.
- **Warmup**: a join-to-first-comment interval — an account does not comment in a group the same day it joined it.
- **Reverse-drift protection**: ledger demotion (`joined→left`) MUST NOT be driven by unreliable whole-page membership text; require N consecutive confirmations, aligning with the anti-pollution stage/promote discipline. A deleted group (nav_error on a joined row) must also be demotable.
- **Low-membership graceful degrade**: 0 members → clean no-op; very few members → the per-group cooldown floor dominates the daily cap so a warming account self-limits.

## 7. Protocol + safety

- New `group.join` cloud→edge command: four-point sync (two `protocol.ts` + `docs/protocol.md`; command-bridge optional because the FB path builds envelopes directly) PLUS the edge onMessage active-command whitelist entry (the typecheck-invisible silent-drop point). FB driver gains a distinct `join` capability; never `browse`. Cloud addresses a specific account's edge via the existing `resolveConnection → pushToEdges(edgeId)` skeleton.
- Kill layers (all fail-closed): global env off → whole loop no-op; shadow on → judge+record, never click/submit; account `paused` → both loops skip; group `enabled=false` → excluded; risk state ≠ normal → both loops stop (join now inherits this).
- **Checkpoint/login → explicit pause**: because the risk state machine does not auto-transition on platform captcha (known gap), edge checkpoint/login receipts wire directly to pausing the account, not via the un-wired state machine.

## 8. Phased rollout (mirrors facebook-scheduled-comment)

0. Data + import + assignment + join rate-limit config; console group page. Risk 0 (no join/comment).
1. Join shadow: `join_group` + `group.join` + whitelist + judgment role, navigate+observe+judge+audit only, never click. Validate the judgment-role accuracy numeric gate.
2. Single-account real join, cap 1–3/day; verify honest-receipt → ledger closed loop, no fake ok, no dangling pending.
3. Single-account real coverage (per-account gate), auto contextual mode; then the human-reviewed contact lane on selected high-value groups.
4. Fleet scale-out; raise caps gradually; observe partition balance and shared-budget clamp.

Each phase is independently reversible (env off) and validated on dev first; production requires explicit operator request + release branch.

## 9. Open decisions

- Account scale: dozens (confirmed) → lazy-claim suffices, no consistent-hashing.
- Comment goal: breadth coverage (auto) is the default bulk mode; contact comments are the selective human-reviewed lane.
- Per-session dimension for join: default one-join-per-slot (single-session cap trivially 1) vs batch-join session.
- One-group-one-account (default) vs overlap for high-value groups (clean seam).
