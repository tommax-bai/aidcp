## 1. Browser Control Completion

- [x] 1.1 Extend correlated browser control replies so `browser.park` confirms configured parking success/failure while uncorrelated reset paths remain compatible.
- [x] 1.2 Generalize Electron main pending control requests for correlated show and park, including timeout and exact-environment reply validation.

## 2. Exclusive Recall Orchestration

- [x] 2.1 Add a main-process exclusive recall operation that snapshots controllable non-target handles, parks them in parallel, then shows the exact target behind AIDCP.
- [x] 2.2 Serialize recall operations, coalesce stale queued requests, and return distinct target failure, superseded, and partial-parking results.
- [x] 2.3 Expose the targeted exclusive-recall IPC through preload without changing guided login or explicit recovery behavior.

## 3. Environment Rail Interaction

- [x] 3.1 Change environment-row single-click to selection-only and bind avatar double-click to one exclusive recall regardless of prior selection.
- [x] 3.2 Keep repeated target double-click idempotent, preserve nickname/persona gesture isolation, and project partial/superseded/failure results honestly.

## 4. Regression Coverage

- [x] 4.1 Add core tests for correlated park completion, failure, and legacy uncorrelated behavior.
- [x] 4.2 Add main-process tests for per-environment park fan-out, target-last ordering, partial failures, and latest-request-wins serialization.
- [x] 4.3 Update renderer tests for single-click selection, direct double-click switching from another environment, repeated target double-click, and stale result suppression.

## 5. Validation and Delivery

- [x] 5.1 Run focused Electron renderer/main/core tests and fix regressions.
  <!-- Edge focused core/main/renderer coverage: 115/115 passed; coordinator 5/5, renderer smoke 103/103, companion UI 84/84, and nickname IPC 4/4 passed. -->
- [x] 5.2 Run Edge acceptance, full tests, typecheck, diff check, and `openspec validate exclusive-browser-window-switching --strict`.
  <!-- Acceptance: 38/38 passed with 1 gated E2E skip. Typecheck, diff check, and strict OpenSpec validation passed. Full `npm test` was rerun after scoped fixes and reached only the pre-existing `facebook_auth_start_ad_data_review` Native postcondition inventory failure; the same targeted failure reproduces on the unmodified Edge `master` at dfb57f1. -->
- [ ] 5.3 Record repo/commit/validation evidence, commit and push the isolated control/Edge branches, then serially integrate eligible default branches without packaging or deployment.
  <!-- Edge implementation commit: aidcp-edge@9f27da5. Default-branch integration remains gated by the unrelated full-suite baseline failure; no package, installation, or deployment is in scope. -->
