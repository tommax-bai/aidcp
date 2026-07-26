## 1. Admission, Inventory and 4a Barrier

- [ ] 1.1 Run control preflight; create isolated worktrees/branches for every owning repo and preserve canonical/unrelated files.
- [ ] 1.2 Add a machine-readable A1–A6/B1–B5 inventory with current call sites, owner, consumer, fact scope, local shape, freshness tier and derived members.
- [ ] 1.3 Add a census that rejects unregistered synchronous cross-owner reads and separately rejects side-effect methods in snapshot members.
- [ ] 1.4 Assert A3 contains only `edgeCount`, `onlineEdgeCount` and `resolveEdgeIdForAccount`; verify 4a owns authenticated/idempotent/result-unknown `resumeEdgesForAccount`.
- [ ] 1.5 Publish a hotspot ownership map: common envelope/kernel/local runtime MAY proceed in parallel; B1/B2/B4 owner mutations, roster/projection and `server.ts` remain blocked until 4a lands.

## 2. Parallel Common Contracts and Runtime

- [ ] 2.1 Define kernel `SyncReadStream`, `factScope`, versioned snapshot envelope, unsigned opaque cursor and exhaustive payload/readiness/health unions.
- [ ] 2.2 Implement the shared atomic snapshot apply state machine with payload digest, per-instance target cursor, old-cursor rejection and invalid-envelope handling.
- [ ] 2.3 Implement/test equal-cursor freshness renewal: only a newly fetched, later-`asOf`, digest-identical owner observation renews; historical replay or same-cursor drift does not.
- [ ] 2.4 Extract an instantiable per-process config-freshness runtime; missing source is stale/not-ready in split mode and explicit local-authority is allowed only in monolith.
- [ ] 2.5 Implement authenticated internal snapshot route/client primitives with server-injected target, fact-scope validation and no caller-selected target.
- [ ] 2.6 If persistence is required, add expand-only tables solely for target-scoped consumer cursor/readiness/health; do not target-partition shared facts, owner versions or projection payloads.
- [ ] 2.7 Validate common Cloud tests/typecheck, kernel admission/build/dist and transport route/client/auth/target tests before any composition-root wiring.

## 3. Automation-to-API Inventory Items

- [ ] 3.1 **A1 week mask:** implement automation `session_config_global` full snapshot using the existing shared config version/bump; wire the api local scalar mirror and test first-load failure, stale last-good and equal-version renewal.
- [ ] 3.2 **A2 scheduled catalog:** move the compile-time catalog and three pure reader methods into kernel, wire api/automation to the same artifact, and test export/pin drift without HTTP or projection storage.
- [ ] 3.3 **A3 Edge presence:** implement a target-scoped snapshot/outbox signal for the three pure reads, wire api count/account→edge mirror, and test zero versus unknown/stale, heartbeat expiry and reconnect healing.
- [ ] 3.4 **A3 command exclusion:** add source/contract guards proving no presence payload/adapter invokes `resumeEdgesForAccount`; run 4a command tests for target/auth/idempotency/response-loss `result_unknown`.
- [ ] 3.5 **A4 publish in-flight:** snapshot the dispatcher recordId set, wire api atomic set/evidence-state projection, and test empty-known versus unknown/stale plus durable approval projection precedence.
- [ ] 3.6 **A5 captcha availability:** snapshot `disabled|available|unavailable|unknown`, wire api startup capability state, and test enabled-but-misconfigured, source loss and explicit disabled without copying secrets.
- [ ] 3.7 **A6 mirror health:** snapshot automation-local health with source `asOf`, combine it with api-local health, and test stale delivery invalidates the whole automation section rather than preserving old `fresh`.
- [ ] 3.8 For A3–A6, emit/coalesce target-scoped `sync_read.changed` outbox signals and test that failed snapshot apply holds topic cursor while periodic full snapshots heal missed notifications.

## 4. Post-4a API-to-Automation Inventory Items

- [ ] 4.1 After 4a lands, rebase onto its exact default SHA and rerun the call-site/write-path census before editing roster, persona/environment/account mutations, projection schema or composition roots.
- [ ] 4.2 Remove B1/B2/B4 payload fields whose only automation consumers moved to 4a API notification/card exits; record the post-4a minimal field inventory.
- [ ] 4.3 **B1 persona:** use existing `persona_config` version, implement the API owner binding/persona/soul snapshot and automation local lookup, and test fresh-complete unbound versus unknown/stale fail-closed.
- [ ] 4.4 **B2 environment gate/slow-start:** reuse existing two mirror keys, implement shared owner snapshot plus automation-local read projection, and test missing/unknown/stale blocks Edge push and never means “no slow start”.
- [ ] 4.5 **B3 freshness runtime:** install the per-process runtime against automation-local mirrors, remove cross-owner ambient implementation imports, and test missing install, stale refusal and monolith local-authority mode.
- [ ] 4.6 **B4 account identity/status:** extend 4a’s `AccountRosterSourcePort` and existing shared `automation_account_projection` only with surviving fields, reuse `account_status` version, and test ambiguity/status unknown/display-only stale semantics.
- [ ] 4.7 **B5 business configs:** implement content schedule, hot-lead, Facebook comment and Facebook join owner snapshots using their existing mirror versions; wire automation local mirrors and test gate/parameter polarity separately.
- [ ] 4.8 Audit every post-4a persona/environment/account/config mutation; connect missing paths to the existing owner version key in the same transaction and prove rollback does not advance it, without adding target-scoped business revisions.

