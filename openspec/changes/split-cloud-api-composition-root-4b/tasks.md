## 1. Admission, Inventory and 4a Barrier

- [x] 1.1 Run control preflight; create isolated worktrees/branches for every owning repo and preserve canonical/unrelated files.
  <!-- 2026-07-26: preflight PASS. Created codex/split-cloud-api-composition-root-4b worktrees for control, Cloud, kernel, transport, API, automation, Console and Edge from their exact post-3b defaults. Every code worktree has a physical non-symlink node_modules directory. Canonical repos remain on main/master and clean; preserved the control repo's unrelated user report artifacts. -->
- [x] 1.2 Add a machine-readable A1–A6/B1–B5 inventory with current call sites, owner, consumer, fact scope, local shape, freshness tier and derived members.
  <!-- 2026-07-26: Cloud boundaries/sync-read-inventory.json pins the 67941e4 pre-4a census and records all eleven groups, twelve remote streams, current declarations/call sites, owner/consumer/scope, local shape and freshness tier. B1/B2/B4 are explicitly provisional until the post-4a census. -->
- [x] 1.3 Add a census that rejects unregistered synchronous cross-owner reads and separately rejects side-effect methods in snapshot members.
  <!-- 2026-07-26: test/acceptance/sync-read-inventory.test.ts derives observed methods from machine-readable source regions/receivers/imports, filters asynchronous declarations, compares the result to the inventory and includes a mutation fixture proving an unregistered read-shaped method is rejected. It also rejects side-effect-shaped snapshot members. -->
- [x] 1.4 Assert A3 contains only `edgeCount`, `onlineEdgeCount` and `resolveEdgeIdForAccount`; verify 4a owns authenticated/idempotent/result-unknown `resumeEdgesForAccount`.
  <!-- 2026-07-26: the inventory and source-derived census pin A3 to the three pure reads only. The excludedSideEffects record assigns resumeEdgesForAccount to 4a's authenticated target-bound idempotent command with result_unknown; common tests fail if it enters a snapshot. -->
- [x] 1.5 Publish a hotspot ownership map: common envelope/kernel/local runtime MAY proceed in parallel; B1/B2/B4 owner mutations, roster/projection and `server.ts` remain blocked until 4a lands.
  <!-- 2026-07-26: Cloud boundaries/composition-root-4b-hotspot-ownership.json pins the 67941e4 base, names 4a as the blocker, permits only contracts/transport/local runtime/inventory in parallel, and reserves server.ts, AccountRosterSourcePort, automation_account_projection and B1/B2/B4 owner mutations to the post-4a 4b single writer. -->

## 2. Parallel Common Contracts and Runtime

- [x] 2.1 Define kernel `SyncReadStream`, `factScope`, versioned snapshot envelope, unsigned opaque cursor and exhaustive payload/readiness/health unions.
  <!-- Cloud source: src/kernel/sync-read-snapshot.ts. The closed registry contains twelve remote streams because B5 has four independent streams while the inventory remains eleven groups. -->
- [x] 2.2 Implement the shared atomic snapshot apply state machine with payload digest, per-instance target cursor, old-cursor rejection and invalid-envelope handling.
  <!-- AtomicSyncReadMirror validates target/scope/version/complete/cursor/value before replacement, compares unsigned decimal cursors through BigInt, retains last good value on invalid/old input and exposes named health/readiness state. -->
- [x] 2.3 Implement/test equal-cursor freshness renewal: only a newly fetched, later-`asOf`, digest-identical owner observation renews; historical replay or same-cursor drift does not.
  <!-- Focused tests cover owner_fetch renewal, replay non-renewal, digest drift invalidation and old-cursor rejection. -->
- [x] 2.4 Extract an instantiable per-process config-freshness runtime; missing source is stale/not-ready in split mode and explicit local-authority is allowed only in monolith.
  <!-- PerProcessConfigFreshnessRuntime has no ambient singleton; remote-mirror without a source stays stale, and local-authority construction is rejected for api/automation/content modes. -->
