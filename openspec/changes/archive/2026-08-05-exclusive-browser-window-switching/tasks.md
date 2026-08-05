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
  <!-- After rebasing onto Edge master@52cd8d9, full `npm test` passed 3036/3036 with 1 gated skip; Acceptance passed 38/38. Typecheck, diff check, and strict OpenSpec validation passed. -->
- [x] 5.3 Record repo/commit/validation evidence, commit and push the isolated control/Edge branches, then serially integrate eligible default branches without packaging or deployment.
  <!-- Edge was rebased, revalidated, and fast-forward integrated to master at aidcp-edge@cff5a19. The control record was rebased onto current origin/main for fast-forward integration. No package, installation, or deployment was performed. -->

## 6. Nickname Selection Regression

- [x] 6.1 Add renderer coverage proving a nickname single-click selects without browser control, then replace the stale deleted row-activation callback while preserving nickname double-click editing.
  <!-- Edge regression reproduced `onRailRowActivate is not defined`, then passed 2/2 focused nickname gesture tests after routing the delayed single-click to `selectEnv`; no stale handler references remain. -->
- [x] 6.2 Run focused renderer validation, Edge typecheck, and strict OpenSpec validation; record the repair commits and delivery boundary without packaging or installation.
  <!-- Edge master@3cd60bf passed nickname gestures 2/2, fleet console 95/95, renderer smoke 104/104, syntax/stale-reference checks, typecheck, and diff check. Control evidence began at ba9d75b4 and strict OpenSpec validation passed. Edge master was pushed; no package, installation, client restart, Cloud deployment, or live-account action was performed. -->

## 7. Repeated Double-click Restore

- [x] 7.1 Revise the companion and fleet contracts so a repeated double-click on the shown environment restores that exact browser only after a correlated parking receipt.
- [x] 7.2 Serialize shown-target restore with exclusive recall, expose the exact-target IPC, and update renderer/coordinator coverage for success, failure, and latest-intent ordering.
  <!-- Edge added correlated `browser:parkShown`, shared recall/restore generation ordering, and renderer toggle coverage. Focused coordinator 9/9, static IPC 1/1, and renderer toggle 3/3 tests passed; JS syntax and diff checks passed. -->
- [x] 7.3 Run focused renderer/main/core validation, Edge typecheck, and strict OpenSpec validation; record commits and delivery boundaries without packaging or installation.
  <!-- Edge master@586b0b3 passed fleet console 97/97, renderer smoke 104/104, focused main/core 14/14, typecheck, syntax/diff checks, plus post-rebase coordinator 9/9 and toggle 3/3. Control evidence began at 56fd5f05 and strict OpenSpec validation passed. Edge master was pushed; no package, installation, client restart, Cloud deployment, or live-account action was performed. -->
