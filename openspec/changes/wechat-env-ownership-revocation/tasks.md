## 1. Contract and data invariants

- [x] 1.1 Validate the proposal, design and `client-customer-auth` delta against the active WeChat interaction/offboarding contract and record any dependency or deviation.
- [x] 1.2 Add the Cloud durable cleanup-hold schema, active env uniqueness/assignment guard, minimal receipt types and repeatable schema checks.

## 2. Cloud revocation lifecycle

- [x] 2.1 Refactor admin scope removal and customer disable transactions so ownership is revoked atomically, exact bindings create existing offboards, and missing bindings create idempotent cleanup holds.
- [x] 2.2 Block reassignment and interaction sync/write while cleanup is unresolved; reconcile late bindings into exact existing offboards under the shared env advisory lock.
- [x] 2.3 Extend internal client-user/environment APIs with truthful additive cleanup receipts and stable cleanup-in-progress errors without changing customer self-delete or protocol v2 envelopes.
- [x] 2.4 Add focused unit and PostgreSQL integration coverage for bound/missing-binding/mixed revocation, retries, concurrency, late binding, reassignment gates and customer self-delete non-regression.

## 3. Console truthfulness

- [x] 3.1 Mirror the internal cleanup receipt/environment summary types and preserve them through scope and customer-status mutations.
- [x] 3.2 Show distinct “ownership revoked, Edge cleanup pending” and “ownership revoked, cleanup binding missing” results/badges while refreshing the authoritative user scope.
- [x] 3.3 Add focused Console tests for successful removal with cleanup warnings, stale response isolation and cleanup-in-progress conflicts.

## 4. Validation and delivery

- [x] 4.1 Run required focused acceptance tests, full owning-repo tests where the risk area requires them, Cloud/Console typecheck or build, and `openspec validate wechat-env-ownership-revocation --strict`.
  <!-- Validation: Cloud feature commit `60acb895600f2ec6993c5f4affcedafd990573ed`; focused ownership tests passed, isolated PostgreSQL 15 integration passed 4/4, post-integration full suite passed 2389/2396 with 7 gated skips and 0 failures, and `npm run typecheck` passed. Console commit `643aad5fb49d0f4e47fa26a48e419c7882ed9176`; focused tests passed 20/20, serialized full suite passed 159 with 1 existing skip and 0 failures, and production build passed. The first parallel Console full run exposed three existing jsdom timing failures; the required serialized rerun was green. Control validation: `openspec validate wechat-env-ownership-revocation --strict` passed. -->
- [x] 4.2 Update this task ledger with owning repos, commits, validation evidence, deployment result and honest remaining manual/live boundaries.
  <!-- Boundary: no real customer environment was revoked or rebound for validation. Runtime verification was non-destructive: the dev database contains the revocation-hold table and one active assignment-guard trigger, with zero live holds at verification time. Customer self-delete behavior and protocol v2 were intentionally unchanged. -->
- [x] 4.3 Rebase and integrate clean sibling worktrees, push eligible default branches, and deploy Cloud/Console runtime changes to `dev` after `scripts/deploy-target dev --check`; do not build an Edge installer.
  <!-- Delivery: Cloud `master` contains the feature at `60acb89` and was deployed from current dev snapshot `c2f25c8bd598f1424e736fc017d57cb90600c3b6`; Console `master` was deployed at `643aad5fb49d0f4e47fa26a48e419c7882ed9176`. `scripts/deploy-target dev --check` passed. Remote backups use stamp `20260717-140035`. Cloud content was already checksum-identical after a concurrent eligible deployment, so it was not overwritten or redundantly restarted; Console updated only `index.html` and the new JS bundle without deletion. Cloud, Console and Edge health passed, PostgreSQL and Feishu WS readiness passed, and the four running isales services were unchanged. No Edge code or installer was produced. -->
