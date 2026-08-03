## 1. Edge Supervisor Repair

- [x] 1.1 Use the lifecycle-frozen Cloud key for the initial target projection and remove the undeclared alias.
- [x] 1.2 Establish launch readiness and register named child observers immediately after assuming child ownership.
- [x] 1.3 Guard proxy-pipe, queue-release, and initial-status setup so synchronous failures settle, surface, terminate, and reap without a ghost handle.

## 2. Regression Coverage

- [x] 2.1 Add a focused Electron CJS undeclared-identifier gate and target-projection regression assertions.
- [x] 2.2 Add lifecycle-order and post-spawn failure contract coverage, preserving immediate `exit` capacity release and bounded `close` finalization.

  <!-- aidcp-edge: executable fake ChildProcess coverage verifies success, missing stdio, setup throw, post-spawn kill error, code=0 retry semantics, proxy no-respawn, and one-time reap. -->

## 3. Validation and Delivery Evidence

- [x] 3.1 Run focused Electron lifecycle/target tests and `node --check` in the isolated Edge worktree.
- [x] 3.2 Run the full Edge test suite, typecheck, and `openspec validate repair-edge-child-spawn-lifecycle --strict`.

  <!-- aidcp-edge 67973b4: acceptance 39/39; full suite 3074 passed, 1 gated real-machine test skipped; typecheck passed; node --check passed for both CJS files. aidcp: strict OpenSpec validation passed. -->

- [x] 3.3 Record repository commits, validations, deviations, and the explicit no-package/no-install/no-deploy boundary.

  <!-- Repositories: aidcp-edge 67973b4; aidcp 1bd23c25 (OpenSpec artifacts). Validation: focused lifecycle/target/proxy tests, acceptance 39/39, full Edge 3074 passed with 1 gated real-machine skip, typecheck, two CJS syntax checks, diff checks, and strict OpenSpec all passed. Deviation: a narrow injectable child-startup helper makes ordering/error classification executable; design was updated accordingly. Boundary: no package, installer, local install, deployment, settings/profile deletion, or real-account action was performed. -->
