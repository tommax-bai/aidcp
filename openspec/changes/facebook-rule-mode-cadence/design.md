## Context

The current Facebook browse loop is a persona-driven event chain: Cloud evaluates visible cards against the bound Soul, opens a selected card, reads it, appraises optional interactions and sends an Edge atomic command only after risk admission. Weekly active windows decide when a browse session may run. Slow start is not a separate scheduler; it is an environment-scoped, authoritative projection that clamps `RiskController` quotas and exposes `off | active | graduated` plus diagnosable ineligible states.

The requested rule mode is a different source of intent. It does not ask “does this content match the persona?” It asks “has this Facebook account completed another batch of ten confirmed reads?” and then creates two bounded action attempts. Encoding that cadence in Soul text would make the count non-durable and let LLM output own scheduling. Encoding it in the hourly content scheduler would confuse a count trigger with a time-slot trigger and create a second authority over the browse loop.

Two active architectural facts shape the change:

- `facebook-join-contact-first-post` defines the single join-then-contact-comment path, including a pinned just-joined group and canonical first-post targeting, but its implementation tasks are not complete. This change depends on that path and must not duplicate it.
- `add-managed-automation-runtime` defines a future `Trigger Binding → TaskRun → StepRun → ExecutionAttempt` model, but it is not an implemented runtime. This change must be independently deliverable in the current Cloud while keeping a mechanical migration mapping.

The baseline `facebook-group-comment-coverage` capability still forbids commenting in a group on the day it was joined. The requested combined action therefore needs a narrow, explicit exception instead of silently bypassing the coverage selector’s warmup contract.

## Goals / Non-Goals

**Goals:**

- Add one account-visible Facebook rule mode with a fixed versioned definition: ten unique confirmed reads, then one like attempt followed by one join-contact-comment attempt.
- Give active slow start absolute ownership over the account so rule mode neither runs nor accumulates progress while slow start is active.
- Remove persona relevance and persona interaction preference from rule-mode browse and like decisions while retaining account identity, bound-persona admission, non-persona content safety, schedule, pacing, target integrity and risk controls.
- Persist unique-read progress, rule batches and separate action outcomes so restart, reconnect and duplicate messages cannot create extra batches or fake completion.
- Reuse existing Edge atomic capabilities and the existing/currently proposed join-contact orchestrator.
- Expose truthful configuration, progress, suppression and partial-result states in the unified Facebook account automation view.

**Non-Goals:**

- Supporting Xiaohongshu, WeChat Channels or an unknown platform.
- Providing a free-form rule editor, arbitrary scripts, configurable thresholds or arbitrary action graphs.
- Changing the slow-start curve, risk quotas, cooldown values, approval policy, contact information, Facebook comment body configuration or group target catalog.
- Allowing an unbound-persona account to run. Rule mode does not use persona for browsing/liking, but the existing account admission and comment composition contracts remain.
- Replacing current Cloud orchestration with the not-yet-implemented managed automation runtime.
- Creating a new Edge-side authorization switch, process environment flag, retry queue or compatibility fallback.
- Packaging/releasing an Edge installer, deploying OL or performing real-account writes as part of proposal creation.

## Decisions

### 1. Choose one authoritative browse mode before a session starts

Cloud derives an account’s effective browse mode from server-side facts:

```text
platform != facebook
  → rule_mode_unsupported

slowStart.state == active
  → slow_start owns the account

slowStart.ineligibleReason in
  {binding_unknown, binding_conflict, platform_unknown, platform_unsupported}
  → fail closed; start neither rule nor persona automation

ruleConfig.enabled == true
  AND effective weekly active window is active
  AND all existing account/session admission gates pass
  → facebook_rule

otherwise
  → existing persona mode
```

`slowStart.binding` does not participate in arbitration. `state=active` wins even when the current risk tier is already stricter and the slow-start clamp changes no numbers. `state=graduated` is no longer active and may enter rule mode. A known `state=off` caused by the explicit global slow-start disable is treated as off; it is not reinterpreted as an unknown binding.

