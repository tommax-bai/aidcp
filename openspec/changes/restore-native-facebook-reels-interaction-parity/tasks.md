## 1. Regression Baseline

- [x] 1.1 Confirm the prepared control and Edge worktrees track the latest default branches and have isolated physical dependencies.
  <!-- control origin/main 20cb7d8; Edge origin/master 20245e8; physical npm ci installed 368 packages -->
- [x] 1.2 Add focused failing Native cases for Reel sibling action rails, multilingual like/follow CTA variants, ambiguity, already-state, movement, and unconfirmed writes.
  <!-- pre-fix focused run: 27 passed / 5 failed, covering sibling controls, ambiguity, fresh commit/verify, picker scope, already-following -->

## 2. Native Reel Control Resolution

- [x] 2.1 Port the established Facebook neutral/reacted and follow/following semantic label families into the embedded Native router with count/control exclusions.
  <!-- Native router recognizes bounded zh/en/vi semantics; selected state accepts only explicit aria/label/text witnesses, and the non-Reel Feed classifier remains unchanged. -->
- [x] 2.2 Resolve like and follow candidates against the uniquely active canonical Reel across nested and sibling action-rail layouts without document-order fallback.
  <!-- Candidate association uses canonical Reel/video identity, bounded action-rail geometry, discussion/share exclusions, unique author witnesses, and unique-target checks. -->
- [x] 2.3 Add a fresh primary Reel-like commit and same-Reel selected-state probe, plus a unique visible picker-scoped Like target for the one permitted second-stage trusted commit.
  <!-- Primary commit stores canonical Reel plus videoKey and marks one live control; verification and picker lookup require that same identity. -->

## 3. Native Command Orchestration and Evidence

- [x] 3.1 Update Rust like orchestration to use the fresh primary commit, at most one scoped picker commit, and honest not-started versus ambiguous effect phases.
  <!-- Zero-write resolution failures remain not_started; any post-primary uncertainty is ambiguous; confirmed requires a same-Reel selected-state witness. -->
- [x] 3.2 Keep follow as one trusted pointer write and terminate honestly on active-Reel movement, target loss, ambiguity, already-following, or unconfirmed state.
  <!-- Follow requires author qualification, freshly re-probes before dispatch, compares noteId plus videoKey plus author, and never dispatches a recovery click. -->
- [x] 3.3 Add bounded local Native action-receipt diagnostics for action, result, effect phase, and reason without page content or protocol changes.
  <!-- Edge logs fixed token fields only; non-token page-derived text collapses to non_token_reason. -->

## 4. Verification

- [x] 4.1 Run focused Native router/session tests, legacy Reel oracle tests, and Native Cargo tests.
  <!-- Post-review focused TS: 78 passed before rebase and 84 after rebase. Cargo library: 51 passed. Four Fake-CDP write-boundary cases passed: direct/picker Like and moved/confirmed Follow. Full Cargo still has the pre-existing explore_feed fixture null-field mismatch. An extra full fake_cdp run exposed three unrelated stale fixed-response tests; facebook_initial_scan_resets_a_persisted_reel_to_home_feed was reproduced on the unchanged canonical master. -->
- [x] 4.2 Run Edge protocol acceptance, full tests, and typecheck with bounded output.
  <!-- Post-rebase acceptance: 30/30; focused Native/legacy: 84/84; full Edge suite: pass (dot reporter, exit 0); typecheck: pass. -->
- [x] 4.3 Run `openspec validate restore-native-facebook-reels-interaction-parity --strict`.
  <!-- strict validation passed again after independent-review fixes on 2026-07-26 -->

## 5. Integration and Runtime Boundary

- [x] 5.1 Rebase and fast-forward integrate the isolated Edge and control branches, record commit and validation evidence, and push without force.
  <!-- Edge rebased onto origin/master with one additive browse-session test-harness conflict resolved by retaining both view/UI projection and bounded action diagnostics; integrated/pushed commits 2228a20 and d48c47b. Control rebased commits 305138d, d477821, and 078a6ae; strict validation passed before default-branch push. -->
- [x] 5.2 Rebuild the local development Native Page Engine artifact without packaging an installer; keep real-account exact-target like/follow acceptance explicitly pending unless separately authorized and observed.
  <!-- Canonical Edge master rebuilt the unsigned darwin-arm64 development artifact; encoded-rule digest ded35464242134c5b74de260c6c478920b15011f9be13d844cfb35c1b028fec2. No installer/signing/notarization or real-account Like/Follow action was performed. -->
