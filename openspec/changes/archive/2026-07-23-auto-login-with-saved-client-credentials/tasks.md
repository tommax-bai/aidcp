## 1. Edge startup authentication

- [x] 1.1 Add a side-effect-free startup auth coordinator that validates an existing session and attempts saved credentials at most once.
- [x] 1.2 Reuse one main-process login function for manual and automatic login, preserving encrypted credentials on token invalidation while clearing them on explicit logout or definitive auto-login rejection.
- [x] 1.3 Gate `app.whenReady()` on startup auth recovery before any authenticated main window or environment startup.

## 2. Verification

- [x] 2.1 Add focused tests for valid-session reuse, successful saved-credential recovery, missing credentials, definitive rejection, transient failure, and the one-attempt invariant.
- [x] 2.2 Run focused Electron auth tests, the complete Edge test suite, and `npm run typecheck`.
  <!-- 2026-07-23: focused auth/lifecycle tests 18/18 passed; `npm test` 2261/2261 passed; `npm run typecheck` exit 0 in aidcp-edge.wt/auto-login-with-saved-client-credentials. -->

## 3. Delivery

- [x] 3.1 Update this checklist with Edge commit SHA and validation evidence, then run `openspec validate auto-login-with-saved-client-credentials --strict`.
  <!-- Edge commit: aidcp-edge 2b2d9dd4a439b6e72798b1755ec8e9b6083e11aa. Validation evidence: focused auth/lifecycle 18/18, full Edge 2261/2261, typecheck exit 0. -->
- [x] 3.2 Rebase and fast-forward the validated Edge change to `master`, push without force, and record the final source-delivery status without claiming an installer update.
  <!-- 2026-07-23: land-change rebase was current; acceptance 30/30, full Edge 2261/2261 and typecheck passed; 2b2d9dd4a439b6e72798b1755ec8e9b6083e11aa fast-forwarded and pushed to origin/master. Source delivered only; no installer was built or published. -->