- [x] 2.5 Implement authenticated internal snapshot route/client primitives with server-injected target, fact-scope validation and no caller-selected target.
  <!-- src/transport/sync-read-snapshot-http.ts requires a nonempty owner-specific stream allowlist, rejects cross-owner registration and caller target fields, and validates target/scope on both server and client. Common focused/boundary validation: 38/38, typecheck/build PASS, boundary census 487/487 with zero cross-boundary edges. -->
- [x] 2.6 If persistence is required, add expand-only tables solely for target-scoped consumer cursor/readiness/health; do not target-partition shared facts, owner versions or projection payloads.
  <!-- Cloud 04c8ec9 adds owner-local 0082 api and 0083 automation checkpoint tables keyed by execution_target/consumer/stream. They persist only cursor, digest, source/observation/apply timestamps, freshness and health state; payloads, owner facts and shared versions remain absent. Restore stays recovering and rejects replay, including a newer cursor, until an authenticated owner_fetch succeeds. Focused 24/24, acceptance 133/133, typecheck and boundary/migration checks passed; no database migration or DEV runtime action was performed. -->
- [x] 2.7 Validate common Cloud tests/typecheck, kernel admission/build/dist and transport route/client/auth/target tests before any composition-root wiring.
  <!-- 2026-07-26: Cloud common/inventory/boundary 38/38, typecheck/build and diff-check PASS; boundary census 487 source = 487 ownership with zero cross-boundary edges. Derived kernel commit 1d7e89bff5f9c9ec93a3ebd25a3c690093667ca2 passed typecheck/build and a 12-stream dist export probe. Derived transport commit 5d332d5 passed typecheck/build/dist route export, pins kernel 1d7e89b exactly, and Cloud loopback tests cover bearer, mandatory owner allowlist, cross-owner rejection, caller-target rejection and server/client target/scope validation. Both commits are pushed on the 4b feature branch; default-branch integration remains a later serial step. -->

## 3. Automation-to-API Inventory Items

- [x] 3.1 **A1 week mask:** implement automation `session_config_global` full snapshot using the existing shared config version/bump; wire the api local scalar mirror and test first-load failure, stale last-good and equal-version renewal.
  <!-- Automation b54595a and API 8fd1879 use the shared sync_read_revision, full-snapshot mirrors and persisted checkpoints; focused tests cover first-load refusal, stale last-good and a newly observed equal-version renewal. -->
- [x] 3.2 **A2 scheduled catalog:** move the compile-time catalog and three pure reader methods into kernel, wire api/automation to the same artifact, and test export/pin drift without HTTP or projection storage.
  <!-- Kernel 0cb83d0 exports the exhaustive scheduled catalog and three pure readers; API 8fd1879 and Automation b54595a pin that artifact directly, with dist/export and exact-pin checks and no HTTP/projection copy. -->
- [x] 3.3 **A3 Edge presence:** implement a target-scoped snapshot/outbox signal for the three pure reads, wire api count/account→edge mirror, and test zero versus unknown/stale, heartbeat expiry and reconnect healing.
  <!-- Automation b54595a publishes the three-read target-scoped snapshot/change signal; API 8fd1879 atomically mirrors it and tests known zero, unknown/stale, expiry and reconnect/full-refresh healing. -->
- [x] 3.4 **A3 command exclusion:** add source/contract guards proving no presence payload/adapter invokes `resumeEdgesForAccount`; run 4a command tests for target/auth/idempotency/response-loss `result_unknown`.
  <!-- Source/inventory guards keep resumeEdgesForAccount outside A3, while the inherited 4a command acceptance retains server target injection, bearer auth, idempotency and response-loss result_unknown semantics. -->
- [x] 3.5 **A4 publish in-flight:** snapshot the dispatcher recordId set, wire api atomic set/evidence-state projection, and test empty-known versus unknown/stale plus durable approval projection precedence.
  <!-- Automation b54595a publishes the dispatcher recordId set and API 8fd1879 replaces it atomically; tests distinguish known-empty from unavailable evidence and keep the durable approval projection authoritative. -->
