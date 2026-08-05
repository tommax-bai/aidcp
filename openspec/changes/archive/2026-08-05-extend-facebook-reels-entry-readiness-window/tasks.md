## 1. Regression Coverage

- [x] 1.1 Add Native regression coverage that fixes the Reels entry document-readiness window at 30 seconds for both navigation attempts.
- [x] 1.2 Add a timeout-chain tripwire proving two 30-second readiness windows plus two 15-second identity windows and explicit non-wait margin fit below the existing 180-second Facebook scroll/session budget.

## 2. Edge Implementation

- [x] 2.1 Introduce one named Reels-entry readiness constant and replace only the initial and optional retry eight-second waits with the 30-second value.
- [x] 2.2 Preserve all unrelated Facebook readiness waits, the 15-second canonical identity window, retry count, blockers, cancellation/deadline gates, and outcome semantics.

## 3. Validation And Delivery

- [x] 3.1 Run focused Reels/timeout tests, Native formatting and clippy gates, and Edge typecheck.
- [x] 3.2 Run the serialized Native test gate and `openspec validate extend-facebook-reels-entry-readiness-window --strict`.
- [x] 3.3 Record repository, commit, validation, packaging, installation, and deployment boundaries; then integrate and push the Edge and control changes without packaging.

## Delivery Evidence

- Edge repository: `aidcp-edge`, feature commit `c9ecfe4ffe0a11aef0e5055bda6cea80d042a5a3` after rebase onto `origin/master` at `b9f9979`.
- Control repository: this OpenSpec change on `codex/extend-facebook-reels-entry-readiness-window`; the resulting control commit is reported in the delivery closeout.
- Focused validation: timeout-chain contract 6/6; Reels-entry Native regression 1/1; Native fmt and clippy gates; Edge typecheck.
- Broader validation after rebase: full Edge tests 3,101 passed with one real-device case gated; Edge acceptance 39/39; Native fmt, clippy, and serialized test gates completed with zero failures, including 200 library tests and 75 Fake CDP integration tests; strict OpenSpec validation passed.
- Timeout review: the two 30-second readiness windows plus two 15-second identity windows and a 30-second non-wait margin total 120 seconds, so the existing 180-second request/admission/engine/session limits and 240-second Cloud idle watchdog remain unchanged.
- Runtime boundary: no Edge package was built or installed, no Cloud or Console code was changed, no deployment was performed, and no real-account acceptance was claimed.
