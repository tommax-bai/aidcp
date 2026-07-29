## 1. Contract Alignment

- [x] 1.1 Synchronize the still-active `restore-native-facebook-residual-parity` design, specification, and task evidence so a later archive cannot restore the rejected five-of-five `explicit_end` home-Feed gate. <!-- proposal/design/spec synchronized; predecessor task 4.9 records the later override -->
- [x] 1.2 Validate that the new `facebook-feed-continuity` and `native-facebook-behavior-parity` deltas define near-bottom as the actual scroll container's one viewport, preserve the five fixed samples, require a same-document canonical-card witness, and keep marker-free completion home-command-only. <!-- both changes pass OpenSpec strict validation after implementation -->

## 2. Native Home-Feed Confirmation

- [x] 2.1 Change the five-sample classifier so a structurally valid canonical home Feed confirms exhaustion after the fifth sample even when `explicit_end` is absent or unstable, while preserving the existing non-home behavior. <!-- home structural confirmation maps to ConfirmedEnd; search/group retain five-marker terminal handling -->
- [x] 2.2 Require the commanded scroll to have observed at least one real canonical card before mapping a structurally confirmed home window to `feed_exhausted`; otherwise retain the existing zero-card/continuation evidence ladder. <!-- canonical witness is bound to the same home surface, URL, and document time origin; raw-card continuation remains separate -->
- [x] 2.3 Preserve the exact `t=0 / 5 / 7.5 / 10 / 12.5s` schedule, actual-scroll-container one-viewport near-bottom predicate, 100px height-growth threshold, same-document/surface/card checks, cancellation, deadline, and no-early-success rule. <!-- internal probe now carries documentTimeOriginMs and scrollViewportHeight; non-home command redirects cannot inherit marker-free authorization -->

## 3. Regression Coverage

- [x] 3.1 Add or update focused Rust tests proving marker-free and intermittently marked home windows return `feed_exhausted` only after sample five. <!-- stable/partially marked home and no-early-success cases pass in the 23-test Feed focus -->
- [x] 3.2 Add or update negative tests for no prior canonical card, loading, material height growth, new/reordered card identity, navigation/generation/surface change, backward document-age reset, departure from near-bottom, and marker-free search/group windows. <!-- also covers document-time-origin change, nested-scroller viewport, non-home-to-home redirect, and noncanonical raw-card continuation -->
- [x] 3.3 Keep the deterministic timing and cancellation/deadline tests green without weakening the initial-home-empty or present-unreportable ladders. <!-- exact offsets, cancellation/deadline, zero-card, and present-unreportable tests pass -->

## 4. Validation and Delivery

- [x] 4.1 Run focused Facebook Feed Rust tests, `npm run gate:native`, and `npm run typecheck` in the Edge worktree. <!-- Feed Rust 23/23; router contract 98/98; native fmt/clippy/full test OK; typecheck OK -->
- [x] 4.2 Run `openspec validate confirm-facebook-feed-exhaustion-structurally --strict` and strict validation of the synchronized predecessor change. <!-- both strict validations pass -->
- [ ] 4.3 Record repository commit SHAs and validation evidence, rebase onto the latest defaults, then fast-forward and push Edge `master` and control `main` without packaging an installer.
