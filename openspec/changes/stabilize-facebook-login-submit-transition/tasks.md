## 1. Native Postcondition Semantics

- [x] 1.1 Update the Facebook auth router so a login submit target that is still present but temporarily non-topmost cannot satisfy the post-action disappearance condition.
- [x] 1.2 Apply the same indeterminate post-action handling to the Facebook TOTP submit target while preserving structural disappearance and document-change confirmation.
- [x] 1.3 Set the bounded Native postcondition window to 200 ms for 35 polls (7 seconds) and lock the budget with a focused unit assertion.

## 2. Regression Coverage

- [x] 2.1 Add focused router tests proving pre-action occlusion remains non-actionable and post-action occlusion remains unsatisfied for login submit.
- [x] 2.2 Add equivalent TOTP submit coverage and retain true target-removal/document-transition confirmation coverage.

## 3. Validation And Delivery

- [x] 3.1 Run focused Facebook auth router/action tests and Edge typecheck in the isolated worktree.
  <!-- Focused TypeScript auth/router/assembly tests passed 43/43; Edge typecheck passed; focused Native seven-second receipt-window test passed 1/1. -->
- [x] 3.2 Run the applicable acceptance, full Edge, and Native gates plus strict OpenSpec validation; investigate any failure without weakening fail-closed assertions.
  <!-- Acceptance passed 31/31; full Edge tests passed 2868 with 0 failures and 1 gated E2E skip; Native fmt/clippy/test passed with 168 unit tests plus integration suites; staged Native artifact verification and strict OpenSpec validation passed. -->
- [ ] 3.3 Record repo commits, validation evidence, integration/push status, and the no-package/no-live-account boundary in this task file.
