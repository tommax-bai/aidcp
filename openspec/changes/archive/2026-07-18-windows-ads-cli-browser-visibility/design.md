# Design — Windows Ads CLI Browser Visibility

## Context

The actual Windows process chain is `AIDCP Edge -> Ads CLI runtime -> SunBrowser`. There is no AdsPower desktop/background console in this path. The bundled Ads CLI's Windows preload hook monkey-patches Node child-process methods and defaults every spawn to `windowsHide: true`. This is appropriate only where hiding a helper subprocess is intended; applying it to the driven browser removes the native window's visible style.

The browser parking control itself is already correctly routed per environment. Its `browser.show` implementation sets visible bounds and calls `Page.bringToFront`; those operations work once `SunBrowser` has been launched as a visible GUI window. The fix therefore belongs at the Ads CLI staging compatibility boundary, not in cloud orchestration or protocol.

## Decisions

### 1. Patch the staged vendor hook, not generated output by hand

Add an idempotent staging helper that opens `cli/core/winHideChildProcess.js`, verifies the pinned vendor shape, and changes only the `spawn`/`spawnSync` wrappers. Commands whose executable basename is `SunBrowser` or `SunBrowser.exe` receive `windowsHide: false`; other commands retain the hook's existing normalization.

The helper throws when neither the original nor already-patched shape is present. `npm run build:ads-runtime` therefore fails at build time on an incompatible Ads CLI upgrade instead of shipping a hidden-window regression.

### 2. Preserve the existing CDP show/parking channel

Do not add Win32 native bindings or a second window-control channel. Newly launched browsers are visible to the OS, after which the existing CDP bounds and `Page.bringToFront` calls remain authoritative. Already-running processes launched with the old hidden flag require a browser/app restart.

### 3. Separate double-click intent from the three-state single-click control

The first physical click keeps the existing three-state behavior. A click event with `detail > 1` is ignored by the phase-transition handler, preventing the second half of a double-click from issuing the inverse action. The nickname's `dblclick` handler explicitly requests show for that environment and never requests park. Programmatic/keyboard activation remains unchanged.

## Validation

- Unit-test the staging helper against a minimal vendor-hook fixture, including idempotence and fail-closed behavior.
- Extend the fleet renderer test so a physical double-click on an already-selected nickname emits show and zero park commands.
- Run focused tests, full Edge tests, typecheck, and strict OpenSpec validation.

