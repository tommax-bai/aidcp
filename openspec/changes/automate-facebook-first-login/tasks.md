## 1. AdsPower Startup And Secret Boundary

- [x] 1.1 Add the fresh-start AdsPower body fields for first-open credential filling and disabled browser password saving, preserving permission-prompt suppression and active-profile honesty.
- [x] 1.2 Add a profile-bound Electron TOTP IPC operation that reads one exact AdsPower V2 profile, validates the server-time request, computes one code, and returns no raw login material.
- [x] 1.3 Add provider, Local API, Electron broker, redaction, profile-mismatch, and TOTP-window tests.

## 2. Native Facebook Signal And Action Support

- [x] 2.1 Add Native command and receipt types for Facebook auth probing and the independent login, TOTP-entry, TOTP-submit/clear, warning, push-blocker, and Remember Password actions.
- [x] 2.2 Implement mutually exclusive Facebook auth signal detection with target/document-bound signal ids, CAPTCHA/unknown classification, visibility, uniqueness, top-hit checks, and shared stable numeric `c_user` plus non-empty `xs` authentication evidence.
- [x] 2.3 Implement one signal-specific Native CDP action per command with fresh signal revalidation, cancellation/deadline support, and a signal-local postcondition.
- [x] 2.4 Add Rust/router tests proving stale, ambiguous, CAPTCHA, unknown, wrong-signal, blank/non-numeric user-cookie, lookalike-domain, and empty-session-cookie cases fail closed, dispatch zero unintended input, and never replay a signal id.
- [x] 2.5 Replace raw-URL document generations with a fixed-size URL-sensitive generation that preserves fresh-signal invalidation across full navigation and SPA route/query changes.
  <!-- Edge commit a6c92a2 emits a 67-byte versioned SHA-256 generation over document time origin plus full origin/path/query state, so raw checkpoint queries no longer cross the Native observation boundary. -->
- [x] 2.6 Recognize a unique visible topmost 2FA text input through its exact browser-associated labels, and add regression fixtures for the observed `autocomplete="off"`/dynamic-id page shape plus long checkpoint queries.
  <!-- Edge commit a6c92a2 uses HTMLInputElement.labels only inside confirmed TOTP context, retains editable/unique/top-hit gates, and focused router tests pass 17/17 including live-shape for/id, wrapping-label, nearby-text rejection, ambiguity, and 734-character query cases. -->

## 3. Bounded Startup Reconciler

- [x] 3.1 Add the TypeScript Facebook auth coordinator that probes, executes at most one matching action, re-probes without assuming order, and honors the existing login-wait/cancellation budget.
- [x] 3.2 Implement Facebook server-time sampling and the 30-second TOTP window rule, including waiting below 10 seconds and clearing rather than submitting a newly stale code.
- [x] 3.3 Invoke the idempotent coordinator after initial attach and cold-standby reattach, before the read-only stable-identity gate, while retaining logged-in no-op behavior.
- [x] 3.4 Add coordinator and startup-assembly tests for optional/reordered signals, one-action passes, timeout/interruption, TOTP boundaries, and Native-only routing.

## 4. Validation And Delivery

- [x] 4.1 Run focused provider/Electron/Native/coordinator tests and the Facebook safety acceptance suites.
  <!-- Edge validation: focused TypeScript 185/185 and Facebook safety acceptance 31/31 passed. -->
- [x] 4.2 Run the full edge test suite, typecheck, Native Page Engine build/tests, and strict OpenSpec validation.
  <!-- aidcp-edge commits: a393004 and 61a0753. Full TypeScript suite and typecheck exited 0; Native fmt, clippy, 167 unit tests, and all integration suites passed; the unsigned darwin-arm64 release artifact was rebuilt and verified after the auth-cookie fix. OpenSpec strict validation passed in the control worktree. Delivery remains feature-source only: no runtime deployment or installer. -->
- [x] 4.3 Resolve the final live gate by either completing the operator-approved third-profile validation or recording an explicit operator waiver and its evidence boundary without credentials, TOTP, cookies, or raw AdsPower responses.
  <!-- One bounded live attempt applied the fresh-start policy, attached CDP/Native, returned an `authenticated` signal from cookie-name-only evidence, dispatched zero login actions, then stopped at `stable_identity_unconfirmed`; the browser was closed. Source now requires the same numeric `c_user` criterion as stable identity plus non-empty `xs`. On 2026-07-30 the operator explicitly instructed AIDCP to merge without another test, so the second attempt is waived; the first attempt remains stopped, not successful. -->
- [x] 4.4 After the live gate succeeds or its explicit waiver is recorded, rebase and integrate the clean edge worktree into `master`, complete the control delivery to `main`, and push both source changes while recording SHAs, prior validations, and delivery deviations without secrets.
  <!-- aidcp-edge master was fast-forwarded and pushed at 61a0753. The control change was rebased onto origin/main from OpenSpec commit a2186936 and is completed by this delivery update. Per operator instruction, no second live-account test or desktop package was run; no Cloud/Console code changed and no ECS service was touched because Edge has no package-free runtime deployment target. -->
- [x] 4.5 Run the focused Native auth/router tests, Native formatting/clippy/unit/integration gates, Edge typecheck, and strict OpenSpec validation; then integrate and push the Edge and control follow-up without packaging or mutating live profiles.
  <!-- Edge a6c92a2 is pushed to master. Validation: auth TypeScript 35/35, Rust auth 4/4, typecheck, fmt, clippy, full cargo test exit 0 (including 167 unit tests plus integrations), artifact tests 3/3, staged Native artifact verification, and strict OpenSpec validation. Read-only probes against the two operator-open 734-query pages returned bounded confirmed receipts and both reached unique totp_entry_ready; no input, click, TOTP generation, or submission occurred. No desktop package was built, installed, or released; this control commit completes the source-only follow-up. -->