If slow start becomes active while a rule session is running, Cloud stops accepting new rule views at the next safe boundary, cancels only undispatched rule action intents and parks/returns the browser through the existing session lifecycle. An already dispatched platform write is not undone; its receipt is still reconciled. Progress accumulated before the takeover is frozen, not reset, and views observed while slow start owns the account never enter rule progress.

Alternative considered: compare cold-start and rule quotas and run whichever is stricter. Rejected because the user chose mode precedence, not numeric composition; running both would still execute the rule’s deterministic writes during cold start.

### 2. Keep the product configuration small and version the definition

The user-visible configuration is account-scoped and contains:

- `accountId`
- `enabled`
- fixed `definitionId=facebook_browse_10_like_1_join_contact_1`
- fixed `definitionVersion=1`
- `updatedAt`
- `updatedBy`

There is no editable threshold, action list or rule source text in v1. The account automation UI explains the fixed behavior and writes non-optimistically: Cloud validates that the account exists and its normalized platform is `facebook`, persists the full accepted state and returns authoritative readback. Missing rows default to disabled and do not create database rows on read.

The configuration is a shared account/business fact and is not split by deployment target. Runtime progress, claims and idempotency are target-scoped and carry server-injected `execution_target`, matching the repository’s DEV/OL worker invariant.

Alternative considered: add fields to `account_content_schedule`. Rejected because a count-trigger definition is not an hourly content action and platform-specific configuration is already intentionally kept out of the generic schedule row. The UI remains unified while the domain storage stays separate.

### 3. Use a dedicated non-persona Cloud selector, not the existing persona evaluator

At session assembly Cloud chooses one role graph:

- persona mode keeps the current `ContentEvaluator → ContentCurator → InteractionAppraiser` path;
- rule mode registers a deterministic `FacebookRuleCardSelector` and does not register persona relevance, mandatory-interaction or like-affinity decision roles.

The rule selector consumes Facebook cards in reported feed order, requires a stable canonical content identity, excludes identities already confirmed in the active rule batch, and selects the first structurally eligible unseen item. It does not call Soul, compare interests, invoke mandatory rules or ask an LLM whether the account likes the content.

Non-persona hard safety remains separate:

- login, checkpoint, consent, captcha and blocking-overlay checks;
- canonical page/card identity and exactly one action target;
- a Soul-free prohibited-content safety gate;
- already-visited/duplicate and already-liked observations;
- supported platform capability and active session/lease;
- pacing/dwell, post-action observation and honest receipts.

The safety gate may use deterministic classifiers or a bounded schema-validated safety model, but its input must not contain the account Soul and its output is only `allow | reject(reason)`. This split is necessary because today’s persona evaluator also contains brand-safety instructions; simply bypassing the whole role would accidentally remove both concerns.

The existing persona binding gate remains at account admission. This is a deliberate narrow exception to “persona is an input to every browse decision,” not permission for unbound accounts to run. Existing Facebook comment generation/template selection, contact injection and approval continue unchanged.

### 4. Count only durable unique confirmed reads

A rule view is eligible only after the current Facebook read contract has produced a confirmed `view` fact with:

- account identity;
- canonical stable content key;
- occurred time;
- originating message/receipt dedupe key;
- current definition revision;
- server execution target.

Mounted cards, loading placeholders, duplicate reports, background articles, navigation-only opens, repeated content in the active batch and content seen while slow start owns the account do not advance progress.

The Cloud handler durably enqueues the rule-view fact alongside the existing risk fact. Rule progress is applied asynchronously and idempotently; failure to durably enqueue a rule fact halts rule progression rather than continuing with an under-counted cadence.

The minimal runtime data model is:

```text
facebook_rule_mode_config
  account_id PK
  enabled, definition_id, definition_version
  updated_at, updated_by

facebook_rule_progress
  account_id + execution_target PK
  definition_version, batch_seq, confirmed_view_count
  state, updated_at

facebook_rule_view_fact
  account_id + execution_target + definition_version
  batch_seq + content_key UNIQUE
  source_dedupe_key UNIQUE per execution_target
  occurred_at

facebook_rule_batch
  batch_id PK
  account_id, execution_target, definition_version, batch_seq
  trigger_content_key
  like_state/reason, join_contact_state/reason
  overall_state, created_at, updated_at
```

