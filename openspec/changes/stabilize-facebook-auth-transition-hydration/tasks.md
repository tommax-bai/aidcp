## 1. Reproduce the transition races

- [x] 1.1 Add Native router fixtures for an empty managed login form before/after 25 seconds and a live-shaped checkpoint before DOM hydration.
- [x] 1.2 Add regression coverage showing a hydrated automation warning independently binds one unique visible/topmost `Dismiss` target without depending on TOTP or another preceding action.

## 2. Implement bounded Facebook authentication hydration

- [x] 2.1 Extend managed AdsPower credential-fill observation to 25 seconds on the exact Facebook login document before returning `credential_fill_unavailable`.
- [x] 2.2 Keep a newly navigated, otherwise unknown Facebook checkpoint non-terminal for at most 15 seconds while preserving immediate fail-closed classification for explicit blockers, ambiguity, and unsafe targets.
- [x] 2.3 Preserve the existing Native `automation_warning_dismiss` signal, trusted pointer dispatch, postcondition verification, and one-signal/one-action lifecycle continuation.

## 3. Verify lifecycle honesty and safety

- [x] 3.1 Add coordinator/lifecycle assertions that in-window hydration stays in automatic startup without emitting premature manual or terminal state, while expired windows preserve existing safe reasons.
- [x] 3.2 Run focused Facebook auth router/coordinator/UI tests, Native formatting/lint/tests, acceptance coverage, and Edge typecheck with bounded output.
  <!-- Edge validation: focused Facebook auth/router/UI tests 52 passed; acceptance 38 passed and 1 gated E2E skipped; `npm run typecheck` passed; `RUST_TEST_THREADS=1 npm run gate:native` passed fmt, clippy, and Native tests. -->
- [x] 3.3 Run `openspec validate stabilize-facebook-auth-transition-hydration --strict` and `git diff --check` in both owning repositories.
  <!-- Control validation: strict OpenSpec validation passed. Edge and control `git diff --check` passed. -->

## 4. Deliver source changes with explicit boundaries

- [x] 4.1 Commit the isolated Edge change, integrate it through the fast-forward workflow, push `master`, and record the Edge commit and validation evidence here.
  <!-- aidcp-edge c8e26e435aa6929f610bec73a2f496da95276f30; pushed to master by fast-forward. After the final rebase, 159 relevant Facebook/router tests, typecheck, 84 Native Facebook library tests, and 7 Native Facebook auth integration tests passed. The preceding final-base gate passed Native fmt, clippy, and all Native tests; focused auth remained 52/52 and acceptance remained 38 passed with the gated real E2E not run. -->
- [ ] 4.2 Commit and push the control-repo OpenSpec artifacts with explicit pathspecs while preserving unrelated files; record that no desktop package, installation, deployment, or real-account action was performed.