- [x] 3.6 **A5 captcha availability:** snapshot `disabled|available|unavailable|unknown`, wire api startup capability state, and test enabled-but-misconfigured, source loss and explicit disabled without copying secrets.
  <!-- Automation b54595a emits only the four-state capability fact and API 8fd1879 gates startup from it; tests cover misconfiguration, source loss and explicit disabled, and contract guards exclude secret material. -->
- [x] 3.7 **A6 mirror health:** snapshot automation-local health with source `asOf`, combine it with api-local health, and test stale delivery invalidates the whole automation section rather than preserving old `fresh`.
  <!-- Automation b54595a publishes owner-observed health/asOf and API 8fd1879 combines it with consumer health; stale delivery marks the complete automation section unavailable instead of retaining a false fresh state. -->
- [x] 3.8 For A3–A6, emit/coalesce target-scoped `sync_read.changed` outbox signals and test that failed snapshot apply holds topic cursor while periodic full snapshots heal missed notifications.
  <!-- Transport ec9dd3d and Automation b54595a implement authenticated target-bound closed-ACK delivery. Emission deduplicates only the same generation; consecutive generations are never coalesced because each is a durable fact. Failed fetch/apply/checkpoint holds the outbox topic cursor, while periodic authoritative full snapshots heal missed notifications. -->

## 4. Post-4a API-to-Automation Inventory Items

- [x] 4.1 After 4a lands, rebase onto its exact default SHA and rerun the call-site/write-path census before editing roster, persona/environment/account mutations, projection schema or composition roots.
  <!-- Work resumed from the landed 4a Cloud 54b0f1f, API f05e9a0 and Automation ae5cf74 roots; the post-4a source/write-path census was rerun before the final API 8fd1879 and Automation b54595a derivations. -->
- [x] 4.2 Remove B1/B2/B4 payload fields whose only automation consumers moved to 4a API notification/card exits; record the post-4a minimal field inventory.
  <!-- The post-4a inventory retains only B1 persona binding/persona/soul, B2 environment gate/slow-start and B4 account identity/status facts; notification/card-exit-only fields are absent from the automation payloads. -->
- [x] 4.3 **B1 persona:** use existing `persona_config` version, implement the API owner binding/persona/soul snapshot and automation local lookup, and test fresh-complete unbound versus unknown/stale fail-closed.
  <!-- API 8fd1879 publishes complete persona_config-versioned facts and Automation b54595a performs atomic local replacement; tests distinguish a fresh complete unbound value from unknown/stale and stop dispatch on the latter. -->
- [x] 4.4 **B2 environment gate/slow-start:** reuse existing two mirror keys, implement shared owner snapshot plus automation-local read projection, and test missing/unknown/stale blocks Edge push and never means “no slow start”.
  <!-- API 8fd1879 reuses both shared environment mirror keys and Automation b54595a reads only its local projection; missing/unknown/stale blocks Edge push and is never interpreted as no slow start. -->
- [x] 4.5 **B3 freshness runtime:** install the per-process runtime against automation-local mirrors, remove cross-owner ambient implementation imports, and test missing install, stale refusal and monolith local-authority mode.
  <!-- Kernel 0cb83d0 supplies the instantiable runtime; Automation b54595a installs it against local mirrors, rejects missing/stale remote authority and permits explicit local authority only in monolith. -->
- [x] 4.6 **B4 account identity/status:** extend 4a’s `AccountRosterSourcePort` and existing shared `automation_account_projection` only with surviving fields, reuse `account_status` version, and test ambiguity/status unknown/display-only stale semantics.
  <!-- API 8fd1879 extends the 4a roster port with the minimal account_status-versioned identity/status payload and Automation b54595a atomically replaces the shared projection; tests cover ambiguity, unknown status and display-only stale data. -->
- [x] 4.7 **B5 business configs:** implement content schedule, hot-lead, Facebook comment and Facebook join owner snapshots using their existing mirror versions; wire automation local mirrors and test gate/parameter polarity separately.
  <!-- Content c5a90c3 and API 8fd1879 expose four independently versioned owner snapshots; Automation b54595a maintains four local mirrors and separately tests gate booleans versus operational parameters. -->
