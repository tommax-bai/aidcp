## 1. Startup lifecycle settlement

- [x] 1.1 Add focused tests for confirmed close, failed close with explicit retry, and failed close followed by resume during pre-controller Facebook authentication.
- [x] 1.2 Route initial Facebook authentication interruptions through the existing owned-browser confirmed-close operation and block startup after unconfirmed closure.

## 2. Confirmed-close projection

- [x] 2.1 Add a core lifecycle callback and acknowledged local IPC for confirmed browser closure before process exit.
- [x] 2.2 Bind confirmed-close evidence to the Electron lifecycle generation and project missing evidence as unconfirmed instead of closed.
- [x] 2.3 Add focused core and Electron contract regressions for confirmed and missing browser-close evidence.

## 3. Validation and delivery

- [x] 3.1 Run focused startup-auth, core-lifecycle, Electron lifecycle, and AdsPower close tests.
- [x] 3.2 Run `npm run test:acceptance`, full `npm test`, and `npm run typecheck` in the Edge worktree.
- [x] 3.3 Run `openspec validate close-facebook-browser-during-startup-auth --strict` and record Edge commit, validation, delivery, and installer boundary evidence.
- [x] 3.4 Rebase the Edge and control branches on current defaults, fast-forward integrate them, and push `master`/`main` without building an installer.

## Evidence

- Edge implementation: `aidcp-edge` commit `bbfdb59e397c0a0273299206ffd2daecfb3d29ce`, fast-forwarded and pushed to `origin/master`.
- Focused validation: 126 startup-auth, lifecycle IPC/controller, Electron lifecycle/slot, manual-login, and AdsPower teardown tests passed; `git diff --check` passed.
- Release validation: `npm run test:acceptance` passed 39 tests; the second full `npx tsx --test --test-reporter=dot test/**/*.test.ts` run exited 0; `npm run typecheck` passed. The gated real-machine acceptance remained skipped because no real-account operation was authorized.
- Control validation: `openspec validate close-facebook-browser-during-startup-auth --strict` passed with all 4 artifacts complete.
- Delivery boundary: source and OpenSpec only. No Edge installer was built or installed, and no Cloud/Console service was changed or deployed.
