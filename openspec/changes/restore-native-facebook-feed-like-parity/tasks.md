## 1. Characterize the regression

- [x] 1.1 Add a focused failing router test proving Feed like must choose the Nth exact structural post reaction control and use its DOM click handler instead of reaction-count or adjacent-card decoys
  <!-- Edge test/native-page-engine/facebook-feed-like-parity.test.ts: initial characterization 4/4 failed before production changes; current exact-card case covers first-card, summary-toolbar, loose same-card, and target primary controls. -->
- [x] 1.2 Add same-card failure cases for duplicate identity, target virtualization or identity change, direct-toggle picker suppression, operation-bound picker ambiguity/offscreen handling, and offscreen primary control
  <!-- Edge focused suite now covers duplicate identity, marker loss, identity recycling, blocker recheck, stale/wrong-operation picker, picker ambiguity/offscreen, and offscreen primary control. Rust fake-CDP covers direct-toggle zero press and picker exactly one press/release pair. -->

## 2. Restore Feed actuation parity

- [x] 2.1 Implement fresh exact-card Feed commit with one structural React control, an operation marker, and DOM initial actuation
  <!-- Edge native/page-engine/src/facebook-command-router.js adds feed_like_target_probe/feed_like_commit with fresh blocker/consent and exact structural control checks. -->
- [x] 2.2 Implement bounded control-position scrolling, marker-bound verification, best-effort cleanup, and one operation-scoped reaction-picker coordinate target
  <!-- Edge router + engine bind verify/picker to the active marker, exclude pre-existing picker containers, scroll the primary control with bounded wheel steps, and clear operation state best-effort. -->
- [x] 2.3 Route non-Reels Native like through the Feed choreography while retaining the Reels-owned path and existing command/result contract
  <!-- Edge native/page-engine/src/engine.rs probes the Reel surface, preserves execute_facebook_reel_like, and uses the Feed-specific DOM/picker choreography only outside Reels. -->

## 3. Validate the owning repositories

- [x] 3.1 Run focused TypeScript router tests and Native Rust tests
  <!-- Edge 37f56b0: `tsx --test ...facebook-feed-like-parity.test.ts ...facebook-router-contract.test.ts` 35/35 passed; `cargo test --test facebook_feed_like` 2/2 passed; `cargo test --lib` 51/51 passed. Extra full-Native probes exposed existing baseline failures outside this change: `fake_cdp` initial-scan/note-open cases fail unchanged at the pre-change HEAD (reproduced from a clean git archive), and `contract_fixtures` expects omitted XHS null blocking fields. -->
- [x] 3.2 Run Edge typecheck and record the explicitly unperformed installer, deployment, and live-account gates
  <!-- Edge 37f56b0: `npm run typecheck` passed. No installer/package build, deployment, running desktop replacement, or real-account Facebook acceptance was performed or claimed. -->
- [x] 3.3 Run `openspec validate restore-native-facebook-feed-like-parity --strict`
  <!-- Control: strict validation passed after switching authority to the existing facebook-note-scoped-targeting capability. -->

## 4. Delivery evidence

- [x] 4.1 Record Edge and control commit SHAs, validation evidence, deviations, and concurrent-file overlap in this checklist
  <!-- Edge implementation: aidcp-edge 37f56b0. Control artifacts: aidcp fe25835 plus the follow-up evidence commit containing this line. Validations: JS 35/35, Feed Rust 2/2, Rust lib 51/51, typecheck pass, OpenSpec strict pass. Existing baseline-only Native failures are recorded in 3.1. Concurrent Reels parity overlaps native/page-engine/src/engine.rs, native/page-engine/src/facebook-command-router.js, and native/page-engine/src/facebook.rs; integrate Reels first, then reconcile Feed and rerun the combined full boundary. Branches were committed only, not pushed, packaged, deployed, or live-account tested. -->
