## 1. Cloud atomic reset

- [x] 1.1 Update the admin persona clear storage path to atomically delete the target account's `persona_config` and `first_post_onboarding` rows, then clear the in-memory persona mirror only after database success.
  <!-- Cloud: PersonaStore.clear uses one data-modifying CTE for both target rows and mutates cache only after query success. -->
- [x] 1.2 Keep non-empty persona updates, customer persona persistence, automatic persona fill, publish data, curated content, risk state, and account master data unchanged.
  <!-- Scope is limited to the existing admin empty-persona clear method; non-empty set/setIfMissing and all unrelated tables are untouched. -->

## 2. Regression coverage

- [x] 2.1 Add PersonaStore regressions proving admin clear removes both rows and a database failure preserves the persona row and in-memory mirror without partial success.
  <!-- persona-store tests cover both-row reset, cache ordering, and injected reset failure preserving both DB projections plus the cache. -->
- [x] 2.2 Add facade/acceptance coverage proving the backend still returns `source=none`, does not fire the bind callback on clear, and the next successful persona bind can create `firstPostOnboarding:true` again while ordinary updates remain idempotent.
  <!-- AccountPersonaService/facade regression covers clear -> no onBound -> true once on rebind -> false on update; focused persona/onboarding/acceptance run passed 38/38. -->

## 3. Validation and delivery

- [x] 3.1 Run focused Cloud persona/onboarding tests, the relevant acceptance suite, full Cloud tests, and `npm run typecheck`.
  <!-- Cloud: focused persona/onboarding/acceptance 38/38; acceptance 63/63; full 2714 pass / 0 fail / 8 explicit gated skips; typecheck passed. -->
- [x] 3.2 Run `openspec validate admin-persona-clear-resets-onboarding --strict` and record concise validation evidence and deviations in this task file.
  <!-- Strict OpenSpec validation passed. No Console/Edge code or schema migration was needed; no real account was cleared and no platform write was performed. -->
- [ ] 3.3 Commit the Cloud and control-repo changes, rebase and fast-forward them onto the latest default branches, rerun required validation, and push both defaults without force.
- [ ] 3.4 Deploy the clean Cloud `master` result to dev and verify the named service, listeners, health endpoint, PostgreSQL, and unrelated isales service boundary without clearing another real account or performing platform writes.
