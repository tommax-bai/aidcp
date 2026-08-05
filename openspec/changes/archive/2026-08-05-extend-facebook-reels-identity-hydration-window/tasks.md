## 1. Regression Coverage

- [x] 1.1 Add Native regression coverage that fixes the shared Facebook Reels canonical-card hydration window at 15 seconds while preserving the existing ambiguous terminal receipt.

## 2. Edge Implementation

- [x] 2.1 Replace the inline five-second Reels hydration deadline with a named 15-second constant used by both entry and post-transition verification.

## 3. Validation And Delivery

- [x] 3.1 Run focused Reels Native tests, Native formatting and clippy gates, and Edge typecheck.
  <!-- Evidence: focused unhydrated Reels entry Fake CDP test passed 1/1 in 15.33s; `npm run gate:native:fmt`, `npm run gate:native:clippy`, and `npm run typecheck` passed. The first full Native run correctly exposed that the test-only 15s outer command budget could expire before the new 15s inner hydration receipt; the test budget was raised to 30s, while production remains on its existing 180s Facebook scroll budget. -->
- [x] 3.2 Run the serialized Native test gate and `openspec validate extend-facebook-reels-identity-hydration-window --strict`.
  <!-- Evidence: `RUST_TEST_THREADS=1 npm run gate:native:test` passed all 376 Native tests, including Fake CDP 67/67 and the new Reels timeout assertion; strict OpenSpec validation passed. -->
- [x] 3.3 Record repository, commit, validation, packaging, installation, and deployment boundaries; then integrate and push the Edge and control changes.
  <!-- Evidence: Edge commit `2c802430be3140952b3d81a448c5336da722fd0e` was integrated and pushed to `aidcp-edge` `origin/master` by `scripts/land-change` after acceptance 38/38, the complete Edge test suite, and the Native fmt/clippy/test gate passed. No Edge package or installer was built, `/Applications/AIDCP.app` was not replaced, no Cloud/Console deployment was performed, and no real-account Facebook action was run. The control OpenSpec commit and push are recorded in the control repository history. -->
