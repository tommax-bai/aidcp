## 1. Evidence and Isolated Setup

- [x] 1.1 Create matching control and `aidcp-edge` worktrees from current default branches with a physical Edge dependency tree.
  <!-- Control and Edge worktrees/branches were renamed with the expanded change to `restore-native-facebook-localized-action-parity`; baselines remain origin/main e447077 and origin/master a6623a4. `npm ci --prefer-offline` exited 0 and Edge owns a non-symlink node_modules. -->
- [x] 1.2 Record the observed Reels Like and Publish failures and complete a retired-executor versus Native action-semantics audit.
  <!-- Repair: Reels bare zh-CN 赞+count, shared reaction ownership, Publish entry/select lifecycle and localized entry/submit labels, Comment pending-approval variants. Retain: Reels Follow author binding, Group Join lists/scope, Consent/blocker, Comment editor/participation/rejected/in-flight/Like+Reply. No Cloud/protocol change. -->

## 2. Shared Reaction Semantics

- [x] 2.1 Add one deterministically ordered Native-only reaction-semantics router module with the retained multilingual vocabulary and positive selected-state primitives.
- [x] 2.2 Migrate Feed Like and Reels to the shared lexical semantics while keeping geometry, target association, commit, and verification capability-owned.
- [x] 2.3 Recognize a unique active-Reel right-rail bare Like label with numeric text without relaxing Feed summary, comment, off-rail, ambiguity, or selected-state guards.
  <!-- Added ordered 08-reaction-semantics.js; Feed and Reels now consume its lexical primitives. Reels alone composes supported bare Like+numeric with active-video rail evidence. Existing router suite remained 44/44 before adding new cases. -->

## 3. Publish Lifecycle and Vocabulary

- [x] 3.1 Restore `navigate_entry` as bounded Facebook-home navigation/readiness validation with no composer click.
- [x] 3.2 Restore `select_mode` target validation, delayed entry polling, one fresh trusted click, and remaining-budget editor verification with honest pre/post-dispatch phases.
- [x] 3.3 Restore the retired Publish entry/editor/submit/submitted-state localized label families and exclude comment/reply decoys inside capability-owned probes.
- [x] 3.4 Update the Facebook capability parity ledger and Rust/parser fixtures for the restored Publish stage ownership.
  <!-- Publish navigation now owns navigation/readiness only through one atomic capability snapshot. Rust select_mode owns canonical-target validation, the 20s late-entry window, one fresh pointer commit, and editor verification inside the Cloud-provided absolute 40s Facebook select_mode deadline preserved through TypeScript/client/Rust. Probe vocabulary restores the retired entry/editor/submit/submitted-state families; submit confirmation restores the old 20s ceiling capped by the caller deadline. Generic JS command branches were removed to prevent dual ownership. -->

## 4. Comment and Boundary Semantics

- [x] 4.1 Restore the full retired Comment pending-approval veto vocabulary while preserving submitted-body stripping and own-row/server-evidence scoping.
- [x] 4.2 Add retain-only parity assertions for equivalent Reels Follow, Group Join, Consent/blocker, and Comment editor/rejected/in-flight/Like+Reply vocabularies.
- [x] 4.3 Add source/manifest gates preventing duplicated shared reaction vocabulary or `CloudElementSelector`/`LikeStepRunner` production assembly.
  <!-- The Comment approval veto now matches the retired executor while stripping the submitted body before lifecycle classification. Exhaustive behavior matrices execute every retained author-bound Follow, scoped Join state, consent action, Comment editor, rejected, in-flight, Like, and Reply family. Manifest/owner tests enforce one shared reaction source and Rust-owned Publish stages; the existing direct-routing contract keeps CloudElementSelector/LikeStepRunner out of production assembly. -->

## 5. Focused Regression Coverage

- [x] 5.1 Add Reels/Feed router cases for retained Like locales, observed `赞` plus count, positive verification, summaries, comments, off-rail, ambiguity, and unknown labels.
- [x] 5.2 Add Publish router/Rust cases for every retained entry/submit/submitted-state locale, personalized `分享你的新鲜事`, late entry, already-open editor, home loss, one-click bound, and post-click timeout.
- [x] 5.3 Add Comment cases for full pending-approval variants and submitted-body non-interference.
  <!-- Coverage now includes a different-score Publish-entry ambiguity, atomic home blockers, Facebook-only 40s timeout propagation, slow-CDP deadline crossings, and bounded transient navigation/post-click read errors in addition to the locale and lifecycle matrices. Final counts are recorded after validation in section 6. -->

## 6. Validation

- [x] 6.1 Run focused retired-oracle, Facebook router, capability-boundary, Publish, Comment, Feed Like, and Rust Native Facebook tests.
  <!-- Focused Native/client/router/boundary/Publish matrix: 82/82 passed. Rust Publish lifecycle and delayed-CDP matrix: 15/15 passed, including three repeated passes of the post-click deadline-crossing case. -->
