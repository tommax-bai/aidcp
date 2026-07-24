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

## 5. Prototype fidelity correction

- [x] 5.1 Restore the featured lineage's substantial source/output covers, engagement evidence, actions and honest unlinked-draft state.
- [x] 5.2 Restore portrait-led reference cards and deterministic decorative fallbacks for missing media while keeping real titles, summaries and counts authoritative.
- [x] 5.3 Complete the idle work-panel process preview and reduce schedule emphasis without exceeding the 255px desktop panel ceiling or supported-width bounds.
- [x] 5.4 Add focused renderer/static tests, compare the populated and idle states against the July 22 prototype in-browser, run full Edge tests/typecheck, validate OpenSpec and integrate the correction.
  <!-- Edge f734708: focused renderer/security/schedule/fleet tests 129/129; full suite 2284/2284; typecheck passed. Browser comparison covered populated and idle states at 1280px and 900px with no horizontal overflow; integration is recorded by the delivery commit. -->

## 6. Embedded-width fidelity correction

- [x] 6.1 Base dashboard responsiveness on the environment content container and preserve readable customer-facing typography.
- [x] 6.2 Stack the featured lineage and lower content sections at medium embedded widths, and balance populated versus empty section height.
- [x] 6.3 Add static regression coverage, visually compare the reported width against the July 22 hierarchy, and rerun required Edge/OpenSpec validation.
  <!-- Edge 187e3f3: focused renderer/security/schedule/fleet tests 130/130; full suite 2285/2285; typecheck passed. Browser QA used an 847px environment content container and a 620px narrow frame, confirmed 240px desktop work height, container-driven stacking, decorative tone-0 fallback and no horizontal overflow. -->
- [x] 6.4 Rebase, integrate and push the renderer and OpenSpec correction while preserving the source-only delivery boundary.
  <!-- Edge 187e3f3 was fast-forwarded and pushed to master. Control was rebased onto the latest origin/main; this completion record is the final control delivery commit. Source-only boundary remains unchanged: no desktop package or installed client was updated. -->

## 7. State-matrix visual fidelity

- [x] 7.1 Treat the July 22 HTML demo as the shared visual contract for populated, loading, empty, error, active, waiting and collapsed states.
- [x] 7.2 Restore content-sized featured badges, balanced source/relation/output proportions, portrait reference-card rhythm and explicit “可创作 / 已创作” scan states.
- [x] 7.3 Replace stretched generic lower-section placeholders with independently designed 218px reference and customer-content states, including honest live, idle, error and action treatments.
- [x] 7.4 Align the 240px work panel's idle, active, waiting and collapsed states while preserving stage-specific labels, completed-label visibility and character-by-character current output.
- [x] 7.5 Add focused state/render regressions, visually compare the client at the reported content width against the populated and empty prototype states, then run full Edge tests, typecheck and strict OpenSpec validation.
  <!-- Edge 30c5c97: focused renderer/security tests passed 41/41; full suite passed 2285/2285; typecheck passed. Browser QA used a 892px dashboard content width and covered populated, empty, loading, error, active and waiting states: work panel 240px, populated lineage 193.3px, featured empty 160px, lower empty states 218px and horizontal overflow 0. Strict OpenSpec validation passed. Source-only delivery; no desktop package or installed client was updated. -->
