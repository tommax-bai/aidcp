## 1. Native Reels execution

- [x] 1.1 Add bounded Native active-Reel and next-button probes keyed by `noteId + videoKey`.
- [x] 1.2 Route Facebook `page_scroll` by surface and implement ArrowDown, active-video wheel, and constrained next-button fallbacks with fresh pre-write probes.
- [x] 1.3 Return fresh Reels cards only after identity movement and emit one honest failed scroll receipt when movement cannot be proven.

## 2. Native session pacing

- [x] 2.1 Track the last Facebook list-card delivery anchor in the selector-free Native session facade.
- [x] 2.2 Apply abortable jittered `dwellMs` remainder before dispatching Native Facebook `page_scroll`, without changing XHS behavior.

## 3. Regression coverage

- [x] 3.1 Add Facebook router contracts for active Reels identity/card projection, ambiguity, and unchanged Feed behavior.
- [x] 3.2 Add Rust tests for Reels movement comparison, fallback selection, trusted input payloads, and honest no-target receipts.
- [x] 3.3 Add Native session tests for dwell remainder, elapsed-time absorption, missing dwell, cancellation, and non-Facebook isolation.

<!-- Implementation: aidcp-edge worktree repair-native-facebook-reels-scroll. Facebook Reels now uses Native-only surface routing, stable active-video identity, verified bounded fallbacks, and Edge-side dwell remainder pacing. No protocol-v2 or Cloud command-mapping changes were required. -->

## 4. Validation and delivery

- [x] 4.1 Run focused Edge TypeScript tests and Rust tests for the changed modules.
- [x] 4.2 Run Native build/verification, Edge acceptance tests, full tests, and typecheck.
- [x] 4.3 Run `openspec validate repair-native-facebook-reels-scroll --strict` and record repository commits, validation results, delivery boundary, and deviations.
- [x] 4.4 Commit, rebase, fast-forward integrate, and push the control and Edge changes without packaging or releasing an installer.

<!-- Edge: 8b48f75 on master and pushed to origin/master. Validation: focused TypeScript 23/23; Rust all-targets 60/60; clippy with -D warnings; Native build and verification; Edge acceptance 30/30 with one explicitly gated real-machine suite skipped; Edge full test 2293/2293; typecheck; git diff --check; OpenSpec strict validation. Delivery remains source-only: no installer packaging, signing, release, installed-client update, or live Facebook-account acceptance. Deviation: cargo/rustfmt were invoked through the installed rustup toolchain because Cargo was not on the shell PATH. -->
<!-- Control: OpenSpec change 7238693 on main and pushed to origin/main before this completion-ledger update. Edge integration was a clean fast-forward from current origin/master; control was current with origin/main before commit. -->

## 5. Real Reels route-card closure

- [x] 5.1 Record the observed `/reel/<id>` DOM shape where the active video has no permalink-bearing article and only `/reel/hashtag/` navigation anchors.
- [x] 5.2 Project one route-identified Reel card from the bounded active-video container while excluding non-content Reel routes from post identity.
- [x] 5.3 Add router regressions for route-only identity, repeated hashtag anchors, and unchanged ambiguous/missing-target behavior.
- [x] 5.4 Run focused and full Edge validation, repeat the live read-only `reel_cards` probe, then commit, fast-forward integrate, and push without packaging an installer.

<!-- Live DEV diagnosis 2026-07-25: target ads-k1etgm0e was on https://www.facebook.com/reel/1528556722142425 with one active video and one enabled next control. `reel_probe` succeeded, but `reel_cards` returned cards=[]/present_unreportable because the local video container had no current-Reel permalink/article and contained repeated `/reel/hashtag/` navigation anchors. Cloud therefore retained fallback pending and re-navigated to the same first Reel instead of entering ordinary Reels scrolling. -->
<!-- Closure: aidcp-edge ec0d7c4 was fast-forwarded and pushed to origin/master. Focused TypeScript 25/25, router regression 14/14 after rebase, Rust all-targets 60/60, acceptance 30/30 with one explicit real-machine gate skipped, full Edge 2295/2295, typecheck, Native build/verification, and git diff --check passed. The same live page evaluated with the repaired embedded router returned one ready Reel card bound to https://www.facebook.com/reel/1528556722142425. The canonical development checkout rebuilt its unsigned darwin-arm64 Native binary for the next local automation start; no installer was packaged, signed, or released, and no live navigation write was injected during diagnosis. -->