## 5. Composition Roots and Derived Repositories

- [ ] 5.1 Wire Cloud monolith explicit local-authority adapters for A1–A6/B1–B5 and prove the branch is unreachable when `AIDCP_SERVICE=api|automation`.
- [ ] 5.2 Wire independent api startup/stop/readiness for A1/A3–A6, including required parameter first-load blockers and blocker-level health.
- [ ] 5.3 Wire independent automation startup/stop/readiness for B1–B5 plus A1/A3–A6 publishers, using only owner-local pools and post-4a ports.
- [ ] 5.4 Update kernel/transport members and ownership maps; derive from exact Cloud SHA without overwriting hand-written api/automation roots.
- [ ] 5.5 Update exact package pins and prove api uses kernel+transport while automation uses kernel plus local owner transport source, with no duplicate transport instance.
- [ ] 5.6 Run managed sync census and strict api/automation composition-root typecheck/tests; any 4a residual must be named rather than hidden by defaults or foreign pools.

## 6. External DTO and UI Honesty

- [ ] 6.1 Extend Cloud summary/lifecycle/config-mirror DTOs with presence evidence, in-flight evidence and per-service delivery state while preserving durable approval precedence and explicit unavailable semantics.
- [ ] 6.2 In `aidcp-console`, render dashboard Edge presence fresh-zero separately from unknown/stale/invalid and show per-service config-mirror health without a global-fresh collapse.
- [ ] 6.3 In `aidcp-console`, render publish in-flight evidence unavailable for affected items and exclude uncertain records from definite waiting/dispatching/zero summaries.
- [ ] 6.4 In `aidcp-edge`, consume the additive lifecycle evidence state and display “下发状态暂不可用” without inferring waiting/dispatching/not-dispatched.
- [ ] 6.5 Run Cloud DTO tests, Console focused tests/build and Edge focused tests/typecheck; record that no Edge installer or installed-client/live-account validation was performed.

## 7. Item-by-Item Acceptance

- [ ] 7.1 Accept **A1** with source version/write, api consumer, first load, same-cursor renewal, stale and recovery evidence.
- [ ] 7.2 Accept **A2** with catalog parity, exhaustive platform actions, kernel dist exports and pin-drift failure evidence.
- [ ] 7.3 Accept **A3** with three-read source/consumer, zero/unknown, heartbeat stale, reconnect and resume-command-exclusion evidence.
- [ ] 7.4 Accept **A4** with in-flight source/consumer, durable projection precedence, known-empty/unknown/stale and UI DTO evidence.
- [ ] 7.5 Accept **A5** with disabled/available/unavailable/unknown, secret exclusion and startup readiness evidence.
- [ ] 7.6 Accept **A6** with api-local/automation-local separation, stale delivery invalidation and Console presentation evidence.
- [ ] 7.7 Accept **B1** with shared owner version, atomic consumer replace, unbound/unknown/stale and dispatch stop evidence.
- [ ] 7.8 Accept **B2** with shared fact content, target-isolated instance health, missing/stale fail-closed and no-slow-start non-default evidence.
- [ ] 7.9 Accept **B3** with independent per-process installation, no remote ambient call and explicit monolith-only local-authority evidence.
- [ ] 7.10 Accept **B4** with post-4a minimal roster, shared projection payload, target-isolated instance readiness, ambiguity/status/display failure evidence.
- [ ] 7.11 Accept **B5** with four independent config snapshots, existing owner versions, gate/parameter behavior and same-version successful observation evidence.
- [ ] 7.12 Run cross-cutting invalid/old/duplicate cursor, same-cursor drift, historical replay, incomplete payload, auth, target mismatch and disconnect-backlog tests.

## 8. Integration, Deployment and Closeout

- [ ] 8.1 Run Cloud focused/acceptance/full tests, typecheck, protocol/risk/publish suites, boundary census, migration status/verify and diff-check; record exact counts.
- [ ] 8.2 Rebase/integrate repos in dependency order, rerun validations, commit/push exact SHAs and record repo/SHA/evidence comments in this checklist.
- [ ] 8.3 Run final `scripts/sync-split-repos --ref <cloud-sha> --tests`; explain only intentional hand-written root/test residuals and block on any managed drift.
- [ ] 8.4 Deploy the clean eligible Cloud default checkout to DEV monolith and verify service/listeners/health/Feishu/PostgreSQL as monolith regression evidence only.
- [ ] 8.5 After 4a/4b roots are both ready, run DEV split bootstrap, ready blockers, outbox backlog, stale fail-closed, same-cursor renewal, recovery, cursor continuation and target isolation; otherwise record `not_started`.
- [ ] 8.6 Update §10 with post-4a inventory, implementation SHAs and source/monolith/split/UI/installer boundaries; strict-validate and archive only after every required item is complete.
