## 1. Cloud group scope data model

- [x] 1.1 Add additive target-scope schema, types, normalization, and target-store transaction methods for list/filter/bulk replace.
- [x] 1.2 Extend group import with optional request-level account-group scopes while preserving mappings when the field is absent.
- [x] 1.3 Make pooled candidate claim resolve the account's current Facebook group label and retain the global one-group-one-account atomic lock.
- [x] 1.4 Revalidate unfinished scoped assignments before actuation, release mismatches safely, and preserve terminal/joined membership facts.
- [x] 1.5 Add focused store concurrency and eligibility tests for multi-scope, ungrouped, no-fallback, global-lock, stale-reclaim, and scope-change cases.
  <!-- aidcp-cloud 1ef8549d1f513a645a073470762b631abef37a0d: additive scope store, scoped atomic claim, pre-actuation revalidation, and focused coverage. -->

## 2. Cloud automatic join action

- [x] 2.1 Add the per-account Facebook join automation config store with default-off switch, bounded daily cap, optional week mask, and truthful write results.
- [x] 2.2 Add join trigger source to the audit ledger and provide latest-scheduled-result reads without inferring old/manual rows.
- [x] 2.3 Extend the platform scheduled-automation registry and content-schedule catalog projection with Facebook `join_group` config, effective limits, scope readiness, and recent result.
- [x] 2.4 Gate the existing content scheduler join action by account config, effective intersected window, operator/risk daily caps, session budget, kill switch, and scoped candidates without adding another timer.
- [x] 2.5 Extend panel read/write endpoints for group scope filters/facets/bulk replacement/import and per-account join configuration with atomic validation.
- [x] 2.6 Add focused Cloud tests for schedule windows, default-off, caps, kill switch, audit source/result, panel contracts, and non-Facebook rejection.
  <!-- aidcp-cloud 1ef8549d1f513a645a073470762b631abef37a0d: 96 core focused + 2 panel contract tests pass; typecheck and diff-check pass. Full test is recorded under 4.1. -->

## 3. Console management surfaces

- [x] 3.1 Extend Facebook group and account-automation API types/queries for scopes, scope facets, join config, effective cap, readiness, and recent result.
  <!-- aidcp-console dec70481373f7702240cc41bc3830996b7e45f5e: Cloud-frozen DTO types and exact group query filter. -->
- [x] 3.2 Add account-group filter/tags, import scope multi-select, no-scope warnings, and selected-row bulk scope replacement to the Facebook groups page.
  <!-- aidcp-console dec70481373f7702240cc41bc3830996b7e45f5e: omit/replace/clear import semantics plus bulk scope UI. -->
- [x] 3.3 Render the server-declared Facebook `join_group` action in the account automation page with switch, daily cap, inherited/custom week mask, effective cap, readiness, and recent result.
  <!-- aidcp-console dec70481373f7702240cc41bc3830996b7e45f5e: dedicated join endpoint; no client-side platform inference. -->
- [x] 3.4 Add focused Console tests for mapping/filter/import/bulk writes and Facebook join action editing/result display without affecting other platforms.
  <!-- Focused: 4 files / 31 tests pass. Full single-worker: 36 files, 245 pass, 1 skip. Typecheck/build pass; existing >500 KiB chunk warning only. -->

## 4. Validation and delivery

- [x] 4.1 Run focused and full required Cloud tests plus typecheck; run focused Console tests plus typecheck/build and record exact results.
  <!-- Cloud final master: acceptance 68/68; full single-concurrency 2,861 pass / 0 fail / 8 skip; typecheck pass. The scoped-join focused run before integration was 96 core + 2 panel; the post-integration catalog-pressure hotfix added two focused tests and bounded RiskController projection concurrency at 2. Console: focused 31/31; full single-worker 245 pass / 0 fail / 1 skip; typecheck/build pass (existing >500 KiB chunk warning only). -->
- [x] 4.2 Run `openspec validate facebook-group-scoped-auto-join --strict`, integrate isolated branches serially, and record repo commit SHAs and deviations.
  <!-- Strict validation passed. Integrated serially: aidcp-cloud initial implementation 1ef8549d1f513a645a073470762b631abef37a0d and final cold-start-safe master 817469dabb7c2458a0a9759bb2ab1f314cc5b79e; aidcp-console dec70481373f7702240cc41bc3830996b7e45f5e. Deviation: Console validation initially left same-worktree vitest workers; exact cwd was verified before terminating only those workers, then the full suite was rerun single-worker and passed. The first dev cold-catalog probe exposed an O(accounts) PostgreSQL connection burst; the final Cloud commit batches scope/audit reads and limits risk projection concurrency, then passed full validation and a fresh cold-start probe. -->
- [x] 4.3 Deploy clean integrated Cloud and Console revisions to dev only, verify schema/health/static assets/read projections, then perform a bounded default-off/scoped dry validation without bulk-mapping existing business targets.
  <!-- Dev only. Cloud 817469d deployed from clean master after backup `/opt/aidcp/backups/deploy-20260722-160822-fb-auto-join-hotfix`; source hash matched. Console live assets matched the latest clean master build and include dec7048. Fresh restart first `/api/content-schedule` returned 200: 36 rows, 20 Facebook rows, all declare `join_group` and expose its view, enabled=0, scope-ready=0, connection-slot errors=0. Scope/config tables and audit source column exist; 1,864 existing targets remain unmapped, scope rows=0, config rows=0. Group facets/list endpoints, health, four listeners, Console HTTP, and unrelated isales services passed; no bulk mapping or automation enablement was performed. -->