When the tenth unique fact is inserted, one database transaction closes that set of ten, creates exactly one batch and advances progress to the next `batch_seq`. A unique batch key prevents two workers or a restart from creating two batches.

Alternative considered: use `risk_counters(view) % 10`. Rejected because the aggregate loses content identity, rule revision and active-batch boundaries, and an asynchronous duplicate/restart can create missed or repeated milestones.

### 5. Bind the like attempt to the trigger content

The tenth confirmed content is the batch’s `trigger_content_key`. Rule mode first attempts a like against that same current content while its target evidence is still fresh. It does not search for a “better” post, revisit one of the previous nine, or ask the persona appraiser.

Immediately before dispatch Cloud evaluates the existing like admission chain, including:

- `RiskController.explain('like')`;
- like/view ratio;
- cooldown;
- single-session like budget;
- platform capability;
- target still current, unique and not already liked.

A rejected gate produces a terminal `risk_suppressed` or named structural skip for this batch. It does not keep a like debt for a later page. Only an Edge/platform-confirmed new like is reported as confirmed; already-liked, missing target, ambiguous and failed receipts remain distinct.

Like runs before group navigation because the current feed target may be lost once the browser enters a group.

### 6. Treat a batch as two serial, independently truthful action attempts

After the like attempt reaches a terminal state, the batch may start the join-contact attempt under the same account single-flight:

```text
10 confirmed unique views
  → like attempt
  → join new group
  → require platform-confirmed joined/already_member + exact group
  → select pinned group post
  → compose/template + contact injection + configured approval
  → comment submit + server verification
  → batch terminal
```

`join_group` and `comment` each run their own just-in-time `RiskController.explain` gate and existing session/daily budgets. Passing one action never pre-authorizes the next. If like is suppressed, join-contact may still proceed if its own gates allow it; if join fails or is ambiguous, comment never begins. If comment is rejected, times out, fails or becomes submitted-unknown, the join truth remains intact and the batch reports a partial result.

The batch is an attempt budget, not a success debt. Risk suppression, approval rejection, missing target, offline/not-started and other terminal outcomes do not queue work for a future quota reset and do not cause multiple historical batches to burst later. A new opportunity requires ten new confirmed views.

While a batch is non-terminal, rule browsing does not accumulate the next batch. Approval/resource waits may release the physical browser according to existing lease semantics, but the account retains logical rule-batch ownership so another periodic source cannot create a concurrent batch.

### 7. Reuse the join-contact orchestrator and define one scoped warmup exception

This change consumes the `facebook-join-contact-first-post` command entry with:

- `injectContact=true`
- `joinFirst=true`
- `priority=automatic`
- the account’s effective approval mode
- no manual override or force flag
- source metadata identifying the rule batch

Feature activation is blocked until that dependency’s Edge, Cloud, Console and protocol tasks are implemented and validated. There is no alternate fallback to an old joined group, whole-site search, second post or a duplicate comment pipeline.

The baseline same-day warmup rule is modified narrowly: a caller-pinned group that was joined by this exact Facebook rule batch may proceed to contact comment after platform-confirmed `joined`/`already_member`, provided slow start is not active and all gates pass. Unpinned daily coverage, standalone automatic join, persona-mode comments and any other source continue to respect normal warmup/cooldown selection.

### 8. Keep time scheduling as an outer window, not the count trigger

Rule mode inherits the account’s effective weekly active window. It may start/resume only in an active cell and stops at the existing safe boundary when entering a sleep cell. The rule definition does not reuse content-active hour cells, per-action hash minutes or `ContentScheduler`’s `(account, action, hourCell)` idempotency.

This preserves one meaning per mechanism:

- weekly active window: when the account may browse;
- slow start: which lifecycle mode owns the account and how risk quotas are clamped;
- rule progress: when ten confirmed reads create one batch;
- RiskController: whether each physical action may occur now.

### 9. Project configuration, progress and three layers of truth

The Facebook account automation view shows:

