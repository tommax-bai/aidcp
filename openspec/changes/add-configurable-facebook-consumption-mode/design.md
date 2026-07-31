## Context

Cloud currently owns three related but differently shaped facts:

- environment slow-start state in `client_environments`;
- an environment-keyed rule-mode enable flag, while rule cadence remains compiled as `5 views / 2 rounds`;
- account-level content and group-join schedules used by the persona-driven scheduler.

Rule progress is durable by account and `execution_target`, and Edge already exposes the atomic Native operations needed by the requested flow. However, the existing rule batch's `joinFirst` path intentionally joins and comments in the same group, while the requested consumption flow must join without commenting and later comment in any strictly eligible joined group. The ordinary group coverage selector also receives its 24-hour join warmup and 72-hour re-comment cooldown from deployment environment variables, not from a product configuration authority.

The design must preserve these invariants:

- Cloud plans, selects targets, persists progress, and owns primary pacing; Edge only executes scoped atomic actions.
- `RiskController` remains the sole writer of final account risk state.
- irreversible writes count only from truthful platform outcomes; ambiguous dispatch is never promoted to success or blindly retried.
- DEV and OL runtime work is separated by `execution_target`.
- mode and policy configuration is environment-scoped, while runtime facts remain account-scoped.
- the existing in-progress `environment-level-rule-mode-and-approval` migration remains the source of environment binding and approval-policy behavior; this change must not regress its ownership checks or approval work.

## Goals / Non-Goals

**Goals:**

- Provide one backend authority for the effective Facebook operation mode and typed rule/consumption cadence.
- Add a restart-safe consumption state machine driven by confirmed new outcomes.
- Make join-to-first-comment waiting product-configurable without conflating it with same-group re-comment cooldown.
- Prevent persona time scheduling from initiating group joins in slow-start, rule, or consumption mode.
- Reuse current Native browse/like/join/first-commentable-post/comment primitives.
- Expose server truth, policy revisions, blockers, and bounds in Console.

**Non-Goals:**

- A generic operator-authored action graph.
- Changing daily risk quotas, approval rules, comment generation, or the semantics of rule mode's immediate pinned join-comment exception.
- Changing the Edge protocol, implementing policy counters on Edge, or producing an Edge installer.
- Deploying to OL.
- Treating an activity row, task completion, click, `already_liked`, or `already_member` as a newly produced platform outcome.

## Decisions

### 1. Resolve one effective mode in Cloud

Cloud exposes `persona | slow_start | rule | consumption` as the effective mode. Internally, the durable operation policy stores a base mode of `persona | rule | consumption`; the existing environment slow-start lifecycle remains authoritative for whether the effective mode is `slow_start`.

Resolution order is:

1. binding/platform/config unknown or conflicting → `blocked`, with no automatic mode action;
2. authoritative slow-start state `active` → `slow_start`;
3. otherwise → the stored base mode.

An unbound environment has no effective runtime mode, so its projection keeps
`effectiveMode=null`. That absence of an execution object MUST NOT erase the
environment-level selection: a persisted active slow-start anchor is still
projected as `slowStart.state=active`, and clients reconstruct the configured
choice from the slow-start lifecycle before falling back to `baseMode`.

Selecting `slow_start` through the unified backend API activates the existing slow-start lifecycle and sets the resumable base mode to `persona`. Selecting another mode disables active slow start and updates the base mode in one service transaction. Existing environments that already have both active slow start and rule enabled retain rule as their resumable base during migration, so current post-graduation behavior is not silently lost.

Only effective `persona` admits the independent time-scheduled group-join trigger. Rule and consumption orchestration may call the same lower-level join executor, but never the time scheduler or its weekly/daily cadence. This is an admission decision made immediately before claiming work, not just a UI convention.

The persona/content active-week projection is not a mode selector. It MUST NOT demote a configured `rule` or `consumption` mode back to `persona` outside a persona schedule window. Slow start keeps absolute precedence; otherwise the operation policy remains the effective mode authority.

Alternative considered: store all four modes in a new table and duplicate slow-start state. Rejected because it creates two authorities for a lifecycle that already has active/graduated state and timing.

### 2. Use a typed, revisioned environment policy

Add `facebook_operation_policy`, keyed by `env_key`, containing:

