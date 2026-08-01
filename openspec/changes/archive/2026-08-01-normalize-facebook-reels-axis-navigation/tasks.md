## 1. Regression Coverage

- [x] 1.1 Add router contract fixtures for the viewport-scale horizontal overlay and the wide-video outer vertical rail, including multiple viewport sizes and a nearer reaction column.
- [x] 1.2 Add a Native Fake-CDP regression proving `axis:horizontal` with `found:false` still dispatches only ArrowRight before same-target transition verification.

## 2. Edge Implementation

- [x] 2.1 Replace raw pixel admission and gap gates with clipped, viewport-normalized active-video/control topology in the Facebook Reels router.
- [x] 2.2 Separate unique axis evidence from safe pointer eligibility so disabled forward controls and large overlays cannot be clicked.

## 3. Validation and Integration

- [x] 3.1 Run the focused router and Native Fake-CDP regression tests.
- [x] 3.2 Run Edge typecheck and the proportionate Native page-engine test suite.
- [x] 3.3 Strict-validate OpenSpec, record repository/commit/validation evidence, integrate the isolated Edge change, and push the owning default branches.

<!-- repo="aidcp-edge" commit="ab635625f386e83f00cfb3295913eeb6d54ec4ee" validation="facebook-router-contract 106/106; npm test 2799 passed, 1 skipped, 0 failed; RUST_TEST_THREADS=1 npm run gate:native:test passed; npm run typecheck passed; native fmt and clippy passed; openspec strict validation passed" integration="fast-forwarded and pushed origin/master" deployment="source only; no installer build, local install, or real-account action" deviations="Two unrelated Facebook publish deadline tests each flaked once under parallel Native execution; both exact reruns and the complete serialized Native suite passed." -->
