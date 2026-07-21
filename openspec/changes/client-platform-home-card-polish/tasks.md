## 1. Platform-aware home card presentation

- [x] 1.1 Add deterministic platform modifiers to the daily progress and publish cards, clearing stale modifiers during environment switches.
- [x] 1.2 Add Facebook-specific single-publish copy, metadata and four-stage state mapping without changing XHS queue behavior.
- [x] 1.3 Apply the shared layered card styling, interaction states and responsive layout while keeping Facebook queue/carousel controls unavailable.

## 2. Regression and visual validation

- [x] 2.1 Add focused UI-logic and Electron DOM tests for Facebook pending, approved, submitted, empty and platform-switch states.
- [x] 2.2 Run focused publish/home UI tests, the required Edge full/acceptance gates, syntax checks and typecheck.
- [x] 2.3 Validate Facebook and XHS desktop/narrow variants visually, including hover, focus, hidden controls and horizontal overflow.

<!-- aidcp-edge commit ed48824 after replay onto master 8de0000; pre-replay full suite 2159/2159 passed. Post-replay focused UI suite 136/136, acceptance 29/29, typecheck and renderer syntax checks passed. Browser visual QA passed at 760px and 430px with no horizontal overflow; hover/focus and XHS regression were inspected. -->

## 3. Delivery

- [x] 3.1 Record Edge commit and validation evidence, then pass strict OpenSpec validation.
- [x] 3.2 Rebase or replay onto the latest default branches, rerun deciding checks, fast-forward merge and push Edge and control repositories.

<!-- Delivery: aidcp-edge ed48824 fast-forwarded and pushed to master; aidcp control commits 80fbc09 and fd48962 fast-forwarded and pushed to main. No Cloud deploy or desktop package was required because this is an Electron renderer-only change. -->
