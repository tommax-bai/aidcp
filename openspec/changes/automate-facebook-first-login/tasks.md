## 1. AdsPower Startup And Secret Boundary

- [x] 1.1 Add the fresh-start AdsPower body fields for first-open credential filling and disabled browser password saving, preserving permission-prompt suppression and active-profile honesty.
- [x] 1.2 Add a profile-bound Electron TOTP IPC operation that reads one exact AdsPower V2 profile, validates the server-time request, computes one code, and returns no raw login material.
- [x] 1.3 Add provider, Local API, Electron broker, redaction, profile-mismatch, and TOTP-window tests.

## 2. Native Facebook Signal And Action Support

- [x] 2.1 Add Native command and receipt types for Facebook auth probing and the independent login, TOTP-entry, TOTP-submit/clear, warning, push-blocker, and Remember Password actions.
- [x] 2.2 Implement mutually exclusive Facebook auth signal detection with target/document-bound signal ids, CAPTCHA/unknown classification, visibility, uniqueness, top-hit checks, and shared stable numeric `c_user` plus non-empty `xs` authentication evidence.
- [x] 2.3 Implement one signal-specific Native CDP action per command with fresh signal revalidation, cancellation/deadline support, and a signal-local postcondition.
- [x] 2.4 Add Rust/router tests proving stale, ambiguous, CAPTCHA, unknown, wrong-signal, blank/non-numeric user-cookie, lookalike-domain, and empty-session-cookie cases fail closed, dispatch zero unintended input, and never replay a signal id.

## 3. Bounded Startup Reconciler

- [x] 3.1 Add the TypeScript Facebook auth coordinator that probes, executes at most one matching action, re-probes without assuming order, and honors the existing login-wait/cancellation budget.
- [x] 3.2 Implement Facebook server-time sampling and the 30-second TOTP window rule, including waiting below 10 seconds and clearing rather than submitting a newly stale code.
- [x] 3.3 Invoke the idempotent coordinator after initial attach and cold-standby reattach, before the read-only stable-identity gate, while retaining logged-in no-op behavior.
- [x] 3.4 Add coordinator and startup-assembly tests for optional/reordered signals, one-action passes, timeout/interruption, TOTP boundaries, and Native-only routing.

## 4. Validation And Delivery

- [x] 4.1 Run focused provider/Electron/Native/coordinator tests and the Facebook safety acceptance suites.
  <!-- Edge validation: focused TypeScript 185/185 and Facebook safety acceptance 31/31 passed. -->
- [x] 4.2 Run the full edge test suite, typecheck, Native Page Engine build/tests, and strict OpenSpec validation.
  <!-- aidcp-edge commits: a393004 and 61a0753. Full TypeScript suite and typecheck exited 0; Native fmt, clippy, 167 unit tests, and all integration suites passed; the unsigned darwin-arm64 release artifact was rebuilt and verified after the auth-cookie fix. OpenSpec strict validation passed in the control worktree. Delivery remains feature-source only: no deployment or installer; the incomplete live-gate deviation is recorded in 4.3. -->
- [ ] 4.3 After every code-level gate passes, run one final AIDCP-source validation against only the third imported stable Facebook profile and record safe per-signal/postcondition evidence without credentials, TOTP, cookies, or raw AdsPower responses.
  <!-- One bounded live attempt applied the fresh-start policy, attached CDP/Native, returned an `authenticated` signal from cookie-name-only evidence, dispatched zero login actions, then stopped at `stable_identity_unconfirmed`; the browser was closed. Source now requires the same numeric `c_user` criterion as stable identity plus non-empty `xs`. A second live attempt is pending renewed user authorization, so this task remains incomplete. -->
- [ ] 4.4 After the live gate succeeds, rebase and integrate the clean edge worktree into `master`, rerun required validation, commit and push the edge and control changes, recording SHAs and validations without secrets.
