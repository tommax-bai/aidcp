# Tasks — client-login-credential-persistence

## 1. aidcp-edge implementation

- [x] 1.1 Add main-process safeStorage-backed read/write/clear helpers for login prefill. <!-- aidcp-edge 7a07a78 -->
- [x] 1.2 Save the successful client login input and clear it with the existing session invalidation/logout path. <!-- aidcp-edge 7a07a78 -->
- [x] 1.3 Expose narrow preload IPC methods for login-page prefill and explicit clear. <!-- aidcp-edge 7a07a78 -->
- [x] 1.4 Load prefill on the login page and clear it when either field is manually emptied. <!-- aidcp-edge 7a07a78 -->

## 2. Tests and validation

- [x] 2.1 Add source-contract tests covering encrypted storage, success save, logout/session invalidation clear, login-page prefill, and manual-empty clear. <!-- aidcp-edge 7a07a78: focused contract 5/5 -->
- [x] 2.2 Run the focused contract test, `npm run typecheck`, and `npm run test:acceptance` in `aidcp-edge`. <!-- aidcp-edge 7a07a78: typecheck pass; acceptance 16/16; full npm test 1087/1087; no lockfile changes -->
- [x] 2.3 Run `openspec validate client-login-credential-persistence --strict` in the control repo. <!-- control repo validation passed 2026-07-13 -->

## 3. Manual acceptance backlog

- [ ] 3.1 Packaged desktop manual check: successful login repopulates the next login window; deleting either field prevents the old pair from returning; logout returns to a blank login form.
