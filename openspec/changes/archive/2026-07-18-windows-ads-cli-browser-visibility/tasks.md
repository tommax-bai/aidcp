# Tasks — windows-ads-cli-browser-visibility

## 1. Contract

- [x] 1.1 Record the Windows Ads CLI -> SunBrowser visibility failure and nickname double-click semantics in proposal/design/spec deltas.

## 2. aidcp-edge

- [x] 2.1 Add an idempotent, fail-closed staging patch that preserves native visibility for Ads CLI-launched `SunBrowser` on Windows. <!-- aidcp-edge 183dc47 -->
- [x] 2.2 Add focused tests for the staging patch's original, already-patched, and incompatible vendor shapes. <!-- aidcp-edge 183dc47 -->
- [x] 2.3 Make rapid second-click handling non-reversing and nickname double-click show-only. <!-- aidcp-edge 183dc47 -->
- [x] 2.4 Add an Electron fleet regression proving double-click emits show without park. <!-- aidcp-edge 183dc47 -->

## 3. Validation and integration

- [x] 3.1 Run focused staging/renderer tests and `npm run typecheck` in the Edge worktree. <!-- 71 focused tests passed; real Ads CLI 2.1.0 staging and hook behavior verified; typecheck passed. -->
- [x] 3.2 Run full Edge tests and `openspec validate windows-ads-cli-browser-visibility --strict`. <!-- 1782 full tests + 24 acceptance tests passed; strict OpenSpec validation passed. -->
- [x] 3.3 Commit, integrate, and push the control and Edge changes; do not package/release an installer without explicit operator request. <!-- aidcp-edge 183dc47 integrated and pushed to origin/master; control change committed as 1d312d2. -->
