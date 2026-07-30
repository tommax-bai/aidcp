## 1. Cloud configuration authority and schema

- [x] 1.1 Add additive migrations for environment operation-policy revisions/audit, target-scoped group-comment policy/audit, rule revision snapshots, and consumption progress/fact/action tables; update schema capability contracts.
- [x] 1.2 Implement the typed environment operation-policy store, server-owned bounds/defaults, environment/platform validation, `expectedRevision` compare-and-swap, immutable audit, migration seeding, and write-after-read projection.
- [x] 1.3 Integrate the existing slow-start lifecycle into effective-mode resolution without creating a second base-mode authority; preserve active slow-start precedence and named binding/platform blockers.
- [x] 1.4 Add Panel `GET/PUT /api/environments/:envKey/facebook-operation-policy` routes and map the customer environment rule-toggle endpoint through its bounded `persona ↔ rule` compatibility contract.
- [x] 1.5 Implement the target-scoped group-comment policy store and `GET/PUT /api/facebook/groups/comment-policy`, including `db → legacy_env → default` read source, CAS, audit, strict bounds, and write-after-read.
- [x] 1.6 Add focused store/API tests for defaults, unbound environment writes, ownership/platform rejection, stale revisions, concurrent writes, audit atomicity, compatibility conflicts, and unavailable schema/storage.
  <!-- aidcp-cloud: migrations 0099-0101; operation/group policy stores and Panel/customer routes; legacy rule compatibility uses exact-env slow-start arbitration, server-read CAS, transactional ownership recheck, and write-after-read binding truth. -->

## 2. Configurable rule-mode cadence

- [x] 2.1 Replace numeric rule definition identity with a stable algorithm identity plus immutable `policy_revision` and snapshot fields while retaining historical fixed-definition rows for read-only audit.
- [x] 2.2 Parameterize rule confirmed-view threshold and join-contact round cadence from the pinned policy snapshot without changing the existing round-based, immediate pinned-group comment semantics.
- [x] 2.3 Implement revision transitions: stop old collection, terminate undispatched old work as `policy_superseded`, settle already-dispatched receipts truthfully, and start new-revision progress from zero.
- [x] 2.4 Update rule-mode projections and focused tests for non-default thresholds, duplicate confirmed views, old/new revision isolation, like-only terminal rounds, slow-start precedence, and partial/ambiguous outcomes.
  <!-- aidcp-cloud: stable algorithm identity plus revision snapshots; rule cadence acceptance and dispatcher/runtime coverage included in the 290-test focused run. -->

## 3. Durable consumption-mode orchestration

- [x] 3.1 Implement the target/revision-scoped consumption runtime store with transactional unique-view facts, counters, immutable action obligations, exact targets, dispatch phases, result dedupe, single-flight ownership, and restart recovery.
- [x] 3.2 Admit confirmed unique browse facts only while effective mode is `consumption`; create one exact-content like obligation per configured view threshold and consume the threshold without retry debt.
- [x] 3.3 Classify like receipts so only a platform-confirmed newly produced like advances `confirmedLikesPerJoin`; keep `already_liked`, pending, ambiguous, gated, structural and failed outcomes distinct and non-counting.
- [x] 3.4 Create join-only obligations from confirmed new-like thresholds, wait truthfully when no target is assignable, invoke the existing atomic join executor without `joinFirst`, and count only a platform-confirmed new `joined` result rather than `already_member`.
- [x] 3.5 Create historical-group comment obligations from confirmed new-join thresholds, retain `waiting_target` while no strict candidate exists, and select solely by joined status, current join-to-first-comment wait, and independent re-comment cooldown without an extra current-cycle exclusion or relaxed fallback.
- [x] 3.6 Force `first_commentable_group_post` for the bound group, bypass account keyword search, and run plain comment composition through existing approval/risk/dedupe/exact-target/platform-readback gates; count only confirmed comments.
- [x] 3.7 Implement policy/mode supersession, correlated late settlement without downstream advancement, durable projections, blockers, structured events and metrics for confirmed-new, already-state, waiting, ambiguous and failed outcomes.
- [x] 3.8 Add focused consumption tests for configurable `5/2/2` and non-default cadence, duplicate receipts, `already_liked`, `already_member`, pending/ambiguous/failed non-counting, no-debt one-shot attempts, strict waiting selection, current-cycle timestamp eligibility, first-commentable targeting, restart recovery and revision isolation.
  <!-- aidcp-cloud: durable runtime/coordinator, exact-target dispatch and truthful receipt accounting covered by focused runtime, coordinator, dispatcher, handler and comment tests. -->

## 4. Scheduler and group-coverage boundaries

