## 1. Environment dashboard structure

- [x] 1.1 Move the single Xiaohongshu value-home DOM into the selected environment workspace, preserving existing content-home IDs and controllers.
- [x] 1.2 Add strict platform-derived visibility so Xiaohongshu shows the value dashboard while Facebook, WeChat Channels and unknown platforms retain the legacy environment body.
- [x] 1.3 Compose the existing account-schedule entry into the value dashboard without coupling its loading/error state to other dashboard sections.

## 2. Navigation and lifecycle integration

- [x] 2.1 Remove the duplicate “内容首页” root tab and keep the existing curated-library, creation, review and editor pages as deeper content views.
- [x] 2.2 Make dashboard actions open the correct deep view and make root close/back return to the current environment dashboard with restored scroll.
- [x] 2.3 Reuse the existing lifecycle/browser action chain and make the first-environment start guide target the visible dashboard action.

## 3. Layout and behavior validation

- [x] 3.1 Adapt existing value-home styles to the environment content width while preserving the 255px desktop work-panel ceiling, equal completed-message sizing, reduced motion and no horizontal overflow.
- [x] 3.2 Add focused tests for initial Xiaohongshu selection, other-platform isolation, stale env responses, complete dashboard structure, schedule composition, deep-page return and new-user lifecycle delegation.
- [x] 3.3 Run focused Edge tests, full Edge tests and typecheck; visually verify populated and empty states at desktop and narrow supported widths.
  <!-- Edge 5ccc917 after rebase: full `npm test` passed 2282/2282; `npm run typecheck` passed; browser QA covered populated/empty desktop states and a 620px responsive frame. -->

## 4. Integration and delivery

- [x] 4.1 Run `openspec validate xhs-environment-value-dashboard --strict` and record validation evidence.
  <!-- Control: strict validation passed before integration. -->
- [x] 4.2 Commit control and Edge changes, rebase onto the latest defaults, rerun required checks and fast-forward push the default branches.
  <!-- Edge 5ccc917 was fast-forwarded and pushed to master after the post-rebase full suite. Control proposal 91db694 was rebased onto d1641cc; this completion record is the final fast-forward control commit. -->
- [x] 4.3 Record that this delivery updates Edge source only and does not build, publish or install a desktop package.
  <!-- Delivery boundary: renderer source only; no Cloud runtime, database, installer, auto-update feed or installed desktop client was changed. -->
