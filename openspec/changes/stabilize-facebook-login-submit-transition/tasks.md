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
- [x] 3.3 Record repo commits, validation evidence, integration/push status, and the no-package/no-live-account boundary in this task file.
  <!-- aidcp-edge 11b1984010ba1ea93da6571377f19f49c472720b and aidcp 1e939c1d were integrated and pushed to origin/master and origin/main respectively after all task 3.1/3.2 gates passed. This closeout record lands in a follow-up control-only commit. No desktop package/install and no live-account action were performed. -->

## 4. TOTP Paste And Recovery Follow-up

- [x] 4.1 Bind the TOTP input by stable structural identity and classify non-empty orphan values as clear-only refresh signals without weakening pre-action top-hit checks.
- [x] 4.2 Replace per-character Facebook TOTP entry with one focus-guarded CDP `Input.insertText` call for the complete six-digit code and retain exact same-field readback.
- [x] 4.3 Preserve the Native auth action reason, clear orphan TOTP text only under proven fresh-start authority, and retain unproven active browsers as manual-required instead of code-1 restart loops.

## 5. Follow-up Regression And Delivery

- [x] 5.1 Add router, Native, and coordinator regressions covering the filled email/password page through full TOTP entry/submit/authentication, layout reflow, precise failure reasons, and proven/unproven orphan recovery.
  <!-- Focused TypeScript auth/router/assembly tests passed 47/47; Native Facebook auth integration tests passed 5/5; Edge typecheck and Rust formatting checks passed. -->
- [x] 5.2 Run focused Facebook auth tests, typecheck, acceptance, full Edge, Native, staged-artifact, and strict OpenSpec gates.
  <!-- Acceptance passed 31/31; full Edge tests passed 2888 with 0 failures and 1 gated E2E skip; Native fmt/clippy/test passed; the focused Native Facebook auth suite passed 5/5 after its final assertion; staged Native artifact verification and strict OpenSpec validation passed. -->
- [x] 5.3 Record follow-up commits, validation evidence, integration/push status, and the no-package/no-live-account boundary.
  <!-- aidcp-edge 0a211aa and aidcp 5c344dce were integrated and pushed to origin/master and origin/main respectively after all task 5.1/5.2 gates passed. This closeout record lands in a follow-up control-only commit. No desktop package/install and no browser input, lifecycle mutation, or live-account action were performed. -->

## 6. Live TOTP Hydration And Refresh Recovery

- [x] 6.1 Classify zero Continue controls after confirmed owned TOTP entry as bounded hydration while preserving ambiguity and pre-action occlusion failures.
- [x] 6.2 Bind refresh signals to the unchanged field value and keep Native clear fresh-probes clear-only, including complete six-digit orphan recovery under proven fresh-start authority.
- [x] 6.3 Retain unproven empty TOTP pages as manual-required, republish changed manual reasons, and project enumerated 2FA or exhausted-probe reasons as desktop `需处理` state.

## 7. Live Regression Coverage

- [x] 7.1 Add router and coordinator coverage for delayed Continue hydration, expiry during hydration, safe clear, fresh code entry, and authenticated completion without duplicate broker or input actions.
- [x] 7.2 Add Native coverage proving complete orphan clear uses CDP key events only, rejects changed-value stale signals, and confirms empty same-field readback.
- [x] 7.3 Add retained-session and UI coverage proving stale, empty, and exhausted-probe manual states remain blocked while genuine failed results still map to code 1.

## 8. Validation And Delivery

- [x] 8.1 Run focused Facebook auth/router/Native/UI tests and Edge typecheck in the isolated worktree.
  <!-- Focused TypeScript auth/router/coordinator/manual-session/UI tests passed 114/114 plus assembly 5/5; focused Native Facebook auth passed 6/6; Native fmt and Edge typecheck passed. -->
- [x] 8.2 Run acceptance, full Edge, Native, staged-artifact, and strict OpenSpec gates without weakening fail-closed assertions.
  <!-- Acceptance passed 31/31; full Edge passed 2892 with 0 failures and 1 gated E2E skip; Native fmt/clippy/all tests passed; the staged darwin-arm64 artifact verified at SHA-256 f281d16677df7d3661d77e654b810233ce0205512ee43ddb5175214325183945 after rebasing onto origin/master; strict OpenSpec validation passed. -->
- [x] 8.3 Record commits, validation evidence, integration/push status, and the no-package/no-browser-action boundary.
  <!-- aidcp-edge 2c3aa5d and aidcp 9eef6758 were integrated and pushed to origin/master and origin/main respectively after all task 8.1/8.2 gates passed. This closeout record lands in a follow-up control-only commit. No desktop package/install and no browser input, lifecycle mutation, or live-account action were performed. -->

## 9. Out-Of-Form TOTP Submit Binding

- [x] 9.1 Resolve one page-wide unique visible Continue control that shares a non-root structural ancestor with the exact TOTP input instead of restricting submission to the input's nearest form, without letting hidden templates compete for action authority.
- [x] 9.2 Require the bound Continue to be enabled and topmost; classify native-disabled, `disabled`, or `aria-disabled=true` as read-only hydration while preserving ambiguity, unrelated scope, and occlusion as blockers.
- [x] 9.3 Reuse the same resolver in the TOTP postcondition so disabled, covered, ambiguous, or temporarily out-of-scope controls cannot prove signal disappearance.

## 10. Structural Regression Coverage

- [x] 10.1 Add router coverage for the observed input-form/outer-footer structure, hidden-template coexistence, disabled and `aria-disabled` hydration, page-wide visible ambiguity, unrelated root scope, and enabled transition.
- [x] 10.2 Add Native action coverage proving a fresh re-probe that becomes disabled dispatches zero CDP input, while an enabled out-of-form control retains the existing one-click and bounded postcondition path.

## 11. Validation And Delivery

- [x] 11.1 Run focused Facebook auth router/Native tests and Edge typecheck in the isolated worktree.
  <!-- Focused TypeScript auth/router/assembly/manual-session tests passed 54/54; focused Native Facebook auth passed 7/7; Edge typecheck passed after rebasing onto the latest origin/master. -->
- [x] 11.2 Run acceptance, full Edge, Native, staged-artifact, and strict OpenSpec gates without weakening fail-closed assertions.
  <!-- Acceptance passed 31/31; full Edge reported 2920 tests with 2919 passed, 0 failed, and 1 gated E2E skip; Native fmt/clippy/all tests passed serially with 179 unit tests plus every integration suite; the staged darwin-arm64 artifact verified at SHA-256 2455f172dadf7b3d0a060983d20381d40d9d112a31871e75d7044a79cbc3413a; strict OpenSpec validation passed. -->
- [ ] 11.3 Record commits, integration/push status, and the explicit no-package/no-install/no-browser-action boundary.
