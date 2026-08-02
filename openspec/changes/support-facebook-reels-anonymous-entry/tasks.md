## 1. Regression Coverage

- [x] 1.1 Add Fake CDP entry regressions for canonical hydration before commit and anonymous horizontal/vertical entry advancing to exactly one matching canonical Reel.
- [x] 1.2 Add fail-closed regressions for missing, ambiguous, unsafe, unchanged, and moved-but-unidentified entry states, including zero later input and pending read-only recovery assertions.
- [x] 1.3 Add focused Rust coverage that rejects anonymous, invalid-host, non-Reel, non-video, non-ready, `content_ref`, multiple, previous-ID, and active-card-mismatched Reels completion batches.

<!-- Evidence: aidcp-edge Fake CDP covers horizontal/vertical entry, boundary and post-input hydration, cancellation, surface loss, missing/ambiguous/unsafe targets, ordinary stale identity, read-only recovery, and persistent second-drift rejection. Rust unit coverage enforces the exact canonical active-card envelope. -->

## 2. Edge Implementation

- [x] 2.1 Add exact canonical active-Reel completion validation and split entry hydration from post-transition completion without changing the 15-second window.
- [x] 2.2 Connect a freshly revalidated anonymous entry to one bounded Reels navigation invocation with cancellation/deadline reserve and no second entry navigation.
- [x] 2.3 Retain a two-live-phase session-local pending transition plus terminal target-drift state after uncertain entry input or ordinary unresolved movement, and make later scroll commands recover it read-only before any new navigation.

<!-- Implementation: aidcp-edge native/page-engine; no Cloud, Console, protocol, database, policy, or pacing change. -->

## 3. Validation And Delivery

- [x] 3.1 Run focused Reels Native tests, Native formatting and clippy gates, and Edge typecheck.
- [x] 3.2 Run the serialized Native test gate and `openspec validate support-facebook-reels-anonymous-entry --strict`.
- [x] 3.3 Record repository, commit, validation, packaging, installation, deployment, and real-account boundaries; then integrate and push the Edge and control changes.

<!-- Validation: focused Reels regressions passed; gate:native:fmt, gate:native:clippy, serialized gate:native:test, test:acceptance (38/38), full Edge tests (3037 passed, 1 gated E2E skipped), typecheck, git diff --check, and strict OpenSpec validation passed. -->
<!-- Delivery: aidcp-edge commit 63ddaf7 was fast-forwarded to origin/master and the canonical checkout. The control artifacts are delivered by the commit containing this evidence. Source-only boundary: package=no; installed-client replacement=no; deployment=no; real-account action/verification=no. -->
