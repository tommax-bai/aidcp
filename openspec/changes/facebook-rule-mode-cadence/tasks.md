## 1. Admission and dependency alignment

- [x] 1.1 Run repository preflight, create isolated `codex/facebook-rule-mode-cadence` worktrees for each owning repo, and record the admitted paths and starting SHAs.
- [x] 1.2 Rebase the implementation plan on the latest `facebook-join-contact-first-post` contracts and block rule-mode activation until its join-then-contact path is implemented and validated.
- [x] 1.3 Reconcile the scoped same-day warmup exception with any intervening `facebook-group-comment-coverage` changes without weakening ordinary coverage, persona-mode, or standalone-join warmup.
- [x] 1.4 Confirm the existing Cloud, Edge, Console, protocol, schedule, slow-start, and risk owners before editing, and document any deviation from the design in this change.
<!-- 1.1-1.4: preflight PASS. Worktrees: control@0c065b3, cloud@6a6c5e5, edge@c37ae9c, console@9896919 on codex/facebook-rule-mode-cadence. The admitted Cloud/Edge defaults already contained joinFirst + first_commentable_group_post and their focused tests. Owner deviation: config/runtime schema was split into API-owned 0092 and automation-owned 0093 instead of one cross-owner migration; numbering moved after rebase preserved default-branch 0089-0091. No protocol or Edge implementation change was required. -->

## 2. Cloud configuration and authority

- [x] 2.1 Add the shared `facebook_rule_mode_config` migration and repository with the fixed v1 definition, disabled-on-missing-row behavior, audit fields, and Facebook-only write validation.
- [x] 2.2 Add authoritative Cloud read/write APIs for the account rule configuration; reject non-Facebook and unknown-platform accounts and return persisted readback without optimistic success.
- [x] 2.3 Project rule configuration into the unified account automation read model without storing count-trigger settings in `account_content_schedule`.
- [x] 2.4 Add authorization, account-scope, audit, API-schema, missing-row, and non-Facebook tests for configuration reads and writes.
<!-- 2.1-2.4: aidcp-cloud commits 8315c58 + 79c9f2a. Focused store/panel/schema tests PASS; config writes transactionally bump the existing content_schedule mirror key and catalog projection omits stale/unavailable rule truth instead of fabricating disabled/zero. Deployment pending §8.6. -->

## 3. Cloud mode arbitration and selection

- [x] 3.1 Implement one Cloud effective-mode arbiter in the required order: unsupported platform, active slow start, unknown/conflicting slow-start identity, eligible rule mode, then existing persona mode.
- [x] 3.2 Stop a running rule session at the existing safe boundary when slow start becomes active, cancel only undispatched intents, reconcile dispatched writes, and freeze prior rule progress.
- [x] 3.3 Implement `FacebookRuleCardSelector` over stable Facebook content identities and feed order without invoking Soul relevance, mandatory persona rules, persona interaction preference, or persona like appraisal.
- [x] 3.4 Preserve the bound-persona account admission gate and implement or reuse a Soul-free prohibited-content safety gate plus login, checkpoint, consent, captcha, target-integrity, duplicate, session, and pacing gates.
- [x] 3.5 Keep the existing persona-mode role graph and behavior unchanged when rule mode is disabled or ineligible.
- [x] 3.6 Add focused tests for active/graduated/off/unknown slow-start states, mid-session takeover, zero persona-decision calls in rule mode, preserved non-persona safety, and unchanged persona-mode selection.
<!-- 3.1-3.6: aidcp-cloud commits 8315c58 + 79c9f2a. Rule selector accepts only canonical www.facebook.com post identities, rejects explicit high-risk captions, and bypasses ContentEvaluator/ContentCurator LLM decisions only while the arbiter returns facebook_rule. In-flight like is terminalized ambiguous on reconnect/session boundary; undispatched work becomes not_started. Focused arbiter/dispatcher/content-role tests and the Cloud full suite PASS. -->

## 4. Durable progress and batch creation

