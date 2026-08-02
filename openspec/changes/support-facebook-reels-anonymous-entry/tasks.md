## 1. Regression Coverage

- [ ] 1.1 Add Fake CDP entry regressions for canonical hydration before commit and anonymous horizontal/vertical entry advancing to exactly one matching canonical Reel.
- [ ] 1.2 Add fail-closed regressions for missing, ambiguous, unsafe, unchanged, and moved-but-unidentified entry states, including zero later input and pending read-only recovery assertions.
- [ ] 1.3 Add focused Rust coverage that rejects anonymous, `content_ref`, multiple, and active-card-mismatched Reels completion batches.

## 2. Edge Implementation

- [ ] 2.1 Add exact canonical active-Reel completion validation and split entry hydration from post-transition completion without changing the 15-second window.
- [ ] 2.2 Connect a freshly revalidated anonymous entry to one bounded Reels navigation invocation with cancellation/deadline reserve and no second entry navigation.
- [ ] 2.3 Retain a session-local pending entry observation after uncertain input and make later scroll commands recover it read-only before any new navigation.

## 3. Validation And Delivery

- [ ] 3.1 Run focused Reels Native tests, Native formatting and clippy gates, and Edge typecheck.
- [ ] 3.2 Run the serialized Native test gate and `openspec validate support-facebook-reels-anonymous-entry --strict`.
- [ ] 3.3 Record repository, commit, validation, packaging, installation, deployment, and real-account boundaries; then integrate and push the Edge and control changes.
