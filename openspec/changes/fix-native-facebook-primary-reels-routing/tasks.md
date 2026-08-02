## 1. Active Native routing

- [x] 1.1 Classify exactly `facebook_reels_primary` and `empty_feed_reels_fallback` as Reels-entry authorizations in the Native Rust Facebook dispatcher while preserving unrelated page-scroll behavior.
- [x] 1.2 Allow the configured-primary reason through the embedded Facebook Reels entry-hydration path without weakening the Native-only continuation guard.

<!-- 1.x: aidcp-edge be163e5; active Rust dispatcher and embedded Facebook router recognize both entry authorizations while preserving the unrelated-reason guard. -->

## 2. Regression coverage

- [x] 2.1 Add Rust coverage for both accepted entry reasons and at least one unrelated reason.
- [x] 2.2 Add embedded-router coverage proving both entry reasons return a canonical Reel card and an unrelated Feed-scroll reason remains rejected on a Reel surface.

<!-- 2.x: aidcp-edge be163e5; Rust predicate coverage and focused embedded-router contract both pass. -->

## 3. Validation and delivery

- [x] 3.1 Run the focused Facebook Native router test and the serial Native Rust test gate.
- [x] 3.2 Run Native formatting/clippy gates, Edge typecheck, and `openspec validate fix-native-facebook-primary-reels-routing --strict`.
- [x] 3.3 Record repo commit and validation evidence, then commit, integrate, and push the control and Edge default branches without packaging, installation, deployment, or real-account actions.

<!-- 3.1-3.2: focused router 2 pass; serial RUST_TEST_THREADS=1 native gate pass; native fmt and clippy pass; Edge typecheck pass; strict OpenSpec validation pass. All required checks were rerun after rebasing onto the latest defaults. -->
<!-- 3.3: source-only delivery. No Edge package, installation, DEV/OL deployment, browser restart, or real Facebook action was performed. -->
