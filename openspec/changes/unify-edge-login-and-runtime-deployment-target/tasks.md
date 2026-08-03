## 1. Deployment target authority

- [x] 1.1 Add one normalized `deploymentTarget` setting with DEV/OL endpoint tuples and compatibility migration from official legacy selectors/default metadata.
- [x] 1.2 Remove active baked, persisted, and inherited single-URL precedence from official Electron customer-auth and automation resolution.
- [x] 1.3 Bind pending local Cloud-mutation cursors to their originating target and prevent cross-target replay or ambiguous legacy replay.
- [x] 1.4 Add focused resolver, migration, and fail-closed target consistency tests.
  <!-- Evidence: `aidcp-edge` commit `9cc7b9cfa05a3cdaf3ae1f67121a5875f82d19b5` adds the frozen paired target catalog, official-key migration, unconditional Electron WebSocket override, and target-scoped offboard replay with unknown legacy records blocked and surfaced. -->

## 2. Target-scoped authentication

- [x] 2.1 Add `deploymentTarget` to encrypted session and credential records; reject legacy/mismatched records and constrain refresh/prefill to the selected target.
- [x] 2.2 Extend the login page with accessible DEV/OL selection, production/test labeling, target-aware submit copy, and target-specific errors.
- [x] 2.3 Narrow login IPC to a validated target enum plus credentials, persist the target before network login, and block login when target persistence fails.
- [x] 2.4 Add startup, login, prefill, session migration, and cross-target credential regression tests.
  <!-- Evidence: `aidcp-edge` commit `9cc7b9cfa05a3cdaf3ae1f67121a5875f82d19b5` binds encrypted sessions/prefill to the target, rejects target-less or mismatched records, validates the exact three-field login payload, and saves the target before `/login`. -->

## 3. Safe target transition and truthful UI

- [x] 3.1 Replace authenticated URL selection/partial WebSocket rebinding with an explicit stop, logout, authority-clear, and return-to-login target transition.
- [x] 3.2 Preserve physical browser roster settings while clearing target-scoped visible environments, bindings, exclusions, and active automation authority.
- [x] 3.3 Display authenticated target separately from confirmed automation target and include confirmed DEV/OL in browser-slot waiting activity.
- [x] 3.4 Add transition, stopped-engine, mismatch, activity-copy, and renderer regression tests.
  <!-- Evidence: `aidcp-edge` commit `9cc7b9cfa05a3cdaf3ae1f67121a5875f82d19b5` removes the customer hot-rebind IPC/UI, retains the physical roster on logout-to-switch, rejects mismatched connection receipts, and projects `自动化通道已连接 DEV|OL，等待浏览器槽位` only from a confirmed connection. -->

## 4. Desktop build contract

- [x] 4.1 Remove `aidcpClientAuthUrl` injection and `AIDCP_CLIENT_AUTH_URL` build inputs from package scripts, macOS helpers, and CI workflows.
- [x] 4.2 Update package verification and release documentation to assert a valid default target/catalog and absence of active baked auth URL routing.
- [x] 4.3 Update focused package/build-input tests without producing a desktop installer.
  <!-- Evidence: `aidcp-edge` commit `9cc7b9cfa05a3cdaf3ae1f67121a5875f82d19b5` removes the independent URL from npm scripts, CI inputs, Windows/macOS build commands and local OL helpers; mounted-ASAR verification now rejects that metadata. -->

## 5. Validation and delivery

- [x] 5.1 Run focused Electron target/auth/UI/package tests and syntax checks.
- [x] 5.2 Run Edge acceptance/full tests and `npm run typecheck`, then fix only regressions caused by this change.
- [x] 5.3 Run `openspec validate unify-edge-login-and-runtime-deployment-target --strict` and record validation plus the explicit no-package/no-install/no-deploy/no-OL boundary.
  <!-- Validation: focused target/auth/UI/package regressions passed 80/80; the full `aidcp-edge` suite passed 3070 with 1 gated real-device E2E skipped; `npm run typecheck`, `npm run verify:desktop-build-input`, syntax checks, `git diff --check`, and strict OpenSpec validation passed. No installer was packaged or installed, no service was restarted or deployed, no OL/DEV endpoint was contacted, and no real-account action was run. -->
- [x] 5.4 Commit Edge and control changes, rebase/fast-forward integrate into current defaults, rerun required validation, and push without force.
  <!-- Evidence: `aidcp-edge` `9cc7b9cfa05a3cdaf3ae1f67121a5875f82d19b5` and control `988277e0` were confirmed current with `origin/master` and `origin/main`, rebased as no-ops, fast-forward integrated, and pushed without force. Post-rebase focused regressions passed 68/68, typecheck passed, and strict OpenSpec validation passed. -->
