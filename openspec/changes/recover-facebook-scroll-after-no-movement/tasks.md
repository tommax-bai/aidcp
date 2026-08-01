## 1. Native recovery implementation

- [x] 1.1 Carry a per-command foreground-activation budget from the Facebook `page.scroll` entry into the Feed executor so watchdog activation cannot be repeated.
- [x] 1.2 Add a focused same-document no-movement eligibility predicate covering movement, loading, list surface, bottom state, URL, generation, and time origin.
- [x] 1.3 Evaluate movement before card confirmation, activate the exact target once on an eligible miss, re-probe, and dispatch exactly one fresh recovery wheel.
- [x] 1.4 Return an ambiguous `scroll_movement_unconfirmed` result when the foreground recovery still makes no non-terminal movement, without adding JavaScript or Cloud fallbacks.

## 2. Regression coverage

- [x] 2.1 Add pure Native tests for recovery eligibility: movement, loading, bottom, document drift, surface drift, and a valid background miss.
- [x] 2.2 Add fake-CDP behavior tests proving background-first ordering, one activation and retry on a valid miss, zero activation after movement or context drift, watchdog at-most-once, and ambiguous second miss.

<!-- Evidence: aidcp-edge@5f88dab adds focused pure predicates plus fake-CDP ordering, activation-budget, drift, identity-acquisition, watchdog, and ambiguous-second-miss coverage. -->

## 3. Validation and integration

- [x] 3.1 Run focused Native tests for Facebook Feed scrolling and the fake-CDP command path.
- [x] 3.2 Run the serial Native gate and Edge TypeScript typecheck with isolated worktree dependencies.
- [x] 3.3 Run `openspec validate recover-facebook-scroll-after-no-movement --strict` and record the predecessor archive-order constraint.
- [x] 3.4 Commit and integrate the control and Edge source changes with validation evidence; do not package or claim installed-client delivery.

<!-- Validation: focused Feed unit tests 2/2; focused fake-CDP scroll tests 4/4; identity-acquisition regression 1/1; RUST_TEST_THREADS=1 npm run gate:native:test; npm run gate:native:clippy; npm run gate:native:fmt; npm run typecheck; openspec validate recover-facebook-scroll-after-no-movement --strict. -->
<!-- Integration: aidcp-edge@5f88dab is fast-forwarded and pushed to master; this control change is based on origin/main. limit-facebook-scroll-foreground-to-watchdog remains unarchived and must be applied before this superseding delta when archiving. No Edge package, installed-client update, or deployment was performed. -->