- [x] 6.2 Run Cargo format, clippy with warnings denied, and the full Rust Native suite.
  <!-- cargo fmt --check and cargo clippy --all-targets -- -D warnings exited 0. Full Cargo suite passed: 75 unit, 1 contract fixture, 2 Facebook Feed Like, 19 fake-CDP, 1 process protocol, and 0 doc-test failures. -->
- [x] 6.3 Run Edge protocol acceptance, full tests, typecheck, Native build/verification, production dist, and desktop build-input verification.
  <!-- Edge acceptance 30/30, full tests 2369/2369, and typecheck passed. Production dist reported reachable=79 removed=63 legacy_page_rules=absent source_maps=absent. Final unsigned darwin-arm64 Native artifact verified at sha256 03d3f958af4b0d713e104dfddd879b910d8c963ec2d64629af8fee9ac060b2c4; desktop build input verified. -->
- [x] 6.4 Run `openspec validate restore-native-facebook-localized-action-parity --strict` and `git diff --check` in both worktrees.
  <!-- Strict OpenSpec validation and both worktree diff checks exited 0 before integration. -->

## 7. Integration and Development Artifact

- [x] 7.1 Rebase the Edge worktree onto current `origin/master`, rerun required gates, commit, and fast-forward push to `master` without force.
  <!-- aidcp-edge commit 0439ecf3955315b10189d1b4341b62051a7d1348 was already based on current origin/master, retained the recorded green gates, and fast-forward pushed a6623a4..0439ecf to master without force. -->
- [x] 7.2 Record implementation commits, validation, and delivery boundaries; rebase the control worktree onto `origin/main`, commit, and fast-forward push to `main` without force.
  <!-- Edge implementation is 0439ecf3955315b10189d1b4341b62051a7d1348; the rebased control specification commit is 0492abbe1538d1aee51a7ce22ade266e77006fc5. Validation and the unperformed installer/restart/deploy/live-write boundaries are recorded above. This closeout record is pushed with the same fast-forward control integration. -->
- [x] 7.3 Rebuild and verify the canonical local development Native artifact; report installer, signing, release, runtime restart, and real-account action acceptance separately.
  <!-- Canonical aidcp-edge master fast-forwarded to 0439ecf and rebuilt/verified the unsigned darwin-arm64 local development artifact at sha256 e1c7442eb7bdba1136021b75c1d947783e99ae27a538f263a8fbfd6af951c297. No installer, signing, release, runtime restart, deployment, or live-account write was performed. The pending non-submit live composer probe and real Publish acceptance from active change facebook-composer-open-deadline remain delivery gates and are not satisfied by this source/artifact work. -->

## 8. DEV Publish Record 195 Follow-up

- [x] 8.1 Record the DEV failure chain and preserve its recovery boundary: `select_mode` returned `ambiguous_target`, the delegated task became `candidate_terminal_failed`, and the failed record is not retried or mutated by this source change.
  <!-- DEV logs and read-only ledgers show record 195 failed at select_mode/ambiguous_target, publish_log and its delegated task are terminal failed, and authorization publish-195 revision 1 is consumed. This change does not retry, mutate, or transfer that authorization; a future real publish requires a new record and explicit approval after the updated runtime is loaded. -->
- [x] 8.2 Canonicalize one matching Publish semantic container and its one matching actionable descendant to the descendant DOM identity, while preserving real multi-control ambiguity.
  <!-- The Publish probe now separates semantic evidence from actionable identity, expands only matching actionable descendants, deduplicates by DOM node, and never falls back to clicking a non-actionable container. Tests cover the observed region/composer structure, nested label evidence, multiple real controls, independent different-score controls, and a container-only false positive. -->
- [x] 8.3 Add focused router regressions, run the required Edge/Rust/OpenSpec gates, and rebuild the canonical local development Native artifact.
  <!-- Router contract 62/62, Edge acceptance 30/30, full Edge 2373/2373, typecheck, cargo fmt/clippy, full Rust (75 unit plus all integration groups), strict OpenSpec, both diff checks, production dist, and desktop build-input verification passed. The isolated-worktree unsigned darwin-arm64 Native artifact verified at sha256 0f391d11bb07f0fdaa9bc44ebde997ea1ef9f05b24616336a3d1fab941b85e68. A read-only current-page structural probe resolved exactly one canonical personalized composer button; no click or publish was performed. -->
- [x] 8.4 Integrate and push the Edge and control follow-up commits; report runtime restart, non-submit live probe, and real publish acceptance as separate gates.
  <!-- Edge follow-up e94f0a1dec12d89c666e09ce59aa33123acfb1ba fast-forward pushed to master. Canonical aidcp-edge master then rebuilt and verified the unsigned darwin-arm64 local development artifact at sha256 13d17488426d1aa39f9fa4aee98efdf9caeec1b231fc0d461bd77a74a6d55614. The control commit containing this closeout record fast-forward pushes the OpenSpec update to main. The already-running Electron process has not been restarted, and no composer click, submit, database recovery, new authorization, or real-account publish has been performed. -->
