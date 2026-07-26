## 1. System proxy and relay primitives

- [x] 1.1 Add a macOS fixed-system-proxy resolver with deterministic SOCKS5/HTTPS-web/HTTP priority, explicit PAC/WPAD rejection, loop validation, stable error enums, and parser tests.
- [x] 1.2 Add a managed per-profile GOST chain controller that generates credential-private stdin configuration, allocates/listens only on loopback, proves readiness, single-flights starts, invalidates changed chains, and terminates all children on shutdown.
- [x] 1.3 Add relay tests for HTTP/HTTPS/SOCKS5 environment hops, secret redaction, missing binary, early exit, readiness timeout, reuse, invalidation, and bounded shutdown.

## 2. Explicit desktop setting and safe status

- [x] 2.1 Add default-off `systemProxyUpstreamEnabled` settings normalization and persistence without storing resolved endpoints or proxy credentials.
- [x] 2.2 Add the AdsPower settings switch, direct/double-hop explanatory copy, restart-required dirty behavior, and renderer regression coverage.
- [x] 2.3 Project safe chain preparation state and stable failure copy without exposing host credentials, raw sidecar output, or claiming browser egress.
- [x] 2.4 Persist the visible proxy-chain selection immediately for offline preflight, freeze the effective mode of running browser generations until restart, invalidate stale offline evidence, and add renderer/contract regressions.

## 3. Preflight and supervisor integration

- [x] 3.1 Route double-hop Facebook preflight through the managed loopback endpoint while preserving the existing direct-mode path and unknown-vs-unavailable semantics.
- [x] 3.2 Invalidate preflight and relay state when the profile proxy or double-hop setting changes; keep the relay alive while its browser may still use it and stop all relays during application shutdown.
- [x] 3.3 Inject only the prepared loopback endpoint into the matching Edge child and add supervisor/preflight tests proving unavailable system proxy blocks without direct fallback.

## 4. AdsPower provider launch override

- [x] 4.1 Validate `AIDCP_ADS_PROXY_OVERRIDE` as an HTTP loopback URL, add `--proxy-server` only to inactive-profile `browser-profile/start`, and reject active-profile takeover when an override is required.
- [x] 4.2 Add provider tests for valid override payload, direct-mode zero regression, invalid/non-loopback rejection, and active-profile fail-closed behavior.

## 5. Reproducible GOST desktop resource

- [x] 5.1 Add a pinned GOST v3.2.6 macOS x64/arm64 staging script with official SHA-256 verification, executable permissions, license notice, and explicit development override resolution.
- [x] 5.2 Wire staged architecture resources into Electron packaging/build-input checks and extend packaged trust gates to require and verify the nested executable.
- [x] 5.3 Add source-level packaging contract tests; do not claim a signed/notarized installer or installed-client delivery without a separately authorized package run.
- [x] 5.4 Split unsigned staging SHA-256 verification from signed macOS runtime identity verification, ignore packaged GOST overrides, and apply the same signed nested-code rule to Native Page Engine.
- [x] 5.5 Add an Electron `afterSign` gate plus final release trust checks for the signed App, GOST identity/version/architecture, and Native Page Engine identity/architecture.

## 6. Validation and closeout

- [x] 6.1 Install physical worktree dependencies, run focused Electron/provider/renderer/packaging tests, full Edge tests required by affected proxy/browser safety contracts, and `npm run typecheck`.
- [ ] 6.2 Run a development smoke with a newly started inactive AdsPower profile: prove the launch payload includes the loopback override, full-chain Facebook preflight succeeds, and browser-context egress evidence reflects the environment proxy; if AdsPower ignores the override, stop without profile mutation and record the blocker.
- [x] 6.3 Run `openspec validate add-system-upstream-proxy-chain --strict`, record Edge/control commit SHAs and validation evidence here, commit with explicit pathspecs, and push both `codex/add-system-upstream-proxy-chain` branches.
- [x] 6.4 Run focused signed-artifact/runtime/packaging tests, full Edge tests, typecheck, strict OpenSpec validation, then rebuild and locally verify the arm64 OL Developer ID signed package.

