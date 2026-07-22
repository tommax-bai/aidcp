## 1. Cloud platform contract

- [x] 1.1 Add a fully covered scheduled-automation action declaration to the platform registry, including allowed modes and daily caps for every supported platform.
  <!-- aidcp-cloud 94c7a0e: PLATFORM_REGISTRY is fully covered and scheduledAutomation declares truthful modes/caps. -->
- [x] 1.2 Extend the content-schedule catalog with normalized platform and server-authoritative available action projections.
  <!-- aidcp-cloud 94c7a0e: catalog returns platform, groupLabel, and availableActions from the registry. -->
- [x] 1.3 Enforce platform action, mode, and cap validation before account schedule UPSERT while allowing explicit fail-closed cleanup values.
  <!-- aidcp-cloud 94c7a0e: action clusters reject unsupported enable/mode/cap writes and allow false/off/0 cleanup. -->
- [x] 1.4 Add focused Cloud tests for registry coverage, catalog projection, valid writes, unsupported-action rejection, and atomic no-write behavior.
  <!-- aidcp-cloud 94c7a0e: 30 focused tests passed. -->

## 2. Console platform-aware view

- [x] 2.1 Extend Console API types for normalized platform and available automation action metadata.
  <!-- aidcp-console f2e34ce: DTO adds platform, groupLabel, and availableActions. -->
- [x] 2.2 Add the default-all platform selector and derive table rows, counts, empty state, and summaries from one filtered collection.
  <!-- aidcp-console f2e34ce: default-all selector drives filteredRows, count, empty state, and table data. -->
- [x] 2.3 Render a compact cross-platform summary in the all-platform view and server-declared editable action columns in single-platform views.
  <!-- aidcp-console f2e34ce: all view is common summary; single-platform action columns consume allowedModes/maxDailyCap. -->
- [x] 2.4 Add focused Console tests for platform filtering, all-platform summaries, empty action platforms, and dynamic mode/cap limits.
  <!-- aidcp-console f2e34ce: ContentSchedulePage plus enum safety focused run passed 18/18. -->

## 3. Validation and delivery

- [x] 3.1 Run focused Cloud tests and Cloud typecheck; record the exact commands and results.
  <!-- `node --import tsx --test test/platform-registry.test.ts test/content-schedule-store.test.ts test/panel-content-schedule.test.ts` 30/30 pass; `npm run typecheck` pass; `git diff --check` pass. -->
- [x] 3.2 Run focused Console tests and Console typecheck/build; record the exact commands and results.
  <!-- `npm run typecheck` pass; `npm run build` pass (3725 modules, existing chunk-size warning); focused change+enum run 18/18 pass. Default-5s single-worker full run was 227 pass/7 fail/1 skip: one enum safety failure was fixed, six resource-timeout failures all passed bounded 20s reruns (47/47 plus ContentSchedulePage 16/16). Deviation: test-hang diagnosis accidentally terminated workers from aidcp-console.wt/wechat-reply-knowledge-document; no files were changed there and that task must rely on its own rerun. -->
- [x] 3.3 Run `openspec validate platform-aware-account-automation --strict`, integrate the isolated repo branches serially, and record commit SHAs and deviations.
  <!-- strict validation passed. aidcp-cloud 833b160 landed on master after acceptance, full test (2812 pass/0 fail/8 skip), and typecheck. aidcp-console f14eb07 landed on master after full test with bounded 20s timeout (237 pass/0 fail/1 skip), typecheck, and production build. The stock Console land helper's default parallel 5s run failed on 38 resource-timeout tests, so it did not push; the complete single-worker 20s run passed before a manual ff-only push and canonical sync. -->
- [x] 3.4 Deploy the clean integrated Cloud and Console revisions to dev, then verify health, static assets, platform projections, and unsupported-write rejection without mutating production data.
  <!-- Dev only. Cloud platform contract 833b160 is included in deployed master 817469d; Console platform view f14eb07 is included in the live latest-master static assets, whose index and primary JS hashes match the clean local build. Health/listeners/static HTTP passed. The authenticated catalog returned 36 normalized rows and server-declared actions; all 20 Facebook rows declare `join_group`. Validation used read-only projections and existing rejection tests; no business schedule/config row was mutated. -->
