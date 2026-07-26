## 1. Serialize the behavior changes

- [ ] 1.1 Inspect the final Feed Like, Reels Interaction, and Group Join feature commits and record their overlapping files, behavior ownership, validation, and real-account boundaries
- [ ] 1.2 Rebase, validate, and land Reels Interaction to Edge `master` and control `main` without force
- [ ] 1.3 Rebase Group Join onto the integrated Reels revision, resolve behavior conflicts, rerun focused validation, and land both repositories
- [ ] 1.4 Rebase Feed Like onto the integrated Reels/Join revision, retain the Reels-owned path, rerun focused validation, and land both repositories

## 2. Establish executable capability ownership

- [ ] 2.1 Add a closed Native Facebook command-to-capability ownership table and reject supported commands without exactly one owner
- [ ] 2.2 Add the behavior-parity ledger covering each supported command's oracle, witness, commit primitive/count, verification, terminal semantics, and deadline
- [ ] 2.3 Add focused validation that the support table, ownership table, ledger, router dispatch, and behavior tests remain complete and consistent

## 3. Extract the Native Facebook runtime

- [ ] 3.1 Create the Facebook runtime entrypoint and move Facebook session state, support admission, blocker/consent gates, and terminal receipt helpers out of the generic engine
- [ ] 3.2 Extract Feed startup, settle, continuation, scroll, refresh, search, open/back, and card projection into the Feed capability module without changing behavior
- [ ] 3.3 Extract Feed Like target/commit/picker/verify choreography into the Feed Like capability module and keep its focused parity tests green
- [ ] 3.4 Extract Reels projection, movement, Like, Follow, author association, and same-Reel verification into the Reels capability module and keep its focused parity tests green
- [ ] 3.5 Extract current-group scope, readiness, hydration, fresh Join commit, verification, and receipt classification into the Group Join capability module
- [ ] 3.6 Extract Comment and Publish workflows into separate capability modules while preserving exact-target, input-readback, acknowledgement, ambiguous-submit, media, and capture semantics
- [ ] 3.7 Reduce the generic engine to platform dispatch and shared lifecycle/CDP concerns, with no command-specific Facebook locating or actuation branches

## 4. Split and assemble the embedded Facebook router

- [ ] 4.1 Add an explicit deterministic router source manifest and shared bounded DOM/identity helper module
- [ ] 4.2 Extract session/feed, Feed Like, Reels, Group Join, Comment, and Publish router modules without changing their command results
- [ ] 4.3 Make Native build encoding and TypeScript router tests consume the same assembled source set and fail on missing, duplicate, or reordered modules
- [ ] 4.4 Extend production-dist and desktop build-input inspection to reject every Facebook router fragment and representative marker outside the encoded Native artifact

## 5. Verify deadlines and behavior invariants

- [ ] 5.1 Verify one absolute command deadline flows from the facade through Native execution and that only Group Join receives the 90-second deadline
- [ ] 5.2 Add Rust/facade cases proving capability phases use remaining budget, ordinary commands retain 30 seconds, and a slow Join retains its durable verification window
- [ ] 5.3 Run the legacy Facebook behavior oracles and focused Native Feed, Reels, Join, Comment, Publish, blocker, consent, and unsupported-command parity suites

## 6. Validate and deliver

- [ ] 6.1 Run Cargo format, clippy, library/full tests, focused Edge tests, and protocol acceptance with bounded evidence
- [ ] 6.2 Run the full Edge suite, typecheck, Native build/verification, production dist build, and desktop build-input verification
- [ ] 6.3 Run `openspec validate preserve-native-facebook-capability-boundaries --strict`
- [ ] 6.4 Rebase, record Edge/control commits and validation/deviation evidence, fast-forward integrate, and push default branches without force
- [ ] 6.5 Rebuild the local development Native artifact and record that installer, signing, deployment, and real-account write acceptance were not performed
