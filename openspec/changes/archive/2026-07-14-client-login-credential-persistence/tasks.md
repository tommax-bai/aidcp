# Tasks — client-login-credential-persistence

## 1. aidcp-edge implementation

- [x] 1.1 Add main-process safeStorage-backed read/write/clear helpers for login prefill. <!-- aidcp-edge 183bf91 -->
- [x] 1.2 Save the successful client login input and clear it with the existing session invalidation/logout path. <!-- aidcp-edge 183bf91 -->
- [x] 1.3 Expose narrow preload IPC methods for login-page prefill and explicit clear. <!-- aidcp-edge 183bf91 -->
- [x] 1.4 Load prefill on the login page and clear it when either field is manually emptied. <!-- aidcp-edge 183bf91 -->

## 2. Tests and validation

- [x] 2.1 Add source-contract tests covering encrypted storage, success save, logout/session invalidation clear, login-page prefill, and manual-empty clear. <!-- aidcp-edge 183bf91: focused contract 5/5 -->
- [x] 2.2 Run the focused contract test, `npm run typecheck`, and `npm run test:acceptance` in `aidcp-edge`. <!-- aidcp-edge 183bf91: typecheck pass; acceptance 16/16; full npm test 1087/1087; no lockfile changes -->
- [x] 2.3 Run `openspec validate client-login-credential-persistence --strict` in the control repo. <!-- control repo validation passed 2026-07-13 -->

## 3. Manual acceptance backlog

- [x] 3.1 Packaged desktop manual check: successful login repopulates the next login window; deleting either field prevents the old pair from returning; logout returns to a blank login form. <!-- 2026-07-14: decoupled to docs/real-machine-acceptance-backlog.md 簇 61.18-61.21 (shares the packaged-client + login-gate prerequisite with the rest of cluster 61). Archive is not gated on real-machine acceptance. -->

## 4. Ledger correction (2026-07-14)

- [x] 4.1 The sha this file originally recorded (`7a07a78`) was **never pushed to origin** — it only ever existed on the local branch `codex/client-login-credential-persistence`. The equivalent commit on `origin/master` is **`183bf91`** ("feat: remember client login credentials securely", same 4 files incl. `test/electron/client-login-prefill.test.ts`). Verified `183bf91` is an ancestor of `origin/master`, and master carries `clientLoginPrefillFile` / `saveClientLoginPrefill` / `clearClientLoginPrefill` in `src/electron/main.cjs`, the `client-auth:prefill` + `client-auth:prefill:clear` preload IPC, and the login-page prefill/clear wiring. Per the forward-port rule the acceptance criterion is "equivalent behavior on master + test coverage", not identical patch-id, so all shas above were rewritten to `183bf91`. <!-- control repo 2026-07-14 -->
- [x] 4.2 `openspec validate client-login-credential-persistence --strict`.
