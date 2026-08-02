## 1. Cloud global policy and migration

- [x] 1.1 Add a forward-only Cloud migration for target-global `slow_start_reel_views_per_like`, default `15`, `NOT NULL`, and `1..100` constraint.
- [x] 1.2 Extend Cloud policy types, row mapping, bounds, strict write validation, revisioned persistence, audit snapshot, and read-after-write projection with `reels.slowStart.viewsPerLike`.
- [x] 1.3 Add migration, store, API and account-decision regression coverage for the new required global field, default, bounds, strict rejection, and immutable projections.
  <!-- Cloud commit 93096b1; includes 0107, schema @3, API-owner schema gate, sync-read validator and tests. -->

## 2. Cloud Reel cadence runtime

- [x] 2.1 Authorize Reel cadence likes for `slow_start` as well as `persona`, using the current mode's unique-Reel ordinal and a mode-auditable reason without changing rule or consumption behavior.
- [x] 2.2 Add integration coverage for cold-start N-boundary likes, mode/session isolation, duplicate exclusion, simultaneous like/follow boundaries, and no-debt gate failures.

## 3. Console global editor

- [x] 3.1 Extend Console API types, policy summary, draft validation and write payload with `reels.slowStart.viewsPerLike`.
- [x] 3.2 Add the cold-start Reel like frequency input beside the existing follow frequency while preserving total-days resizing and per-day cap editing.
- [x] 3.3 Add Console tests for load, edit/save, validation, stale revision preservation and the unchanged “copy last day” behavior.
  <!-- Console commit ac0ce49; the global editor keeps the complete slowStart cadence in every CAS write. -->

## 4. Validation and delivery record

- [x] 4.1 Run focused Cloud migration/store/API/runtime tests and focused Console editor/page tests.
- [x] 4.2 Run Cloud acceptance tests, full tests and typecheck; run Console full tests, production build and typecheck with bounded output.
- [x] 4.3 Run `openspec validate add-facebook-slow-start-reel-like-cadence --strict` and record repo commits, validation results, deviations, and the explicit no-deploy/no-package/no-real-account boundary.
  <!-- Focused: Cloud 103/103 and Console 18/18. Final: Cloud acceptance 184/184; Cloud full 4114 passed, 11 skipped; Cloud typecheck passed; Console full 345 passed, 1 skipped; Console build and typecheck passed; OpenSpec strict passed. No design deviations. No DEV/OL deployment, migration application, Edge package, installed-client change or real-account action was performed. -->