- [x] 4.8 Audit every post-4a persona/environment/account/config mutation; connect missing paths to the existing owner version key in the same transaction and prove rollback does not advance it, without adding target-scoped business revisions.
  <!-- The final mutation audit connected persona, environment, account and business-config writes to their existing owner revision in the same transaction; rollback tests keep generations unchanged and migrations add no target-scoped business revision. -->

## 5. Composition Roots and Derived Repositories

- [x] 5.1 Wire Cloud monolith explicit local-authority adapters for A1–A6/B1–B5 and prove the branch is unreachable when `AIDCP_SERVICE=api|automation`.
  <!-- Cloud composition tests prove monolith installs explicit local-authority adapters before Edge/publisher activation and that split api/automation modes cannot reach those adapters. Final Cloud regression remains tracked by 8.1. -->
- [x] 5.2 Wire independent api startup/stop/readiness for A1/A3–A6, including required parameter first-load blockers and blocker-level health.
  <!-- API 8fd1879 installs owner listeners before bootstrap, restores checkpoints, performs the first authenticated full load, starts periodic refresh, exposes blocker-level readiness/health and stops its 4b timers/listeners/pool. -->
- [x] 5.3 Wire independent automation startup/stop/readiness for B1–B5 plus A1/A3–A6 publishers, using only owner-local pools and post-4a ports.
  <!-- Automation b54595a wires B1–B5 bootstrap/checkpoints and A1/A3–A6 publishers/change relay using one owner-local pool and post-4a ports; remote-owner pools and ambient implementations are absent. -->
- [x] 5.4 Update kernel/transport members and ownership maps; derive from exact Cloud SHA without overwriting hand-written api/automation roots.
  <!-- Final derived defaults are Kernel 0cb83d0 and Transport ec9dd3d; managed sync updated member/ownership maps while preserving the hand-written API 8fd1879 and Automation b54595a composition roots/tests. -->
- [x] 5.5 Update exact package pins and prove api uses kernel+transport while automation uses kernel plus local owner transport source, with no duplicate transport instance.
  <!-- API 8fd1879 pins Kernel 0cb83d0 plus Transport ec9dd3d; Automation b54595a pins Kernel 0cb83d0 and owns its local transport source. npm dependency checks found no duplicate transport instance. -->
- [x] 5.6 Run managed sync census and strict api/automation composition-root typecheck/tests; any 4a residual must be named rather than hidden by defaults or foreign pools.
  <!-- Managed sync and root tests/typechecks pass; Automation's boundary census is 226/226 with 569 checked imports and zero forbidden edges. Split bootstrap remains blocked by 12 named future Automation blockers and the API Feishu owner WebSocket lacking a close handle; neither is hidden by defaults or a foreign pool. -->

## 6. External DTO and UI Honesty

- [x] 6.1 Extend Cloud summary/lifecycle/config-mirror DTOs with presence evidence, in-flight evidence and per-service delivery state while preserving durable approval precedence and explicit unavailable semantics.
  <!-- Cloud DTO acceptance covers additive presence/in-flight evidence and per-service delivery state, preserves durable approval precedence and represents unavailable explicitly instead of synthesizing zero/fresh. -->
- [x] 6.2 In `aidcp-console`, render dashboard Edge presence fresh-zero separately from unknown/stale/invalid and show per-service config-mirror health without a global-fresh collapse.
  <!-- Console 32bc318 renders fresh zero distinctly from unknown/stale/invalid and presents API/Automation delivery health independently rather than collapsing them into one global freshness flag. -->
- [x] 6.3 In `aidcp-console`, render publish in-flight evidence unavailable for affected items and exclude uncertain records from definite waiting/dispatching/zero summaries.
  <!-- Console 32bc318 marks affected in-flight evidence unavailable and excludes uncertain rows from definite waiting, dispatching and zero aggregates. -->
