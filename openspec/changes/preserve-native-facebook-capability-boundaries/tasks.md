## 1. Serialize the behavior changes

- [x] 1.1 Inspect the final Feed Like, Reels Interaction, and Group Join feature commits and record their overlapping files, behavior ownership, validation, and real-account boundaries
  <!-- All three overlapped engine.rs, facebook.rs, facebook-command-router.js, and focused Native tests. Reels owns active-video Like/Follow, Group Join owns current-group/fresh DOM/timing, and Feed Like owns exact-card DOM/picker choreography. All remained source-only with real-account writes pending. -->
- [x] 1.2 Rebase, validate, and land Reels Interaction to Edge `master` and control `main` without force
  <!-- Edge 2228a20+d48c47b; control through 1e323d1. Focused 84/84, acceptance 30/30, full Edge pass, typecheck, Rust lib 51/51, and local Native artifact build passed. -->
- [x] 1.3 Rebase Group Join onto the integrated Reels revision, resolve behavior conflicts, rerun focused validation, and land both repositories
  <!-- Edge 938767d; control 75ee1af. Combined focused 74/74, Rust lib 55/55, Join Fake-CDP 2/2, acceptance 30/30, full Edge 2336/2336, and typecheck passed. -->
- [x] 1.4 Rebase Feed Like onto the integrated Reels/Join revision, retain the Reels-owned path, rerun focused validation, and land both repositories
  <!-- Edge d02b1bc; control cf4b9aa. Conflicts retained Join lifecycle/timing and all Reels/Feed operations. Combined focused 82/82, Rust lib 55/55, all three write-path Fake-CDP boundaries, typecheck, and full Edge 2344/2344 passed. -->

## 2. Establish executable capability ownership

- [x] 2.1 Add a closed Native Facebook command-to-capability ownership table and reject supported commands without exactly one owner
- [x] 2.2 Add the behavior-parity ledger covering each supported command's oracle, witness, commit primitive/count, verification, terminal semantics, deadline, and protected commit-window contract
- [x] 2.3 Add focused validation that the support table, ownership table, ledger, router dispatch, and behavior tests remain complete and consistent
  <!-- `facebook/capability.rs` is the closed support/ownership/parity source. Rust completeness tests and Edge source-boundary tests require one owner, one ledger entry, and one focused suite per supported command. -->

## 3. Extract the Native Facebook runtime

- [x] 3.1 Create the Facebook runtime entrypoint and move Facebook session state, support admission, blocker/consent gates, and terminal receipt helpers out of the generic engine
- [x] 3.2 Extract Feed startup, settle, continuation, scroll, refresh, search, open/back, and card projection into the Feed capability module without changing behavior
- [x] 3.3 Extract Feed Like target/commit/picker/verify choreography into the Feed Like capability module and keep its focused parity tests green
- [x] 3.4 Extract Reels projection, movement, Like, Follow, author association, and same-Reel verification into the Reels capability module and keep its focused parity tests green
- [x] 3.5 Extract current-group scope, readiness, hydration, fresh Join commit, verification, and receipt classification into the Group Join capability module
- [x] 3.6 Extract Comment and Publish workflows into separate capability modules while preserving exact-target, input-readback, acknowledgement, ambiguous-submit, media, and capture semantics
- [x] 3.7 Reduce the generic engine to platform dispatch and shared lifecycle/CDP concerns, with no command-specific Facebook locating or actuation branches
  <!-- Facebook runtime modules now own complete state machines; the generic engine delegates once through `facebook::runtime::execute` and contains no Facebook locator/router-expression or command-specific executor. -->

## 4. Split and assemble the embedded Facebook router

- [x] 4.1 Add an explicit deterministic router source manifest and shared bounded DOM/identity helper module
- [x] 4.2 Extract session/feed, Feed Like, Reels, Group Join, Comment, and Publish router modules without changing their command results
- [x] 4.3 Make Native build encoding and TypeScript router tests consume the same assembled source set and fail on missing, duplicate, or reordered modules
- [x] 4.4 Extend production-dist and desktop build-input inspection to reject every Facebook router fragment and representative marker outside the encoded Native artifact
  <!-- Ten capability-owned fragments are assembled from one ordered manifest by Rust and TypeScript. Production-dist/build-input/afterPack scanners reject fragments and representative page-rule markers outside the encoded Native binary. -->

## 5. Verify deadlines and behavior invariants

- [x] 5.1 Verify one absolute command deadline flows from the facade through Native execution and that only Group Join receives the 90-second deadline
- [x] 5.2 Add Rust/facade cases proving capability phases use remaining budget, ordinary commands retain 30 seconds, and a slow Join retains its durable verification window
- [x] 5.3 Add a correlated local commit-window request/ack lifecycle and wire Native Facebook Join, Comment, and Publish to the existing Edge `CommitWindowGuard`
- [x] 5.4 Prove no write occurs before a matching acknowledgement, the coordinator returns `window_busy` during the established window, and cancellation after expiry remains ambiguous without replay
- [x] 5.5 Run the legacy Facebook behavior oracles and focused Native Feed, Reels, Join, Comment, Publish, blocker, consent, and unsupported-command parity suites
  <!-- ACK carries an explicit host decision and is correlated to session/task/command/token/label. Join/Comment/Publish fail `not_started` before actuation when unavailable; post-submit cancellation remains `ambiguous`. Focused router/boundary parity passed 55/55. -->

## 6. Validate and deliver

- [x] 6.1 Run Cargo format, clippy, library/full tests, focused Edge tests, and protocol acceptance with bounded evidence
  <!-- Edge 746fdcd, 073eadc, and a6623a4 after rebase onto the independently landed identity-dist boundary. Cargo format/check and clippy `-D warnings` passed; Rust full tests passed 83/83; focused Edge router/boundary parity passed 55/55; protocol acceptance passed 30/30. -->
- [x] 6.2 Run the full Edge suite, typecheck, Native build/verification, production dist build, and desktop build-input verification
  <!-- Edge full suite passed 2350/2350; typecheck, production dist, desktop build-input, Native release build and verification passed. Worktree artifact SHA-256: a7371f10d0898ce96677f70a81faa4dd68a730ecfe2941692f7d007c308e95ad. -->
- [x] 6.3 Run `openspec validate preserve-native-facebook-capability-boundaries --strict`
  <!-- Strict validation passed after recording the implementation and source/artifact delivery boundary. -->
- [ ] 6.4 Rebase, record Edge/control commits and validation/deviation evidence, fast-forward integrate, and push default branches without force
- [ ] 6.5 Rebuild the local development Native artifact and record that installer, signing, deployment, and real-account write acceptance were not performed