- `base_mode`;
- rule parameters: `views_per_round`, `rounds_per_join_comment`;
- consumption parameters: `views_per_like`, `confirmed_likes_per_join`, `confirmed_joins_per_comment`;
- monotonically increasing `policy_revision`;
- audit metadata.

All parameter sets remain stored when another mode is selected so switching back does not erase operator choices. Cloud validates strict integer bounds and returns those bounds and defaults in every read projection; Console does not duplicate them as independent constants.

Writes require the complete typed payload plus `expectedRevision`. Unknown fields, stale revisions, invalid bounds, unsupported platforms, missing ownership, and binding conflicts fail before mutation. The configuration row and an append-only audit row containing before/after snapshots, actor, request ID, reason, and timestamp are written atomically. The response is a database readback, not the request echo.

The customer-facing environment rule-toggle endpoint remains as an explicitly bounded compatibility adapter:

- enable maps to base `rule` with the stored rule parameters or server defaults;
- disable maps to `persona` only if the current base mode is `rule`;
- it cannot replace `consumption` or active `slow_start`;
- it accepts an owned `envKey`, never an account selector.

Alternative considered: add three numbers to `facebook_rule_mode_config` and a separate consumption table. Rejected because mode switches would require non-atomic coordination between mutually exclusive booleans and would leave scheduled-join admission without one authority.

The new Edge client does not extend that Boolean compatibility adapter. It uses a customer-scoped unified policy route with `{ expectedRevision, mode }`, receives the committed full mode projection, and never sends cadence numbers. The legacy slow-start and rule routes remain only for already released clients.

### 3. Freeze cadence interpretation by policy revision

Runtime ownership is `account_id + execution_target + policy_revision`. A rule batch or consumption action stores the immutable parameter snapshot that created it.

When a policy changes:

- no new work is admitted under the prior revision;
- not-started prior-revision work is cancelled with a named policy-change reason;
- a write already dispatched to the platform may settle truthfully under its original snapshot;
- counters are not copied or arithmetically reinterpreted;
- the new revision starts from zero and new content dedupe facts.

Rule definition identity becomes a stable algorithm identifier instead of encoding `5/2`; policy revision carries the configurable values. Historical definition/version rows remain readable for audit and are not rewritten.

Alternative considered: immediately apply a new threshold to accumulated counters. Rejected because changing `5` to `3` could synthesize actions that were never earned under either policy.

### 4. Model consumption as durable obligations plus one-shot attempts

Consumption state uses three layers:

- `facebook_consumption_progress`: counters and next sequence for the active account/target/revision;
- `facebook_consumption_view_fact`: confirmed content identities used for dedupe;
- `facebook_consumption_action`: immutable action obligation/attempt rows for `like`, `join`, and `comment`, including snapshot, idempotency key, target, dispatch phase, result, and timestamps.

State transitions occur in database transactions with compare-and-swap ownership:

1. Each confirmed unique view increments `views_since_like`. Reaching `viewsPerLike` subtracts that threshold and creates exactly one like obligation for the triggering content.
2. A platform-confirmed **new** like increments `confirmed_new_likes_since_join`. Reaching `confirmedLikesPerJoin` subtracts that threshold and creates exactly one join obligation.
3. A platform-confirmed **new** membership increments `confirmed_new_joins_since_comment`. Reaching `confirmedJoinsPerComment` subtracts that threshold and creates exactly one comment obligation.

An obligation may wait for a target or an admission gate without pretending an attempt occurred. Once an irreversible platform action is dispatched, that obligation is never blindly dispatched again. A correlated late confirmation may settle the same action exactly once.

Terminal failures do not recreate threshold debt: the triggering upstream credit was consumed when the obligation was created, and future outcomes accumulate toward a new obligation. This prevents repeated attempts from one threshold and keeps the configured cadence literal.

Result classification is explicit:

| Result | New-like counter | New-join counter | Successful comment |
| --- | ---: | ---: | ---: |
| confirmed newly liked | +1 | — | — |
| `already_liked` | 0 | — | — |
| confirmed newly joined | — | +1 | — |
| `already_member` | — | 0 | — |
| pending / gated / not started | 0 | 0 | 0 |
| ambiguous dispatched write | 0 | 0 | 0 |
| failed | 0 | 0 | 0 |
| platform-confirmed comment readback | — | — | 1 |

