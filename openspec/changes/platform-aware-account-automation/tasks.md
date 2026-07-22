## 1. Cloud platform contract

- [ ] 1.1 Add a fully covered scheduled-automation action declaration to the platform registry, including allowed modes and daily caps for every supported platform.
- [ ] 1.2 Extend the content-schedule catalog with normalized platform and server-authoritative available action projections.
- [ ] 1.3 Enforce platform action, mode, and cap validation before account schedule UPSERT while allowing explicit fail-closed cleanup values.
- [ ] 1.4 Add focused Cloud tests for registry coverage, catalog projection, valid writes, unsupported-action rejection, and atomic no-write behavior.

## 2. Console platform-aware view

- [ ] 2.1 Extend Console API types for normalized platform and available automation action metadata.
- [ ] 2.2 Add the default-all platform selector and derive table rows, counts, empty state, and summaries from one filtered collection.
- [ ] 2.3 Render a compact cross-platform summary in the all-platform view and server-declared editable action columns in single-platform views.
- [ ] 2.4 Add focused Console tests for platform filtering, all-platform summaries, empty action platforms, and dynamic mode/cap limits.

## 3. Validation and delivery

- [ ] 3.1 Run focused Cloud tests and Cloud typecheck; record the exact commands and results.
- [ ] 3.2 Run focused Console tests and Console typecheck/build; record the exact commands and results.
- [ ] 3.3 Run `openspec validate platform-aware-account-automation --strict`, integrate the isolated repo branches serially, and record commit SHAs and deviations.
- [ ] 3.4 Deploy the clean integrated Cloud and Console revisions to dev, then verify health, static assets, platform projections, and unsupported-write rejection without mutating production data.
