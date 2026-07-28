## 1. Contract Fixtures

- [x] 1.1 Add router fixtures proving `/reel/` with one active video is targetable but emits no card until a canonical id exists.
- [x] 1.2 Add vertical, horizontal, and ambiguous navigation-rail fixtures that assert axis and unique forward-control selection.
- [x] 1.3 Add Rust unit coverage for anonymous versus identified transition rules, typed axis decoding, and forward-key mapping.

## 2. Edge Native Implementation

- [x] 2.1 Split the router's unique active-video observation from canonical Reel identity without weakening card or interaction identity gates.
- [x] 2.2 Generalize the next-control probe to return a structurally proven vertical or horizontal axis and only that axis's fresh forward target.
- [x] 2.3 Extend strict Rust probe types and transition helpers for optional pre-action `noteId`, session-local `videoKey`, and typed navigation axis.
- [x] 2.4 Make the Reels actuator dispatch ArrowDown plus vertical-only fallbacks or ArrowRight plus horizontal button fallback, suppressing later writes after observed movement.
- [x] 2.5 Return `not_started` only before input and an honest ambiguous failure when dispatched navigation never yields a canonical post-transition card.

## 3. Validation

- [x] 3.1 Run the focused Facebook router contract tests and Native Rust unit tests.
<!-- Edge focused validation: facebook-router-contract 80/80; cargo test --locked reel 15/15 across unit + Fake-CDP filtered tests, including anonymous horizontal ArrowRight bootstrap. -->
- [x] 3.2 Run Native formatting, strict Clippy, the complete Rust test suite, and Native artifact build/verification.
<!-- Edge Native validation: cargo fmt --check; cargo clippy --locked --all-targets -- -D warnings; cargo test --locked (102 unit + 39 integration/process tests); build:native-page-engine + verify:native-page-engine, unsigned darwin-arm64 SHA-256 ab418c63836100d621b4b0504081d9ffa2b8d396287f7d78d84a64994202f4b0. -->
- [x] 3.3 Run Edge acceptance tests, the complete Edge test suite, and TypeScript typecheck.
<!-- Edge validation: test:acceptance 30 passed / 1 gated real-E2E skipped; npm test 2552 passed / 1 gated real-E2E skipped; npm run typecheck passed. -->
- [x] 3.4 Run `openspec validate support-facebook-reels-entry-axis-navigation --strict` and record validation evidence and any delivery-boundary deviations.
<!-- Control validation: openspec validate support-facebook-reels-entry-axis-navigation --strict passed. Delivery is source + unsigned local Native artifact validation only; no installer, signing/notarization, installed-client update, or real-account execution is claimed. -->

## 4. Integration

- [x] 4.1 Commit the Edge implementation and OpenSpec artifacts with explicit path scopes, rebase both branches on their latest defaults, and rerun required validation.
<!-- Edge implementation commit 845ef0d; control artifacts committed on the matching branch. Both branches rebased cleanly. land-change reran test:acceptance (30 pass), npm test (2552 pass / 1 gated E2E skip), and typecheck before Edge integration. -->
- [x] 4.2 Fast-forward the Edge and control default branches, push them without force, and record repo SHAs and source-only delivery boundaries.
<!-- Integrated and pushed without force: aidcp-edge origin/master 845ef0d; aidcp origin/main e95a318 (artifacts + validated integration record). Source and unsigned local Native artifact only; no dev/OL runtime deployment, installer, signing/notarization, or real-account acceptance. -->
