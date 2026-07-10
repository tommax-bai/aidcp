## 1. Core Lifecycle

- [x] 1.1 Add per-core IPC lifecycle commands and idempotent deactivate/finalize coordination.
- [x] 1.2 Make pause retain the owned browser, resume exit without browser cleanup, and close/termination retain final cleanup semantics.
- [x] 1.3 Add focused lifecycle tests proving pause never calls browser close and explicit close still confirms cleanup.
<!-- aidcp-edge commit 63cd290; lifecycle controller and Electron IPC preserve one browser owner across pause. -->

## 2. Electron Supervisor

- [x] 2.1 Spawn edge cores with per-environment IPC and track pause, parked, resume, and close intents without cross-environment leakage.
- [x] 2.2 Update single and bulk lifecycle controls so pause parks, resume reuses, close finalizes, and app quit/removal still close browsers.
- [x] 2.3 Surface IPC delivery failures honestly without falling back to a browser-closing pause path.

## 3. Renderer and Status Projection

- [x] 3.1 Add the `closed` session projection and human-readable health, detail, presence, and fleet labels.
- [x] 3.2 Add an explicit close control for paused environments and wire the preload/renderer IPC flow.
- [x] 3.3 Extend renderer, companion UI, fleet, and pure view-logic tests for paused, closed, resume, close, and environment isolation behavior.

## 4. Validation and Release

- [x] 4.1 Run targeted Electron/core tests, acceptance tests, the full aidcp-edge test suite, and typecheck.
- [x] 4.2 Build the next desktop client packages and verify artifact versions, sizes, and hashes.
<!-- aidcp-edge validation: 109 targeted tests passed on 63cd290; latest release ref e5633c4 passed 16 acceptance tests, 852 full tests, typecheck, and build:dist. -->
<!-- AIDCP 0.3.4 artifacts built from latest master for macOS arm64/x64 and Windows x64; local and dev SHA-256 values matched. -->
- [x] 4.3 Commit and push the edge implementation, publish packages to the dev download host, update console download metadata, deploy console static assets, and verify public URLs.
<!-- aidcp-console commit 43cff23 first published 0.3.3; concurrent mainline release commit 0ede919 advanced the final download metadata to 0.3.4. Console had 76 tests pass with 1 skipped and production build passed. -->
<!-- dev publish: 0.3.4 installers uploaded to /opt/aidcp/downloads, console deployed to /opt/aidcp/console, all three public 8088 download URLs returned 200 with matching Content-Length. -->
- [x] 4.4 Record commit, validation, and dev release evidence here; run `openspec validate edge-pause-preserve-browser-close-state --strict` and archive the completed change.