Ambiguous writes still consume the existing risk/quota and dedupe facts required by their action contracts, because the platform may have accepted the write. They do not advance consumption success counters and are not automatically retried.

### 5. Separate join from historical-group comment

The consumption join action calls the join-only executor and never supplies `joinFirst`. Its result must distinguish `joined` from `already_member`; only `joined` advances the new-join counter.

At the comment threshold, Cloud creates a comment obligation and selects a group only when one is strictly eligible:

```text
membership.status = 'joined'
AND membership.joined_at <= now - joinToFirstCommentHours
AND per-group re-comment cooldown has elapsed
AND account and execution scope match
```

There is no additional exclusion for the two joins that triggered the obligation. Their eligibility follows solely from `joined_at` and the current join-to-first-comment setting. With the default 24-hour wait they are naturally ineligible; after the configured wait they may be selected.

The selector forbids the ordinary relaxed fallback. If no group is eligible, the obligation remains `waiting_target` and is re-evaluated later without a platform write or success count. Once selected, it stores the exact group identity and explicitly requests `first_commentable_group_post`; account keywords cannot redirect it into group search. “First” means the first commentable content encountered from the top of the current discussion stream, including a pinned item if it is the first eligible item.

The selected item then uses the ordinary comment composition, approval, risk, target rebinding, Native CDP actuation, and platform readback pipeline. Consumption does not inject contact details unless an existing explicit approval/template source independently requires them.

### 6. Make join-to-first-comment timing a separate backend policy

Add `facebook_group_comment_policy`, keyed by the local `execution_target`, with:

- `join_to_first_comment_hours`, default `24`, accepted range `1..168`;
- `revision` and audit metadata.

This is deliberately separate from the existing per-group re-comment cooldown (default 72 hours). API and Console labels use “入群后首次评论等待” and “同群再次评论冷却” so operators cannot mistake one for the other.

Reads use database truth when present. During migration only, absence falls back to the legacy `AIDCP_FB_GROUP_COVERAGE_WARMUP_HOURS`, then the compiled default, and reports `source=db|legacy_env|default`. The compatibility fallback is removed only in a later explicit cleanup after every target has a persisted row.

Eligibility reads the current timing policy just before target selection. Lowering the setting can make a previously waiting obligation eligible; increasing it cannot be bypassed by an older mode-policy snapshot.

Alternative considered: snapshot the 24-hour value into each consumption policy. Rejected because the same safety rule also governs persona/ordinary coverage and must have one current authority.

### 7. Expose one write authority and truthful projections

Panel APIs:

```text
GET /api/environments/:envKey/facebook-operation-policy
PUT /api/environments/:envKey/facebook-operation-policy
GET /api/facebook/groups/comment-policy
PUT /api/facebook/groups/comment-policy
```

Customer-auth APIs:

```text
GET /environments/:envKey/facebook-operation-policy
PUT /environments/:envKey/facebook-operation-policy
POST /environment-provisioning/complete
```

The customer GET returns only the owned environment key, configured/effective mode, revision, slow-start state and named blocker. The PUT accepts only `expectedRevision` plus one of `persona | slow_start | rule | consumption`; Cloud preserves the stored cadence values and performs the same audited transaction as Panel. A stale revision returns the current projection. Provisioning accepts one mutually exclusive `facebookOperationMode` and writes the environment plus initial policy snapshot atomically; mixing it with legacy slow-start/rule Boolean intents is rejected.

The operation-policy response includes configured base mode, effective mode, slow-start projection, typed parameters, bounds/defaults, policy revision, binding state, and blocker. The content-schedule catalog adds read-only consumption/rule progress and current effective mode but does not accept policy writes.

Console:

- `/environments` owns the mode and cadence editor;
- `/facebook-groups` owns the join-to-first-comment policy editor;
- `/content-schedule` shows runtime progress and blockers only.

All editors disable duplicate saves, send `expectedRevision`, refetch after success, preserve the form on failure, and visibly report conflicts or unknown server state. A stale GET is not shown as a successful save.

Edge:

