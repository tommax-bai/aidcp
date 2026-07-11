## 1. CSV Import Utility

- [x] 1.1 Add a typed CSV parser for the group import template, including BOM, quoted-field, header-alias, optional-field, empty-row, and size-validation behavior.
- [x] 1.2 Add the UTF-8 BOM-prefixed, header-only CSV template generator and browser download helper.
- [x] 1.3 Add focused unit tests for valid rows, optional cells, quoting, BOM/CRLF, bad headers, and template contents.
  <!-- aidcp-console codex/facebook-group-import-modes: facebookGroupCsvImport covers CSV grammar, aliases, validation, and the header-only template. Focused tests: 6 passed; typecheck passed. -->

## 2. Console Workflow

- [x] 2.1 Replace the shared paste box with explicit single-group and CSV file modes.
- [x] 2.2 Implement single-group URL submission with optional cascading region/park and direction selectors.
- [x] 2.3 Implement CSV selection, local validation, parsed-row feedback, file removal, template download, and structured import submission.
- [x] 2.4 Add focused page tests for mode switching, single add payloads, CSV import guards, and template download interaction.
  <!-- aidcp-console codex/facebook-group-import-modes: added FacebookGroupImportPanel and integrated it with the existing structured import mutation. Focused parser/component tests: 11 passed; typecheck passed. -->

## 3. Validation and Delivery

- [x] 3.1 Run focused console tests, the full console test suite, `npm run typecheck`, and `npm run build`.
  <!-- Validation before integration: focused tests 11 passed; full suite 87 passed with 1 skipped; typecheck passed; production build passed. Existing jsdom and chunk-size warnings were non-fatal. -->
- [x] 3.2 Run `openspec validate facebook-group-import-modes --strict`.
  <!-- Validation: Change 'facebook-group-import-modes' is valid. -->
- [x] 3.3 Commit and push the control and console changes, then fast-forward the console default branch.
  <!-- Delivery: aidcp-console master 7deb077abedaa490ef38763e54c35c961357c99c contains the implementation and was pushed by fast-forward; aidcp main eb291b7172b3dcc380bc061f4d53704965890d99 records the validated change artifacts before deployment. -->
- [x] 3.4 Publish console static assets to `dev` and verify the two modes and template control in the deployed page.
  <!-- Dev deploy 20260710-114932: scripts/deploy-target dev --check passed for 121.89.85.150; backed up /opt/aidcp/console to /opt/aidcp/console.bak.20260710-114932.tar.gz; rsync --delete published aidcp-console master dist. Verification: console HTTP 200, panel /api/health ok, aidcp-cloud.service active, and deployed JS contains 单条添加 and 下载 CSV 模板. In-app browser reached the normal login guard but had no authenticated session, so post-login visual inspection was not performed; focused component interaction tests remain the UI behavior evidence. -->