<!--
Implementation evidence (2026-07-26):
- Edge repo commit: 3820cfa (`codex/add-system-upstream-proxy-chain`), pushed to origin.
- Control OpenSpec artifact commit: 2b3f134 (`codex/add-system-upstream-proxy-chain`).
- Physical `npm ci --prefer-offline` completed in the Edge worktree.
- Focused proxy/provider/renderer/packaging suites passed, including a real GOST process integration carrying HTTP first-hop -> authenticated SOCKS5 second-hop traffic.
- `npm test`: 2408 passed, 0 failed; `npm run typecheck`: passed.
- `npm run build:dist`: passed (`reachable=79`, `removed=63`, legacy rules/source maps absent).
- `npm run verify:desktop-build-input`: passed.
- `openspec validate add-system-upstream-proxy-chain --strict`: passed after rebasing the control branch onto current `origin/main`.
- GOST v3.2.6 arm64 and x64 archives staged with pinned SHA-256 verification; arm64 `gost -V` and generated-config readiness smoke passed.
- Current development Mac system proxy resolved as fixed SOCKS5 loopback via the new resolver.

Task 6.2 remains open: no inactive AdsPower profile was selected for a real browser launch, so `launch_args` browser adoption, Facebook preflight through the customer's environment proxy, and CDP browser-context egress are not claimed. No AdsPower profile was persistently modified. No installer was built, signed, notarized, published, installed, or customer-tested.

Follow-up evidence (2026-07-26):
- Edge follow-up commit: `c797ae2` (`codex/add-system-upstream-proxy-chain`).
- Edge source was fast-forward integrated to `origin/master` at `c797ae2` after 30/30 acceptance tests, the complete Edge test command, `npm run typecheck`, and desktop build-input verification passed.
- `systemProxyUpstreamEnabled` remains default-off; the standard desktop build stages the pinned architecture-specific GOST resource and fails closed when required build input is absent.
- Observed regression: changing the visible switch while an environment was stopped left the old persisted mode active, so offline selection reused a double-hop preflight after the UI showed direct mode.
- The switch now persists its target mode immediately; the main process invalidates stopped-environment preflight/relay evidence before scheduling the next offline preflight.
- Running child generations resolve their effective mode from the frozen `status.proxyMode` until explicit restart, including browser-absent cold-standby/control-plane states.
- Renderer + system proxy contract tests: 88 passed; focused lifecycle/fleet/preflight/runtime tests: 43 passed; Electron main/renderer syntax checks and `npm run typecheck`: passed.

Signed nested-artifact follow-up (2026-07-26):
- Edge fix commit: `5236653`, pushed to `codex/add-system-upstream-proxy-chain`, fast-forwarded to `origin/master`, and fast-forwarded to `release/20260726-ol-current`.
- Root cause reproduced on the previously installed Developer ID app: signing changed GOST SHA-256 from manifest `ca290005...` to `98efe662...` and Native Page Engine from manifest `b2fc532d...` to `e024e7bb...`; both old runtime hash verifiers failed while `codesign` and Team ID `DK3BYZ9K32` were valid.
- Development/staging and `afterPack` retain pre-sign SHA-256 validation. Packaged macOS runtime now ignores `AIDCP_GOST_BINARY`, verifies fixed resource containment, App and nested Developer ID identities, Team ID, Identifier and architecture, then checks GOST v3.2.6 only after signature trust. Native Page Engine uses the same packaged signature rule.
- Electron `afterSign` and the final macOS release trust gate verify both nested executables. Focused signed-artifact/runtime/packaging tests: 31 passed; complete Edge test command exited 0; `npm run typecheck` passed; strict OpenSpec validation passed.
- Final arm64-only OL build completed with exit 0 from `release/20260726-ol-current` at `5236653`; mounted DMG verification passed for deep App signature, both nested identities, `aidcpCloudDefaultEnv=ol`, and `aidcpClientAuthUrl=http://123.56.253.183:8088/capi`.
- Local signed-only DMG: `dist-electron-ol-arm64-signed-20260726-gost-fix/AIDCP-0.3.24-arm64.dmg`, SHA-256 `8509e0952c377dffb7e681e76d36d1feeca58f6464be9e461cf0c28f7b9fedf8`. Notarization was intentionally disabled; `spctl` reports `Unnotarized Developer ID`, so no notarized/Gatekeeper-accepted delivery is claimed.
-->
