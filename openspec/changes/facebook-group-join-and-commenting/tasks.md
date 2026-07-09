## 1. Preconditions

- [ ] 1.1 Ground on `origin/main`: `facebook-scheduled-comment`, `generalize-contact-info` (contact-info verbatim injection), `feed-hot-lead-auto-group-comment` (human-reviewed lead-gen lane), and `facebook-browser-environment` are archived + deployed dev. Do NOT re-implement them.
- [ ] 1.2 Confirm per-profile proxy/egress is an OPERATIONAL precondition configured manually in the AdsPower environment config, not built here.
- [ ] 1.3 Open `aidcp-console` same-name worktree only when the group-target management page (Phase 0) is implemented.

## 2. Cloud — data model + assignment (Phase 0)

- [ ] 2.1 Add `FacebookGroupTargetStore` (`facebook_group_target`: `group_url` PK, `group_name`, `join_gating IN unknown|instant|gated`, `priority`, `enabled`, `import_batch`; self-create + migration). Bulk import dedups on canonical URL; per-group enable/kill.
- [ ] 2.2 Add `FacebookGroupMembershipStore` (`facebook_group_membership`: junction + coverage columns; `UNIQUE(group_url)` one-group-one-account lock; indexes on `(account_id,status)`, `(status)`, `(account_id,status,last_commented_at)`).
- [ ] 2.3 Add `facebook_group_join_audit` append-only store (clone the comment audit store; best-effort never-throws).
- [ ] 2.4 Lazy-claim: atomic `INSERT … SELECT … ON CONFLICT (group_url) DO NOTHING RETURNING` claiming the next `unknown|instant`, `enabled` target with no membership row. Orphan reclaimer (MVP): release `assigned`/`joining` rows idle past a TTL back to the pool.
- [ ] 2.5 Panel API: import / list-with-status / per-account progress / per-group enable / assignment view. Register FB-account routes before the wildcard `GET /api/accounts/:id`.

## 3. Cloud — join rate-limit action (Phase 0, hotspot·serialize)

- [ ] 3.1 Add `join_group` to `RISK_ACTIONS` + all three tiers of daily quotas + minute/hour burst caps (typecheck-enforced coupled edit).
- [ ] 3.2 `risk_counters` CHECK constraint + idempotent DROP/ADD migration (mirror the `comment_like` retrofit) so `join_group` is countable.
- [ ] 3.3 Add `join_group` to the `interaction.occurred` action union so verified joins auto-record; join counts only after a judgment-confirmed join.
- [ ] 3.4 Ensure join and comment for one account run on the SAME scheduler instance's SAME action array (shared per-account single-flight); write out and check the worst-case aggregate daily action count.
- [ ] 3.5 (Optional) Add `joins` to the per-session budget only if joins batch within one browser session (open decision D-单场).

## 4. Cloud — join-gate judgment role (Phase 1)

- [ ] 4.1 Declare the join-gate judgment role name in the role-name enum (hotspot·serialize) and register it in the role catalog (`browse_judge`, `llmKind:'text'`) for model config.
- [ ] 4.2 Implement it as a command-式 role (plain class + imperative `evaluate()`, constructed by the join scheduler; NOT dispatcher-registered), template shape = the follow-decision role. Pre-click verdict {instant_join|gated_skip|already_member|ambiguous_skip}; post-click verdict {joined|pending/gated|failed}; deterministic short-circuits; fail-closed on uncertainty.
- [ ] 4.3 Record input observation + verdict + reason to audit for the console "why joined/skipped" readout and the shadow accuracy measurement.

## 5. Cloud — join scheduler + coverage scheduler (Phase 1–3)

