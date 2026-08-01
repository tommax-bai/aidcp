## 1. Manual Login State

- [x] 1.1 Add the explicit Native `manual_login_required` auth signal for `credential_fill_unavailable` and coordinator result coverage.
  <!-- aidcp-edge 90106f1; Native Rust and TypeScript signal decoding covered; no deviation. -->
- [x] 1.2 Keep the startup core/browser/CDP alive in a read-only manual identity wait, resume the existing identity path in place, and close the owned browser on explicit interruption.
  <!-- aidcp-edge 90106f1; focused startup lifecycle tests and typecheck passed; no deviation. -->

## 2. Electron And UI Projection

- [x] 2.1 Handle generation-scoped `lifecycle.auth_required`, retain the safe reason, release the serial launch waiter, and preserve the occupied browser slot and foreground control.
  <!-- aidcp-edge 90106f1; Electron source contract verifies queue release, slot projection, and unchanged show-browser gate. -->
- [x] 2.2 Show the Facebook-specific credential-fill message and clear it on the existing stable account event.
  <!-- aidcp-edge 90106f1; renderer and account-event regression coverage passed. -->

## 3. Validation And Delivery

- [x] 3.1 Add focused Native/coordinator/startup/Electron/renderer tests for wait, show-browser availability, in-place resume, queue release, and explicit close.
  <!-- aidcp-edge 90106f1; focused suite 112 passed plus Native manual-login wire test. -->
- [x] 3.2 Run focused tests, Facebook safety acceptance, full Edge tests, typecheck, Native gates, and strict OpenSpec validation.
  <!-- Post-rebase validation: focused 112/112; acceptance 31/31; full Edge 2857 passed, 1 gated skip, 0 failed; typecheck passed; Native fmt/clippy/test passed; strict OpenSpec passed. -->
- [x] 3.3 Record repo commits, validation evidence, integration/push status, and the no-installer delivery boundary.
  <!-- Integrated/pushed: aidcp-edge 90106f1 to master; aidcp 3db48344 to main. No deployment or Edge installer was requested or produced; installed clients remain unchanged. -->