- rule mode enabled/disabled and fixed definition text;
- effective mode: `slow_start | rule | persona | blocked`;
- progress `0..9 / 10` only while rule mode owns the account;
- current batch and separate like/join/contact outcomes;
- named blockers such as `slow_start_active`, `binding_unknown`, `schedule_sleep`, `risk_suppressed`, `edge_offline`, `waiting_approval`, `submitted_unknown`;
- last authoritative update time.

The UI does not show “liked” or “commented” from a trigger, intent or command acceptance. Configuration readback, runtime progress and platform result are separate projections. Writes are non-optimistic and unknown/stale mirrors stop new rule work.

### 10. Keep a mechanical migration path to managed automation

The current vertical uses explicit types and boundaries that map later without changing product semantics:

| Current vertical | Future managed automation |
| --- | --- |
| rule config + definition version | ManagedPlan + TaskDefinition version |
| ten-view progress | StepRun checkpoint |
| rule batch | TaskRun |
| like / join-contact states | StepRun + ExecutionAttempt |
| per-account single-flight | account work arbiter lane |
| named gate/outcome reasons | DecisionTrace + Execution Ledger |

This change does not wait for the future repository. A later cutover must shadow and reconcile the current persisted batch/progress state before enabling the corresponding Trigger Binding; it must not reset counts or re-dispatch old attempts.

## Risks / Trade-offs

- **[Bypassing persona also bypasses today’s combined brand-safety prompt]** → Split a Soul-free safety gate and require its tests before rule mode can be enabled.
- **[The tenth post is mechanically chosen and may be unsuitable to like]** → Bind to the current target, keep structural/safety/risk gates, report a skip and do not retarget or accumulate debt.
- **[Slow start changes during a batch]** → Re-read authoritative mode at safe boundaries and before each undispatched write; stop new work while preserving already-dispatched truth.
- **[Progress write amplification]** → Store one compact fact per confirmed unique read and checkpoint only at fact/batch boundaries; do not persist every card or scroll event.
- **[DEV and OL both scan the same account]** → Runtime claims and dedupe are execution-target scoped, while platform risk accounting remains account-global; account/environment lifecycle must still prevent simultaneous real ownership.
- **[Join succeeds but comment fails]** → Preserve the membership ledger fact and expose a partial batch result; never roll back or relabel the join.
- **[The same-day exception broadens spam risk]** → Scope it to caller-pinned groups from this fixed rule, require cold start off/graduated, keep all join/comment budgets and approval, and leave ordinary coverage warmup unchanged.
- **[Dependency is only specified, not implemented]** → Block feature activation and integration acceptance until `facebook-join-contact-first-post` is landed and validated.
- **[Future managed runtime duplicates current state]** → Keep stable definition/batch IDs, require shadow reconciliation and forbid dual writers during cutover.

## Migration Plan

1. Add strict OpenSpec deltas and validate the dependency/conflict matrix before code.
2. Add schema through the repository migration executor; deploy with no config rows and default disabled.
3. Add Cloud authority APIs, mirror/read model and Console display/write flow; verify non-Facebook and missing-row fail-closed behavior.
4. Add durable view facts, progress and batch worker without enabling physical action dispatch; validate restart/reconnect/idempotency with fixtures.
5. Add the non-persona Facebook rule selector and safe mode arbitration; keep existing persona mode unchanged.
6. Integrate confirmed-like dispatch and then the landed `facebook-join-contact-first-post` orchestrator, preserving per-action risk and truthful partial outcomes.
7. Rebase/integrate owning repositories serially, run protocol/risk/comment acceptance, full suites and typechecks, then deploy eligible Cloud changes to DEV from a clean default checkout.
8. Keep all accounts disabled until an explicitly authorized DEV account acceptance. Edge packaging/release and OL remain separate authorization boundaries.

Rollback disables rule config for all accounts first, preventing new batches. Undispatched batches become cancelled with a reason; dispatched actions continue to receipt/reconciliation. Source rollback may then remove the runtime readers while retaining tables and historical facts for audit. Rollback must not delete or rewrite confirmed likes, memberships or comments.

## Open Questions

None. The v1 threshold/action graph, cold-start precedence, Facebook-only scope, persona-bypass boundary, risk behavior and scoped same-day join-contact exception are fixed by the confirmed product direction.
