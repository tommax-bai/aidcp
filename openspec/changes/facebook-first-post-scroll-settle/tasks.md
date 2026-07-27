## 1. Edge implementation

- [x] 1.1 Add the fixed 2-second hydration settle between Facebook first-post scrolling and the returned card probe.
- [x] 1.2 Add focused regression coverage proving the settle occurs before `feedCards()` while the scroll-round bound remains unchanged.
- [x] 1.3 Rebuild the Native Facebook router artifact and verify generated-source integrity.

## 2. Validation and delivery

- [x] 2.1 Run focused Native Facebook tests and Rust formatting/check validation.
- [x] 2.2 Run the Edge typecheck and relevant artifact integrity validation.
- [x] 2.3 Run `openspec validate facebook-first-post-scroll-settle --strict`.
- [x] 2.4 Record repository commits, validation evidence, runtime delivery boundary, and deviations in this checklist.

<!--
Delivery evidence (2026-07-28):
- aidcp-edge commit `453ba8c` fast-forwarded and pushed to `origin/master`.
- `tsx --test test/native-page-engine/facebook-router-contract.test.ts`: 73 passed.
- `tsx --test test/native-page-engine/facebook-capability-boundary.test.ts`: 5 passed.
- `cargo test --locked --test fake_cdp facebook_first_post_scrolls_until_the_below_fold_candidate_hydrates -- --exact`: 1 passed.
- `cargo fmt --all -- --check`, `cargo check --locked`, `npm run typecheck`: passed.
- `npm run build:native-page-engine` and `npm run verify:native-page-engine`: passed for unsigned darwin-arm64 artifact `b19c7c409fbae4bf98344cf347d92a9c3ebe26cec3cfc45f8cb39e300ffad3d7`.
- Integration gate: acceptance 30 passed; full Edge suite 2482 passed, 1 gated machine E2E skipped, 0 failed; typecheck passed.
- `openspec validate facebook-first-post-scroll-settle --strict`: passed.
- Per operator boundary, no Facebook account/browser probe, installed-client replacement, package, signing, or machine validation was performed.
- Deviation: the first Native build attempt selected Rust 1.87 and was rejected by the crate's 1.97.1 requirement; rerunning with the installed 1.97.1 toolchain passed.
-->