- [x] 4.1 Add target-scoped migrations and repositories for rule progress, unique confirmed-view facts, and rule batches with definition revision, sequence, dedupe, timestamps, and explicit action states.
- [x] 4.2 Durably enqueue an eligible rule-view fact from a confirmed Facebook read and halt rule progression if that enqueue cannot be committed.
- [x] 4.3 Apply facts idempotently so only ten distinct stable content keys for the current account, execution target, definition version, and collecting sequence can close a set.
- [x] 4.4 Atomically create one batch on the tenth eligible view, bind `triggerContentKey` to that content, advance the sequence, and prevent another collecting set while the batch is non-terminal.
- [x] 4.5 Exclude mounts, placeholders, scroll-only observations, background articles, duplicate/replayed receipts, unstable identities, and reads made while slow start owns the account.
- [x] 4.6 Add migration, concurrency, restart, reconnect, duplicate-receipt, cross-target isolation, definition-version, and `7/10` resume tests.
<!-- 4.1-4.6: aidcp-cloud commits 8315c58 + 79c9f2a. Tests cover 7/10 restart, concurrent tenth fact, content/source receipt dedupe, DEV/OL isolation, active-batch single flight, terminal debt release, reconnect ambiguity, process recovery, schema owner/version constraints, and risk-outbox failure halting rule emission. -->

## 5. Like attempt

- [x] 5.1 Create the batch like intent only for the still-current tenth content, with deterministic idempotency and no retarget, back-search, or persona appraisal.
- [x] 5.2 Apply just-in-time `RiskController.explain('like')`, like/view ratio, cooldown, session budget, capability, current-target, and already-liked gates before dispatch.
- [x] 5.3 Persist distinct confirmed, structural-skip, risk-suppressed, not-started, failed, ambiguous, and submitted-unknown outcomes from honest Edge/platform evidence.
- [x] 5.4 Make every terminal suppression or skip debt-free so later quota recovery never replays the old like attempt.
- [x] 5.5 Add focused tests for the tenth-content binding, changed/absent target, already-liked observation, risk suppression, duplicate dispatch prevention, and truthful receipt reconciliation.
<!-- 5.1-5.5: aidcp-cloud commits 8315c58 + 79c9f2a. RiskController explain retains the existing ratio gate; focused Cloud tests cover tenth binding, risk suppression without debt, already_satisfied, structural_skip, submitted_unknown, duplicate prevention, and reconnect ambiguity. Existing Edge ba5ade4 suites verify no_target, target_lost, identity_mismatch, ambiguous_target, target_not_visible, and already_liked without fallback. -->

## 6. Join-contact attempt

- [x] 6.1 After the like attempt becomes terminal, invoke the single implemented join-contact orchestrator with the pinned rule batch, `joinFirst=true`, `injectContact=true`, automatic priority, effective approval mode, and no force/manual override.
- [x] 6.2 Re-run independent just-in-time risk, daily/session, approval, contact, dedupe, platform, and exact-target gates for `join_group` and `comment`.
- [x] 6.3 Allow the scoped same-day contact comment only after the same batch confirms `joined` or `already_member` for the exact pinned group and slow start is still not active.
- [x] 6.4 Persist like, membership, and comment outcomes independently; block comment on an unconfirmed join and render partial, ambiguous, rejected, failed, and submitted-unknown results without coercing success.
- [x] 6.5 End suppressed or unavailable action attempts without debt, keep logical batch ownership during approval waits, and prevent another batch or scheduler from running concurrently.
- [x] 6.6 Add focused tests for like-suppressed/join-allowed, join ambiguity, already-member, slow-start takeover, approval wait, comment risk rejection, submitted-unknown, ordinary warmup preservation, and no replay after quota reset.
<!-- 6.1-6.6: aidcp-cloud commits 8315c58 + 79c9f2a. Reuses CommentScheduler joinFirst path; actionGate re-reads ownership/risk before join, after confirmed membership, and after approval immediately before submit. Focused plus existing comment-scheduler suite covers joined/already_member/non-member, approval, warmup/coverage preservation, partial truth, risk suppression, and no historical replay. -->

## 7. Active window, Console, and Edge integration