- [x] 6.4 In `aidcp-edge`, consume the additive lifecycle evidence state and display “下发状态暂不可用” without inferring waiting/dispatching/not-dispatched.
  <!-- Edge a33602d consumes the additive evidence state and renders “下发状态暂不可用”; focused tests prove unavailable is not inferred as waiting, dispatching or not-dispatched. -->
- [x] 6.5 Run Cloud DTO tests, Console focused tests/build and Edge focused tests/typecheck; record that no Edge installer or installed-client/live-account validation was performed.
  <!-- Cloud DTO tests pass; Console 32bc318 passes 54/54 plus typecheck/build, and Edge a33602d passes 111/111 plus typecheck/source build. No Edge installer, installed-client or live-account validation was performed. -->

## 7. Item-by-Item Acceptance

- [x] 7.1 Accept **A1** with source version/write, api consumer, first load, same-cursor renewal, stale and recovery evidence.
  <!-- Accepted in API 8fd1879 and Automation b54595a: transactional source generation, first-load gate, exact cached observation, equal-cursor owner-fetch renewal, stale last-good and authenticated recovery are covered. -->
- [x] 7.2 Accept **A2** with catalog parity, exhaustive platform actions, kernel dist exports and pin-drift failure evidence.
  <!-- Accepted in Kernel 0cb83d0, API 8fd1879 and Automation b54595a: parity/exhaustiveness, dist exports and exact-pin drift failures are covered. -->
- [x] 7.3 Accept **A3** with three-read source/consumer, zero/unknown, heartbeat stale, reconnect and resume-command-exclusion evidence.
  <!-- Accepted: the closed three-read payload, known zero/unknown, heartbeat expiry, reconnect healing and resumeEdgesForAccount exclusion are covered across Automation b54595a and API 8fd1879. -->
- [x] 7.4 Accept **A4** with in-flight source/consumer, durable projection precedence, known-empty/unknown/stale and UI DTO evidence.
  <!-- Accepted: Automation b54595a and API 8fd1879 cover atomic in-flight replacement and durable precedence; Console 32bc318 covers known-empty versus unknown/stale presentation. -->
- [x] 7.5 Accept **A5** with disabled/available/unavailable/unknown, secret exclusion and startup readiness evidence.
  <!-- Accepted: all four capability states, no-secret contracts and required-parameter readiness behavior are covered by Automation b54595a and API 8fd1879. -->
- [x] 7.6 Accept **A6** with api-local/automation-local separation, stale delivery invalidation and Console presentation evidence.
  <!-- Accepted: owner/consumer health remains process-local, stale delivery invalidates the whole automation section, and Console 32bc318 presents per-service evidence. -->
- [x] 7.7 Accept **B1** with shared owner version, atomic consumer replace, unbound/unknown/stale and dispatch stop evidence.
  <!-- Accepted in API 8fd1879 and Automation b54595a: persona_config generation, complete replacement, fresh unbound distinction and unknown/stale dispatch refusal are covered. -->
- [x] 7.8 Accept **B2** with shared fact content, target-isolated instance health, missing/stale fail-closed and no-slow-start non-default evidence.
  <!-- Accepted: shared environment facts are not target-partitioned, consumer health is target-isolated, and missing/stale fails closed without defaulting to no slow start. -->
- [x] 7.9 Accept **B3** with independent per-process installation, no remote ambient call and explicit monolith-only local-authority evidence.
  <!-- Accepted in Kernel 0cb83d0 and Automation b54595a: each process installs its own runtime, remote ambient implementations are absent, and local authority is monolith-only. -->
- [x] 7.10 Accept **B4** with post-4a minimal roster, shared projection payload, target-isolated instance readiness, ambiguity/status/display failure evidence.
  <!-- Accepted in API 8fd1879 and Automation b54595a: the minimal roster and shared projection remain business facts, while readiness is target-local and ambiguity/status/display failures stay explicit. -->
- [x] 7.11 Accept **B5** with four independent config snapshots, existing owner versions, gate/parameter behavior and same-version successful observation evidence.
  <!-- Accepted across Content c5a90c3, API 8fd1879 and Automation b54595a: four independent snapshots reuse owner versions, separate gate/parameter polarity and renew only from a successful later same-version observation. -->