- the creation dialog orders `普通 → 冷启动 → 规则 → 消费`;
- the existing-environment operation area shows the same four mutually exclusive choices, with consumption visually after cold-start and rule;
- UI truth comes from the customer GET and successful write-after-read response; pending, conflict and unavailable states are never applied optimistically;
- effective priority is Cloud-owned: active slow start wins, then the selected base policy. Rule and consumption cannot be simultaneously configured, so Edge does not invent Boolean precedence or merge multiple toggles;
- cadence numbers, bounds, counters and action debt remain absent from the Edge request and local persistence.

### 8. Keep Edge execution atomic and policy-thin

Cloud reuses existing Edge operations:

```text
browse confirmation
→ like current scoped content
→ join exact assigned group
→ note.open(selection='first_commentable_group_post', container=groupUrl)
→ interaction.comment(exact rebound target)
```

The policy snapshot parameters and counters are never sent to or interpreted by Edge. The desktop renderer may display the Cloud mode/revision projection, but it is not an execution authority. Existing Edge receipt phases remain the source for confirmed versus ambiguous classification. No protocol version change is needed unless implementation discovery proves an existing receipt cannot distinguish a newly produced like/join from an idempotent already-state; in that case work stops and the protocol delta is added before code changes.

### 9. Observe every admission and transition

Structured events include account, environment, execution target, mode, policy revision, action sequence/type, prior/new state, target identity where available, outcome class, and blocker. Metrics distinguish:

- confirmed unique views;
- new confirmed likes versus `already_liked`;
- new confirmed joins versus `already_member`;
- waiting-target obligations;
- dispatched ambiguous writes;
- confirmed comments;
- scheduler skips by effective mode.

No metric or Console label collapses lease release, dispatch, or ambiguous receipt into platform success.

## Risks / Trade-offs

- **[Concurrent policy edits or mode switches create mixed work]** → Require `expectedRevision`, freeze action snapshots, cancel only not-started old work, and let dispatched work settle truthfully.
- **[A join or comment dispatch is accepted but verification is ambiguous]** → Consume existing risk/dedupe accounting, do not advance success counters, and do not auto-retry; allow only correlated late settlement.
- **[No group is eligible when the comment threshold is reached]** → Keep one durable `waiting_target` obligation and re-evaluate strict eligibility; never relax the warmup/cooldown.
- **[Legacy rule and slow-start rows conflict during migration]** → Preserve slow-start precedence, keep the rule choice as resumable base, emit a migration/audit marker, and expose effective versus configured mode.
- **[DEV configuration affects OL in the shared database]** → Scope the group timing row and all runtime work by `execution_target`; environment operation policy follows the existing shared business-config authority and runtime still filters its local target.
- **[Console and Cloud deploy out of order]** → Cloud accepts the current rule-toggle compatibility API, while the new Console feature is hidden until the new read contract and bounds are present.
- **[Large scheduler integration surface]** → Keep action execution behind existing join/comment executors and add focused acceptance tests for mode admission and outcome classification before full suites.

## Migration Plan

1. Land additive Cloud migrations and stores:
   - seed operation-policy rows from environment rule config and slow-start projection;
   - preserve existing rule parameters as `5/2`;
   - default other environments to `persona`;
   - add target-scoped group-comment policy with legacy fallback;
   - add empty consumption runtime tables.
2. Deploy Cloud code that dual-reads existing rule configuration only when no new policy row exists, exposes the new APIs, and keeps the released rule-toggle adapter.
3. Switch rule admission/runtime writes to policy revision and add consumption orchestration behind `mode=consumption`; default migration never enables consumption.
4. Gate scheduled group joins on effective `persona` immediately before claim and dispatch.
5. Deploy Console editors and runtime projection, then persist the DEV group-comment policy and verify write-after-read.
6. Run real DEV verification only on explicitly selected test environments/accounts: mode switch truth, no scheduled join outside persona, one confirmed consumption transition, strict no-eligible-group behavior, and ambiguous outcome non-counting. Do not perform additional platform writes beyond the approved probe.

Rollback disables new admissions first, restores rule reads through the retained legacy row, and leaves additive policy/runtime/audit rows intact. Dispatched actions are allowed to settle; no rollback rewrites confirmed or ambiguous historical facts.

## Open Questions

None. Product decisions are fixed for this change: confirmed-new outcome counting, no scheduled group joining outside persona mode, timestamp-only group eligibility, and current first-commentable-item semantics.
