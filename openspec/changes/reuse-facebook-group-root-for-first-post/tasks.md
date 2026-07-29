## 1. Isolated setup

- [x] 1.1 Create same-named control and Edge worktrees from current defaults with `codex/reuse-facebook-group-root-for-first-post`, preserving unrelated canonical artifacts.
- [x] 1.2 Install a physical Edge worktree-local dependency tree with `npm ci --prefer-offline` before running tests.

## 2. Native group-root reuse

- [x] 2.1 Add one internal Facebook router probe and strict Rust decoder for the current target's exact group-root, readiness, blocker, scope, modal, feed-loading, and real-scroller state.
- [x] 2.2 Replace unconditional first-post root navigation with the fail-closed reuse decision, bounded decision diagnostics, cancellation preservation, and a single canonical navigation fallback.
- [x] 2.3 Bind every first-post candidate probe to the exact canonical group root, allowing only the reused branch's pre-acceptance canonical recovery while preserving the existing total scroll-round budget.
- [x] 2.4 Preserve the shared post-selection state reset, action gate, fixed scroll budget, permalink same-group checks, and accepted permalinkless bound-reference behavior in both branches.
<!-- Implemented in aidcp-edge commit 0c744131f8248734bb0898ce1c8123e10cae6bfa. No protocol or Cloud command shape changed. -->

## 3. Regression coverage

- [x] 3.1 Extend Facebook router contract tests for exact-root probe fields, full-URL context checks, blocker/loading/dialog evidence, and nested-scroller position.
- [x] 3.2 Extend fake CDP coverage so an exact ready group root performs zero root navigation, while mismatch/unknown state performs exactly one root navigation.
- [x] 3.3 Cover context change before candidate acceptance, context mismatch after navigation, malformed probe evidence, cancellation, permalink detail navigation, and bound-reference in-place detail.
<!-- Coverage also proves scroll-origin TOCTOU rejection before/after async card hydration and that canonical recovery does not reset the four-round scroll budget. -->

## 4. Validation and delivery

- [x] 4.1 Run focused Rust fake-CDP and Facebook router contract tests.
- [x] 4.2 Run Edge acceptance, full test, typecheck, Native gate/build, and Native build-input verification from the worktree.
- [x] 4.3 Run `openspec validate reuse-facebook-group-root-for-first-post --strict` and record exact validations, commits, delivery boundary, and deviations here.
- [ ] 4.4 Rebase onto current defaults, fast-forward integrate and push the Edge and control changes without force; do not deploy ECS or build an installer.
<!-- Validation after rebasing Edge onto origin/master: router contract 98/98; Native gate passed with RUST_TEST_THREADS=1 (138 lib tests and fake CDP 46/46, all Rust suites green); typecheck passed; acceptance 31 passed with one gated E2E skip; controlled-concurrency full Edge suite 2715 passed, one gated skip, zero failures; Native release build and verify passed with encoded-rules digest 5f0353945b274bbacea0b78949ce62d90ee94293fa0f010258daf5147dcff2c0; desktop build input passed. A default-concurrency full run exposed one unrelated WeChat timing flake; its focused test and full 48-test file both passed, and both controlled full runs were green. OpenSpec strict validation passed. Edge was fast-forward pushed to origin/master at 0c744131f8248734bb0898ce1c8123e10cae6bfa. No ECS deployment or installer build was in scope. -->