- [x] 4.1 Make group coverage read the current target-scoped join-to-first-comment policy before selection, pin its revision with a selected target, retain the separate re-comment cooldown, and keep the ordinary relaxed fallback behavior isolated from consumption.
- [x] 4.2 Gate independent scheduled Facebook group joining on authoritative effective `persona` immediately before assignment/dispatch; unknown, slow-start, rule and consumption modes skip without consuming a schedule fire or fabricating an outcome.
- [x] 4.3 Keep manual, rule and consumption callers able to use the lower-level atomic join executor under their own source attribution and existing scope/risk/session/confirmation gates.
- [x] 4.4 Add scheduler/coverage acceptance tests for persona-only scheduled joins, fail-closed mode lookup, mode-specific executor reuse, dynamic timing revisions, strict consumption selection and independent 72-hour re-comment cooldown.
  <!-- aidcp-cloud: scheduled joining is persona-only; strict consumption selection has no relaxed fallback and uses current timing policy plus the independent re-comment cooldown. -->

## 5. Console and Edge configuration surfaces

- [x] 5.1 Add typed operation-policy API models and an `/environments` editor for effective/configured mode, rule cadence, consumption cadence, revision, binding truth and blockers using server bounds, CAS and post-write refetch.
- [x] 5.2 Remove rule/consumption mutation authority from `/content-schedule` and show read-only effective mode, current revision progress, active action states and named unknown/blocker projections.
- [x] 5.3 Add the `/facebook-groups` “入群后首次评论等待（小时）” editor with source, revision, server bounds, CAS and post-write truth, visibly separate from same-group re-comment cooldown.
- [x] 5.4 Add Console tests for all mode-specific forms, invalid/stale/unavailable states, unbound environments, failed-write form retention, content-schedule projection-only behavior and group timing terminology.
  <!-- aidcp-console: focused 50/50, npm run typecheck, npm run build (3730 modules; existing chunk-size warning only), git diff --check. -->
- [x] 5.5 Add customer-auth `GET/PUT /environments/:envKey/facebook-operation-policy` with ownership/platform checks, strict `{expectedRevision,mode}` input, CAS conflict truth and a cadence-free customer DTO.
- [x] 5.6 Extend atomic environment provisioning with mutually exclusive `facebookOperationMode`, initial policy/audit persistence and write-after-read truth while retaining released Boolean inputs only as compatibility.
- [x] 5.7 Add the Edge client consumption entry to both Facebook environment creation and the existing-environment mode area, ordered after cold-start and rule, using only the unified Cloud projection and non-optimistic CAS writes.
- [x] 5.8 Add Cloud customer-route/provisioning tests and Edge intent/IPC/renderer tests for mode ordering, priority, strict inputs, conflicts, offline/unavailable truth and absence of cadence numbers.
  <!-- aidcp-edge: focused contract/receipt 28/28 plus renderer smoke, npm run typecheck, three node --check commands and git diff --check; no installer/package built. -->

## 6. Validation, integration and DEV delivery

- [x] 6.1 Run Cloud focused acceptance tests for policy, rule, consumption, group coverage, scheduler, comment outcomes and risk honesty; record command, exit status and concise counts.
  <!-- `npx tsx --test --test-reporter=spec` over 13 focused policy/rule/consumption/group/scheduler/comment files: exit 0, 290/290. Boundary/schema ownership set: exit 0, 43/43. -->
- [x] 6.2 Run Cloud full tests and typecheck, then Console and Edge focused tests/build/typecheck; resolve only failures caused by this change.
  <!-- Cloud `npx tsx --test --test-reporter=dot 'test/**/*.test.ts'`: exit 0; `npm run typecheck`: exit 0. Console and Edge evidence recorded above. -->
- [x] 6.3 Run `openspec validate add-configurable-facebook-consumption-mode --strict` and record implementation commits, validations, deviations and delivery evidence in this checklist.
  <!-- Implementation commits before integration: aidcp-cloud 56bb0bd, aidcp-console b7cf9d8, aidcp-edge 8e0a593. Strict OpenSpec validation: exit 0. Deviation: bounded DEV behavior probes remain task 6.6 because no test environment was selected; no Edge package and no OL deployment. -->
- [ ] 6.4 Rebase and fast-forward integrate clean Cloud, Console and Edge default branches, push them and the control change, without modifying unrelated worktree changes.
- [ ] 6.5 Read deployment guidance, run DEV target checks, back up the affected Cloud configuration/schema, deploy only documented AIDCP DEV services and Console, then verify service/listener/health/schema and rollback readiness.
- [ ] 6.6 Perform a bounded DEV verification on explicitly selected test environments: backend write-after-read, effective-mode arbitration, no scheduled join outside persona, strict no-eligible-group waiting, and confirmed-versus-ambiguous counter truth; do not package Edge or deploy OL.
