## 1. Cloud Storage and API

- [x] 1.1 Add nullable `region`, `park`, and `direction` columns to `facebook_group_target`, plus indexes for list/facet filters.
  <!-- aidcp-cloud master 1b174dee6f906015277aea9c2f09469946c32e64: added additive target metadata columns and region/park/direction indexes. -->
- [x] 1.2 Extend Facebook group target input/row/list DTOs, import upsert behavior, and metadata normalization.
  <!-- aidcp-cloud master 1b174dee6f906015277aea9c2f09469946c32e64: import now stores canonical group URLs, inserts new rows, and enriches existing rows without touching join state. -->
- [x] 1.3 Extend list filters and add a facets read path for regions, parks, and directions.
  <!-- aidcp-cloud master 1b174dee6f906015277aea9c2f09469946c32e64: listTargets accepts metadata filters; listFacets returns regions with nested parks and directions. -->
- [x] 1.4 Extend panel API validation for metadata-bearing import items and optional filter query params.
  <!-- aidcp-cloud master 1b174dee6f906015277aea9c2f09469946c32e64: /api/facebook/groups accepts region/park/direction; import items accept optional metadata; /facets added. -->
- [x] 1.5 Add focused cloud tests for URL canonicalization, metadata import/upsert, list filters, facets, and panel API validation.
  <!-- Validation: npm test completed 1707 passing tests; npm run typecheck passed. -->

## 2. Console Import and Filters

- [x] 2.1 Add a paste parser that supports URL-only text and wide spreadsheet/tab-separated data with region, park, and direction inference.
  <!-- aidcp-console master 94e59d687dccf05e51e5c2488a32f76791d1dc1e: added facebookGroupImportParser with URL-only and wide TSV coverage. -->
- [x] 2.2 Extend API types and import payloads to send metadata-bearing items.
  <!-- aidcp-console master 94e59d687dccf05e51e5c2488a32f76791d1dc1e: group DTOs include metadata and import sends structured items. -->
- [x] 2.3 Add optional region, park, and direction filters to the Facebook groups page, with park options scoped by selected region.
  <!-- aidcp-console master 94e59d687dccf05e51e5c2488a32f76791d1dc1e: added region/park/direction Select controls; clearing region clears park. -->
- [x] 2.4 Display metadata in the group table without replacing the canonical copyable group URL.
  <!-- aidcp-console master 94e59d687dccf05e51e5c2488a32f76791d1dc1e: classification tags display beside existing canonical group path. -->
- [x] 2.5 Add focused console tests for paste parsing and filter payload construction.
  <!-- Validation: parser/query focused tests passed; npm run typecheck passed; npm test passed 74 tests with 1 skipped; npm run build passed. -->

## 3. Validation and Delivery

- [x] 3.1 Run focused cloud tests and `npm run typecheck` in `aidcp-cloud`.
  <!-- Validation: pre-rebase npm test ran full suite because the package script includes test/**/*.test.ts: 1707 pass, 0 fail. After rebase: npx tsx --test test/comment-agent/facebook-group-store.test.ts test/panel-server.test.ts passed 28 tests; npm run typecheck pass. -->
- [x] 3.2 Run focused console tests and `npm run typecheck` in `aidcp-console`.
  <!-- Validation: npm test pass 74 tests with 1 skipped before rebase. After rebase: npm test -- src/pages/facebookGroupImportParser.test.ts src/pages/facebookGroupsQuery.test.ts pass; npm run typecheck pass; npm run build pass. -->
- [x] 3.3 Run `openspec validate facebook-group-target-filters --strict`.
  <!-- Validation: passed before implementation; final validation rerun after task update. -->
- [ ] 3.4 Commit and push the control, cloud, and console branches.
- [ ] 3.5 Deploy/publish to dev after validation, or record why deployment was intentionally skipped.
