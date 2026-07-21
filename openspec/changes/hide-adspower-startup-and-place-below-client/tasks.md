## 1. Hidden Startup Staging

- [x] 1.1 Compute a startup staging coordinate beyond the right-most local display independently from final parking/show bounds, including per-environment cascade and serialization coverage.
  <!-- Edge: startup staging now uses the right-most known display edge plus the existing offscreen gap; final parking/show bounds remain independent. -->
- [x] 1.2 Omit `--start-maximized` for AdsPower and self launches that receive a staging position while retaining fixed desktop size and standalone fallback behavior.
  <!-- Edge: positioned Electron launches keep 1440x980 and omit maximize; unpositioned standalone launches retain maximize. -->
- [x] 1.3 Add focused provider/parking tests for staged launch arguments, final bounds independence, and no-staging compatibility.
  <!-- Covered by browser-provider, chrome-launcher, and browser-parking focused tests. -->

## 2. Browser Below AIDCP

- [x] 2.1 Extend the core browser-show control with correlated completion replies while preserving uncorrelated foreground behavior for guide/tray/recovery actions.
  <!-- Core replies only to request-id-bearing show commands and reports set-bounds/config failures without changing legacy uncorrelated commands. -->
- [x] 2.2 Add Electron main-process correlation, timeout cleanup, and final AIDCP `show/focus/moveTop` ordering for the environment-avatar path.
  <!-- Main waits up to 3 seconds for the matching environment reply, then restores and raises AIDCP; failure leaves the UI phase unchanged. -->
- [x] 2.3 Route the environment rail show phase through the below-client policy and add renderer/main/core regression coverage for success, failure, timeout, and unchanged guided-login behavior.
  <!-- Avatar show sends keepClientForeground=true; guided login still sends the legacy foreground command. -->

## 3. Validation and Delivery

- [x] 3.1 Run focused browser provider, parking, Electron fleet/main, and browser-window tests and fix regressions.
  <!-- 2026-07-21: 149 focused tests passed; git diff --check passed. -->
- [x] 3.2 Run Edge acceptance, full tests, and typecheck; record real-machine startup/focus acceptance as completed or explicitly outstanding.
  <!-- 2026-07-21: acceptance 28 passed / 1 gated skip; full Edge suite exited 0; typecheck passed. Real-machine AdsPower flash/focus observation remains outstanding because no installer was built or target profile launched. -->
- [x] 3.3 Update this checklist with commits/validation evidence, run strict OpenSpec validation, and commit/push the isolated Edge and control branches without building an installer.
  <!-- Edge 85b59ee; control bb912f4 plus this evidence commit. Both isolated branches pushed. Strict OpenSpec validation passed; no installer was built. -->

## 4. Client-Aligned Show Correction

- [x] 4.1 Clarify that avatar-show geometry is centered on the live AIDCP window bounds rather than the static primary-screen/cascade inspection position.
  <!-- 2026-07-21 screenshot evidence showed the browser exposed at the client's lower-right edge while Z-order was otherwise correct. -->
- [x] 4.2 Derive display-aware client-centered bounds in Electron, pass them through the correlated show command, and apply the validated override in core without changing guide/recovery behavior.
  <!-- Electron now reads mainWindow bounds and its matching display per avatar gesture; core validates and applies only that correlated bounds override. -->
- [x] 4.3 Add regression coverage, run focused/full Edge validation plus strict OpenSpec validation, record the real-machine screenshot finding, and safely integrate the correction.
  <!-- Edge 227a6f0 integrated to master after rebasing 13 concurrent commits. Client-alignment/core override regressions, acceptance 28/28, full Edge suite, typecheck, diff check, and strict OpenSpec validation passed. The supplied screenshot confirms the pre-fix lower-right offset; post-fix visual acceptance remains pending a rebuilt client. -->
