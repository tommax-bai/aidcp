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
- [ ] 5.3 Record follow-up commits, validation evidence, integration/push status, and the no-package/no-live-account boundary.
