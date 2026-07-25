## 1. Parity Baseline

- [x] 1.1 Record the Facebook command support matrix and map each supported Native path to its existing OpenSpec and retired TypeScript behavior oracle.
  <!-- aidcp design ledger; implementation oracle refreshed against aidcp-edge master; no protocol change -->
- [x] 1.2 Add focused failing parity tests for unsupported commands, Feed state distinctions, exact target selection, and ambiguous comment reasons.
  <!-- aidcp-edge 54ae5b2; focused Native regression suite 71/71 -->

## 2. Stateful Native Browse

- [x] 2.1 Add Facebook session state for active list surface, seen canonical identities, and bounded refresh timing.
  <!-- aidcp-edge 54ae5b2; Rust EngineSession state, Cargo 50/50 -->
- [x] 2.2 Implement loading-aware initial Feed settling and bounded continuation across visible unreportable articles without entering Reels.
  <!-- aidcp-edge 54ae5b2; eight-round established bound retained -->
- [x] 2.3 Implement bounded ordinary Feed continuation, de-duplication, and structural `feed_exhausted` evidence.
  <!-- aidcp-edge 54ae5b2; no-growth, near-bottom, consecutive evidence -->
- [x] 2.4 Preserve search/back list context and replace primary raw reload with verified SPA Feed refresh plus the existing bounded reload floor.
  <!-- aidcp-edge 54ae5b2; search hydration continuation added; three-minute reload floor retained -->

## 3. Blocker, Consent, and Capability Gates

- [x] 3.1 Restore login, positive captcha, generic checkpoint, and Facebook throttle classification with same-source bounded evidence.
  <!-- aidcp-edge 54ae5b2; sustained unknown confirmation remains Edge-owned -->
- [x] 3.2 Enforce the configured Facebook cookie-consent policy with unique target selection, trusted click, post-click disappearance, and bounded attempts.
  <!-- aidcp-edge 54ae5b2; accept_all and necessary_only remain distinct -->
- [x] 3.3 Reject unsupported Facebook commands before embedded-router evaluation and add command-matrix assertions.
  <!-- aidcp-edge 54ae5b2; capability_unsupported is pre-CDP -->

## 4. Exact-Target Native Writes

- [x] 4.1 Make Feed and Reels like/follow resolve, actuate, and verify the commanded canonical target without DOM-order fallback.
  <!-- aidcp-edge 54ae5b2; reaction picker excludes the original post control -->
- [x] 4.2 Restore comment target hydration, trusted input/submit, full readback, same-account verification, and established pending/rejected/ambiguous terminal reasons.
  <!-- aidcp-edge 54ae5b2; participation gate and exclusive sibling editor parity included -->
- [x] 4.3 Restore bounded group-join readiness and post-click state polling with honest already-member, pending, questionnaire, failure, and ambiguous outcomes.
  <!-- aidcp-edge 54ae5b2; recommended-group CTAs excluded from current-group scope -->
- [x] 4.4 Restore Facebook composer hydration, trusted full-text input and submit, cleanup, and bounded post-submit verification for the supported publish atoms.
  <!-- aidcp-edge 54ae5b2; unsupported publish atoms remain honest; no capability expansion -->

## 5. Verification and Delivery

- [x] 5.1 Port the relevant legacy Feed, overlay/consent, like, comment, join, and publish behavior cases into focused Native tests.
  <!-- aidcp-edge 54ae5b2; Native 71/71 and legacy Facebook suite exit 0 -->
- [x] 5.2 Run focused Edge tests, Native Cargo tests, Edge acceptance and full tests, and Edge typecheck with bounded output.
  <!-- acceptance 30/30; Edge 2309/2309; Cargo 50/50; typecheck pass -->
- [x] 5.3 Run `openspec validate restore-native-facebook-behavior-parity --strict` and record repository commits, validation, delivery scope, and deviations in this checklist.
  <!-- strict validation pass; deviation: cargo-clippy unavailable in installed toolchain, non-gating tests/typecheck passed -->
- [x] 5.4 Rebase and fast-forward integrate the isolated Edge worktree, commit and push the control change, and rebuild the local Native Page Engine artifact without packaging an installer.
  <!-- Edge master 54ae5b2; aidcp OpenSpec f7e5e30; canonical darwin-arm64 sha256 108aed9b04ffccc446baa3dfe590595ce415b31832ecf094f4a7b80db3dbacb1; no installer or OL deployment -->