- [x] 7.1 Reuse only the effective weekly account active window for rule session start/resume/stop; prove content hour cells, action modes, and hash-minute offsets do not trigger or advance the ten-view cadence.
- [x] 7.2 Extend the Console Facebook account automation view with non-optimistic enable/disable controls and separate effective mode, `0..9/10` progress, batch actions, blockers, and update-time projections.
- [x] 7.3 Render stale or unavailable configuration/progress as unknown and keep active slow start distinct from disabled rule mode or fabricated zero progress.
- [x] 7.4 Reuse existing Edge atomic browse, like, join, comment, and receipt capabilities; add only the minimum synchronized protocol/route changes required by the validated join-contact dependency.
- [x] 7.5 Keep authorization, pacing, scheduling, progress, and final risk decisions in Cloud and verify Edge introduces no local rule toggle, counter, fallback, or second risk authority.
- [x] 7.6 Add Console component/API tests and any required Edge command, target-integrity, and receipt tests, including explicit non-Facebook rejection.
<!-- 7.1-7.6: aidcp-console commit 5af538d; aidcp-cloud commits 8315c58 + 79c9f2a; Edge has no feature diff at ba5ade4. Cloud uses effectiveActiveWeekMask only; rule facts originate only from confirmed reads and never from content scheduler hour claims. Post-rebase Console focused 22 tests, full 39 files / 285 passed / 1 skipped, typecheck and production build PASS. Cloud Panel API tests cover auth/account scope/non-Facebook rejection. Existing Edge protocol/browse/like/join/comment/native-page-engine suites plus typecheck PASS. -->

## 8. Validation, integration, and delivery

- [x] 8.1 Run focused Cloud acceptance tests for mode precedence, unique counting, action ordering, risk honesty, partial outcomes, single-flight, active-window behavior, and target isolation.
- [x] 8.2 Run the Cloud full test suite and typecheck; if Edge or protocol changed, run the required Edge safety/acceptance suites, full tests, and typecheck.
- [x] 8.3 Run Console tests, typecheck, and production build, then run protocol-drift, unauthorized-publish, risk-honesty, and relevant end-to-end safety suites.
- [x] 8.4 Update completed tasks with owning repo, commit SHA, exact validation, deployment result, and any deviation, then run `openspec validate facebook-rule-mode-cadence --strict`.
- [x] 8.5 Fetch and rebase each implementation worktree onto the latest default, resolve single-writer hotspots serially, rerun required validation, and fast-forward integrate with explicit path scopes.
- [x] 8.6 Commit and push the validated default branches, run deployment preflight, deploy runtime Cloud changes to `dev`, and verify service, listener, health, database, and behavior evidence with rollback on failure.
- [x] 8.7 Keep OL deployment, Edge installer packaging/release, and real-account Facebook writes outside this change unless separately and explicitly authorized; report source, DEV runtime, package, and platform evidence as distinct boundaries.
<!-- 8.1-8.3: Post-rebase Cloud focused rule/panel/schema/boundary/safety tests PASS; Cloud full `npx tsx --test --test-reporter=dot 'test/**/*.test.ts'` + typecheck PASS. Console full single-worker suite 39 files / 285 passed / 1 skipped, focused rule page 22/22, typecheck and production build PASS. Edge no feature/protocol diff; relevant protocol, browse, exact-target like, join, comment, Native router/parity suites and typecheck PASS. 8.7 boundary held: no OL, installer, or real-account write. -->
<!-- 8.4: OpenSpec strict validation PASS in aidcp control worktree before integration and again after recording DEV evidence in 8.6. -->
<!-- 8.5: Rebased on control bfac77a, cloud 545099b, console a369544, and edge ba5ade4. Cloud migration collision with default 0089-0091 resolved by renumbering this change to API 0092 / automation 0093 while retaining both ownership rows and schema notes. Post-rebase Cloud full + typecheck, Console 39 files / 285 passed / 1 skipped + typecheck + build, Edge focused safety suites + typecheck, and OpenSpec strict validation PASS. Fast-forward integration completed to local main/master with explicit repos; unrelated control untracked PDF artifacts were preserved. -->
<!-- 8.6: Pushed control main 3414314, Cloud master 79c9f2a, and Console master 5af538d after deploy-target dev preflight PASS. Backups at /opt/aidcp/backups use stamp 20260727-223623 for Cloud source/env, Console, and all three owner databases. DEV applied API 0092_facebook_rule_mode_config and automation 0093_facebook_rule_mode_runtime; post-migrate status is content 20/20, automation 51/51, API 59/59 with zero pending. Restarted only aidcp-cloud.service: active, NRestarts=0, listeners 8787/8090/8088/5432 present, local and public /api/health returned {"ok":true}, and all owner DB SELECT 1 probes passed. Owner readback found config only in API and progress/view-fact/batch only in automation; config rows=0 and aggregate runtime rows=0, so every account remains disabled and no platform action was emitted. Startup logs confirmed the dev automation writer lock, schema gates through 0093/0092, panel/API listeners, and Feishu WS onReady. Console index/JS/CSS returned 200 publicly and matched local SHA-256; all four running isales units remained untouched. No rollback was required. -->