- [ ] 5.1 Add a `join` action slot to the existing content scheduler (per-account offset + weekly mask + single-flight + risk gate): one atomic join per slot; drives lazy-claim → observe → judge → `group.join` → record honest outcome to the ledger + audit. Kill switch `AIDCP_FB_GROUP_JOIN_AUTO` (default off); shadow `AIDCP_FB_GROUP_JOIN_SHADOW`.
- [ ] 5.2 State machine writes: `joined` (write `joined_at`, judgment-confirmed only) / `gated`/`pending` (flip target `join_gating='gated'`, fleet-wide exclude, no dangling request) / account-transient checkpoint/login → pause account join loop / retryable failures with attempt cap + backoff.
- [ ] 5.3 Coverage loop: per-account daily slice over `status='joined'` groups, oldest-`last_commented_at`-first past a per-group cooldown floor + small random window; join-to-first-comment warmup interval; writes back `last_commented_at`/`comments_total` on verified comment only.
- [ ] 5.4 Per-account comment-source gate (allowlist): coverage-enabled accounts source containers from the joined-group ledger; keywords still from config; fail-closed (no keywords or no joined groups → no-op). NOT a global boolean.
- [ ] 5.5 Reverse-drift protection: `joined→left` demotion requires N repeated confirmations, never a single whole-page signal; deleted/inaccessible group (nav_error on joined) is demotable.

## 6. Cloud — contact-comment lane (Phase 3)

- [ ] 6.1 Route mode-(b) contact comments through the existing human-reviewed lane (`gated-auto-comment` + `compose-approve` verbatim contact injection + Feishu approval), extended with a Facebook submit closure. Fail-closed if `accounts.contact_info` missing.
- [ ] 6.2 Add a Facebook validator carve-out that exempts ONLY the injected contact span (mirror how xhs excludes contact from overlap/length gates); the composed body still passes all hard validators. Do NOT weaken the unattended-path contact-forbidden invariant.

## 7. Edge — join action + protocol (Phase 1)

- [ ] 7.1 Add `FacebookJoinExecutor.joinGroup(url)` (CDP IIFE, jsdom-stub testable): URL guard → navigate+settle → fresh overlay probe (login/captcha fail-closed) → scoped group-header observation report → click Join once only when instructed → post-click observation report → dismiss optional survey / do NOT submit required questionnaire. Honest outcomes; `ok=true` only on member-now.
- [ ] 7.2 FB driver gains a distinct `join` capability (never `browse`); route `group.join` through the Facebook command handler (`switch(env.type)`), never a second `onBrowseCommand` call.
- [ ] 7.3 Protocol four-point sync for `group.join` (two `protocol.ts` verbatim + `docs/protocol.md` count/table) + edge onMessage active-command whitelist entry (typecheck-invisible silent-drop point); regression assert the command reaches the handler.
- [ ] 7.4 Checkpoint/login receipts wire to pausing the account join loop directly (not the un-wired risk state machine).

## 8. Console — group management (Phase 0)

- [ ] 8.1 Add a "群组" management page: bulk import (paste/dedup), status list (unassigned/assigned/joined/gated-skip/failed), per-account progress, per-group enable, shadow badge. Keep status `Record<Union>` exhaustive with a gray fallback (enum-drift white-screen guard).
- [ ] 8.2 "安全" quota page gains the `join_group` action column (mirror enum + label; typecheck won't catch drift).

## 9. Rollout + verification

- [ ] 9.1 Phase 0 on dev: import 2000–5000 targets, verify dedup + atomic lazy-claim + join rate-limit config surfaces in "安全" page. No join/comment.
- [ ] 9.2 Phase 1 shadow: run the judgment role over hundreds of real targets; measure join-gate classification accuracy against a numeric threshold (with denominator) — this gates Phase 2.
- [ ] 9.3 Phase 2 single disposable account, `join_group` cap 1–3/day: verify honest-receipt → ledger closed loop, no fake ok, no dangling pending, learned gating excludes fleet.
- [ ] 9.4 Phase 3 single account: auto contextual coverage (per-account gate), then the human-reviewed contact lane on selected groups.
- [ ] 9.5 Phase 4 fleet: raise caps gradually; observe partition balance, shared-budget clamp, cross-account jitter. Register real-machine items in `docs/real-machine-acceptance-backlog.md`.
- [ ] 9.6 Regression discipline: `npm run test:acceptance` → full `npm test` → `npm run typecheck` in edge and cloud after protocol/risk changes; AC-PROTO-*/AC-RISK-* must pass.