- [x] 7.12 Run cross-cutting invalid/old/duplicate cursor, same-cursor drift, historical replay, incomplete payload, auth, target mismatch and disconnect-backlog tests.
  <!-- Kernel 0cb83d0 and Transport ec9dd3d plus API/Automation focused suites cover invalid/old/duplicate cursors, same-cursor drift, replay, incomplete payload, bearer/target rejection and closed-ACK disconnect backlog recovery. -->

## 8. Integration, Deployment and Closeout

- [x] 8.1 Run Cloud focused/acceptance/full tests, typecheck, protocol/risk/publish suites, boundary census, migration status/verify and diff-check; record exact counts.
  <!-- Cloud 05d6c5a: full test 3684 total / 3673 pass / 0 fail / 11 skip; typecheck PASS; source-owner census 515/515 with zero invalid edges; diff-check PASS. DEV migration status reached content 20/20, automation 49/49 and api 55/55 with zero pending; verify reported zero missing declared objects for all three owner databases. -->
- [x] 8.2 Rebase/integrate repos in dependency order, rerun validations, commit/push exact SHAs and record repo/SHA/evidence comments in this checklist.
  <!-- Pushed defaults: Kernel 0cb83d0f25837e06447bd35cffead3d1a24a098e; Transport ec9dd3d3b8ecd8e14774c4dc827a2a08dbc0ffa7; API 8fd1879d64c9d710b128efb19ef1add05988ddc5; Automation b54595aba4df6598710e2f84bf47533bc466fb63; Content c5a90c3b70d9f5c1fd8d0d7b5728b44ba1840750; Console 32bc3188ddf1ae86705a402e78573ec99921ef00; Edge a33602d71733fc0e01accf298abbee285065038c; Cloud 05d6c5af11c6eee564878ac633500304f8a0310d. Final Automation follow-up preserved 1747 total / 1744 pass / 0 fail / 3 skip plus typecheck/build. -->
- [x] 8.3 Run final `scripts/sync-split-repos --ref <cloud-sha> --tests`; explain only intentional hand-written root/test residuals and block on any managed drift.
  <!-- `AIDCP_CODES_ROOT=/Users/baitianxing/codes ./scripts/sync-split-repos --ref 05d6c5a --tests`: every managed source and test set has zero add/change/extra drift; migrations and exact Kernel/Transport pins align. The command's non-zero status is solely its intentional report-only treatment of the API/Automation/Content hand-written index/server roots plus the registered private Automation root and private derived tests. -->
- [x] 8.4 Deploy the clean eligible Cloud default checkout to DEV monolith and verify service/listeners/health/Feishu/PostgreSQL as monolith regression evidence only.
  <!-- DEV monolith deployed from clean Cloud 05d6c5a after backup `/opt/aidcp/backups/4b-05d6c5a-20260726`. Expand migrations 0082–0087 applied; status/verify and direct object probes pass. Stop-then-start preserved the single writer: service active, NRestarts=0, schema gates pass, writer lock held, 4b mirror ready before :8787, panel :8090 and client-auth :8091 healthy, split :8092 absent, all split units inactive/disabled. Feishu WS reached ready and bot identity is Dev.A; the send probe truthfully remains blocked by the pre-existing chat-membership error 230002. No Edge client/live-account probe was present. -->
- [x] 8.5 After 4a/4b roots are both ready, run DEV split bootstrap, ready blockers, outbox backlog, stale fail-closed, same-cursor renewal, recovery, cursor continuation and target isolation; otherwise record `not_started`.
  <!-- not_started: DEV split bootstrap was not run. Automation still declares 12 future independent-runtime blockers (4 operator-command, 7 content-owner and 1 production-runtime composition), and the inherited API Feishu owner WebSocket has no closable lifecycle handle. DEV remains monolith with no split units/listeners, cross-process soak or target-isolation runtime probe; OL is out of scope. -->
- [ ] 8.6 Update §10 with post-4a inventory, implementation SHAs and source/monolith/split/UI/installer boundaries; strict-validate and archive only after every required item is complete.
