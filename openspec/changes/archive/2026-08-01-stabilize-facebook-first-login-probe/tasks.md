## 1. Coordinator regression coverage

- [x] 1.1 Add focused tests proving an allowlisted read-only Native auth probe failure resets the owner session and succeeds on a later bounded probe.
- [x] 1.2 Add focused tests proving contract/unknown probe failures remain terminal and Native action exceptions are never retried.
- [x] 1.3 Add focused coverage proving 20-second transient-probe exhaustion enters the controlled manual-login wait without an action or process restart.

## 2. Edge implementation

- [x] 2.1 Classify bounded non-secret `NativePageEngineError` details for Facebook startup auth commands.
- [x] 2.2 Rebuild the Native startup-auth owner session and retry only allowlisted read-only probe failures for at most 20 seconds within the shared deadline using bounded backoff.
- [x] 2.3 Preserve existing interruption, timeout, fresh-start policy, signal-id replay, TOTP, and stable-identity boundaries.

## 3. Validation and delivery

- [x] 3.1 Run the focused Facebook auth/runtime tests and TypeScript typecheck in the isolated Edge worktree.
- [x] 3.2 Run the applicable Native acceptance/gate and full Edge test suite; investigate failures without weakening safety assertions.
- [x] 3.3 Run `openspec validate stabilize-facebook-first-login-probe --strict` and record repo, commit, validation, delivery boundary, and deviations.
- [x] 3.4 Rebase, integrate, and push the validated Edge and control-repo changes; do not package or install an Edge client without explicit release scope.

<!-- Implementation: aidcp-edge commit a0163e99cecea2c6ddd4c51b59b9b51b95e0cbe8. Validation: focused facebook-auth 18/18; test:acceptance 31/31 with one gated E2E skip; npm test 2861 passed, 0 failed, 1 gated E2E skip; npm run typecheck passed; RUST_TEST_THREADS=1 npm run gate:native passed; openspec strict validation passed. Delivery boundary: source integration only, with no packaging, installation, deployment, or real-account login attempt. Deviations: none. -->
<!-- Integration: aidcp-edge a0163e99cecea2c6ddd4c51b59b9b51b95e0cbe8 was rebased onto origin/master, the landing gate repeated acceptance/full/typecheck/Native validation, and origin/master plus the canonical checkout were fast-forwarded. -->
<!-- Control contract: aidcp 1b8f961736fc190dc9d4bddf6b7fd4c4618b68b9 records the validated proposal, design, spec delta, and completed tasks. -->
