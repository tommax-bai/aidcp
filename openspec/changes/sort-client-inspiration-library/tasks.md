## 1. Cloud customer sorting contract

- [x] 1.1 Add the typed client sort enum and fixed stable SQL ordering to `CuratedContentStore.listForClient`, including weighted bigint math and honest NULL placement without a schema column.
- [x] 1.2 Parse and validate the customer-auth `sort` query, default it to weighted, and pass only the allowlisted value into the account-scoped store query.
- [x] 1.3 Add focused Store and customer-auth regressions for all four sorts, formula/tie/null behavior, pagination-before-limit, default compatibility, account isolation, and invalid-sort rejection.
  <!-- Cloud focused Store + customer-auth: 93/93 pass. -->

## 2. Edge authenticated bridge

- [x] 2.1 Extend the `curated:list` main-process handler to accept only the four sort values and encode the selected value into the fixed customer-auth path.
- [x] 2.2 Extend IPC/security regressions to prove the renderer cannot submit arbitrary fields, directions, URLs, envKeys, account ids, or tokens.
  <!-- Edge IPC/security focused: 9/9 pass; main.cjs syntax check pass. -->

## 3. Customer inspiration-library interaction

- [x] 3.1 Add the right-aligned secondary sort control, formula/snapshot explanation, responsive toolbar layout, quiet loading treatment, and accessible menu states to the existing content workspace DOM/CSS.
- [x] 3.2 Add per-environment sort state, weighted default, first-page reset, server request wiring, keyboard/outside-close behavior, stale-response protection, confirmed-list preservation, and failure rollback to the renderer controller.
- [x] 3.3 Add focused renderer regressions for placement, responsive structure, option labels/formula, server request values, state restoration, account switches, loading preservation, failure rollback, and keyboard accessibility.
  <!-- Edge focused content/security: 32/32 pass; renderer/main syntax pass. Browser visual QA passed at 900x720 and 640x720; same-page header grid truncation found and fixed. -->

## 4. Validation and integration

- [x] 4.1 Run focused Cloud tests, full Cloud tests, acceptance, and typecheck; record exact results and any unrelated flakes.
  <!-- Cloud focused Store + customer-auth 93/93 pass; full suite 2,751 pass + 8 skipped / 0 fail (2,759 total); acceptance 64/64 pass; `npm run typecheck` pass. -->
- [x] 4.2 Run focused Edge tests, full Edge tests, acceptance, typecheck, and syntax checks without packaging; record exact results and any unrelated flakes.
  <!-- Edge focused content/security 32/32 pass; full suite 2,131/2,131 pass; acceptance 28/28 pass; `npm run typecheck` pass; renderer/main syntax checks pass; no package/installer built. The first full run exposed two interaction-workspace regressions because the new hidden sort options reused `aria-selected`; changing the sort menu to the accurate `menuitemradio` + `aria-checked` semantics fixed both, and the final full rerun was green. -->
- [x] 4.3 Run `openspec validate sort-client-inspiration-library --strict`, update this checklist with commits and validation evidence, and push the isolated feature branches.
  <!-- Cloud commit `de163dd` and Edge commit `c1d5b1c` pushed to `origin/codex/sort-client-inspiration-library`; strict OpenSpec validation passed before control-repo commit. -->
- [x] 4.4 Merge the latest default branches into the feature branches, resolve any serial overlap with source-published-time work, rerun required gates, then fast-forward and push the default branches without force operations.
  <!-- Merged current defaults including `normalize-source-published-time` without conflict. Post-merge Cloud: focused 97/97, full 2,765 pass + 8 skipped / 0 fail (2,773 total), acceptance 64/64, typecheck pass; integrated `ddda894` to `master`. Post-merge Edge: focused 34/34, full 2,133/2,133, acceptance 28/28, typecheck + syntax pass; integrated `78a5f79` to `master`. No force operations used. -->
- [x] 4.5 Run the `dev` target guard, back up the current Cloud runtime, deploy only the clean integrated Cloud default branch, and verify service, listeners, health, Feishu, PostgreSQL, authenticated sort behavior, and unrelated `isales` services.
  <!-- `scripts/deploy-target dev --check` passed. Backups: `/opt/aidcp/backups/cloud-pre-sort-client-inspiration-library-20260721-155055.tar.gz` and `/opt/aidcp/backups/cloud-env-pre-sort-client-inspiration-library-20260721-155055`. Deployed clean Cloud `master` at `ddda894` with no package/lockfile or migration delta; remote Store SHA-256 `c380eb22ff8835df2bc61dec5f5d7f04e4564c9f46fbd1f51294dea230ad9455`. Only `aidcp-cloud.service` restarted. Verified active service; 8787/8090/8091/8088/5432 listeners; internal/public health 200; PostgreSQL `select 1`; Feishu bot `Dev.A`, WS ready; all four existing isales services active. Authenticated customer sort smoke passed weighted/collects/likes/recent with 20/173 rows and correct primary order, invalid sort returned 400 `invalid_sort`, and public `/capi` weighted smoke returned 200. -->
