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
- [x] 3.4 Treat profiles explicitly configured without an environment proxy as outside double-hop applicability: skip relay/preflight/override, preserve the existing no-proxy launch path, and add a regression test.

## 4. AdsPower provider launch authority

- [x] 4.1 Validate `AIDCP_ADS_PROXY_OVERRIDE` as an HTTP loopback URL, add `--proxy-server` only to inactive-profile `browser-profile/start`, and reject active-profile takeover when an override is required.
- [x] 4.2 Add provider tests for valid override payload, direct-mode zero regression, invalid/non-loopback rejection, and active-profile fail-closed behavior.
- [x] 4.3 Replace the rejected launch-argument design with an encrypted per-profile original-proxy authority; preserve user proxy input during create/edit, bootstrap existing profiles, remove authority for explicit no-proxy, and keep credentials out of projections, settings, argv, env, and logs.
- [x] 4.4 Deliver the original and generation-target proxy to the Edge child through a private anonymous pipe; remove `AIDCP_ADS_PROXY_OVERRIDE` and all `--proxy-server` injection.
- [x] 4.5 Before every inactive AdsPower launch, including cold-standby wake, update the profile proxy through the constrained API, read it back exactly, and fail closed before `browser-profile/start` on mismatch; configured-proxy active profiles remain non-adoptable.
- [x] 4.6 After confirmed browser close, best-effort restore and verify the original environment proxy; add crash-left-loopback, next-start correction, restore-failure honesty, and no-proxy zero-update tests.

## 5. Reproducible GOST desktop resource

- [x] 5.1 Add a pinned GOST v3.2.6 macOS x64/arm64 staging script with official SHA-256 verification, executable permissions, license notice, and explicit development override resolution.
- [x] 5.2 Wire staged architecture resources into Electron packaging/build-input checks and extend packaged trust gates to require and verify the nested executable.
- [x] 5.3 Add source-level packaging contract tests; do not claim a signed/notarized installer or installed-client delivery without a separately authorized package run.
- [x] 5.4 Split unsigned staging SHA-256 verification from signed macOS runtime identity verification, ignore packaged GOST overrides, and apply the same signed nested-code rule to Native Page Engine.
- [x] 5.5 Add an Electron `afterSign` gate plus final release trust checks for the signed App, GOST identity/version/architecture, and Native Page Engine identity/architecture.

## 6. Validation and closeout

- [x] 6.1 Install physical worktree dependencies, run focused Electron/provider/renderer/packaging tests, full Edge tests required by affected proxy/browser safety contracts, and `npm run typecheck`.
- [x] 6.2 Run a reversible development smoke with a newly started inactive AdsPower profile: prove startup updates and reads back the profile to the GOST loopback without `--proxy-server`, full-chain Facebook preflight succeeds, browser-context egress reflects the environment proxy, and confirmed close restores the original proxy exactly.
- [x] 6.3 Run `openspec validate add-system-upstream-proxy-chain --strict`, record Edge/control commit SHAs and validation evidence here, commit with explicit pathspecs, and push both `codex/add-system-upstream-proxy-chain` branches.
- [x] 6.4 Run focused signed-artifact/runtime/packaging tests, full Edge tests, typecheck, strict OpenSpec validation, then rebuild and locally verify the arm64 OL Developer ID signed package.
- [x] 6.5 Re-run the focused, acceptance, complete Edge, typecheck, build-input, and strict OpenSpec gates for the profile-authority pivot; record the new SHAs and integrate the source and contract updates without claiming a new installer.

## 7. Installed-runtime compatibility and arm64 OL package

- [x] 7.1 Separate strict signed-artifact release verification from relaxed installed-runtime GOST and Native Page Engine resolution; retain fixed packaged paths, compatible manifests, executable bits, architecture checks, ignored packaged overrides, and honest process/readiness failures.
- [x] 7.2 Add regressions proving installed runtime resolution accepts an ad-hoc re-signed outer App without invoking `codesign` or a GOST version subprocess, while `afterSign` and final release verification remain strict.
- [x] 7.3 Bump Edge to 0.3.25; run focused Electron artifact/packaging/lifecycle tests, the complete Edge suite, typecheck, desktop build-input verification, and strict OpenSpec validation; commit, push, and fast-forward source/contracts into the default branches.
- [x] 7.4 Create an explicit OL arm64 release branch, build a Developer ID signed DMG with IP-based customer-auth URL, verify the mounted payload and a reversible ad-hoc outer-App re-sign runtime smoke, and record the local artifact path/SHA without claiming notarization or upload.

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

No-proxy applicability follow-up (2026-07-26):
- Edge fix commit: `39f3ce5` (`codex/add-system-upstream-proxy-chain`).
- Observed regression: with the machine-level switch enabled, an AdsPower profile explicitly configured without a proxy was classified as a missing second hop and blocked with `environment_proxy_missing`.
- The main process now reads profile proxy applicability before preparing the chain. Explicit `noProxy` clears stopped-profile relay state, projects `proxyChainApplicable=false`, skips the Facebook network probe, and launches without `AIDCP_ADS_PROXY_OVERRIDE`. Profiles with a configured proxy continue to fail closed when their required system hop or relay is unavailable.
- Renderer state no longer reports a restart requirement for a running no-proxy profile and explains that double-hop is not applicable.
- Focused proxy/provider/lifecycle/fleet suites: 216 passed; renderer suite: 96 passed; complete Edge suite: 2417 passed, 0 failed; `npm run typecheck` passed; strict OpenSpec validation passed.

Profile-authority pivot follow-up (2026-07-26):
- Edge implementation commit: `893a146`, pushed to `codex/add-system-upstream-proxy-chain`, fast-forwarded to `origin/master`, and validated from the same source tree.
- Control contract commit: `1c4b9ac` (`codex/add-system-upstream-proxy-chain`).
- Environment creation still writes the user's submitted proxy directly. AIDCP separately retains the original configured proxy in a per-profile `safeStorage`-encrypted authority; explicit no-proxy removes the authority and skips all update/readback restrictions.
- Every configured-proxy browser generation now receives its authority through an anonymous pipe, updates AdsPower through `user/update`, reads back the exact route before `browser-profile/start`, and never injects `--proxy-server`. Direct mode writes the original proxy; double-hop mode writes the managed GOST loopback. Active configured-proxy profiles remain non-adoptable.
- Confirmed close best-effort restores and reads back the original proxy; crash-left-loopback is corrected by the next launch rewrite. Original proxy credentials do not enter renderer projections, settings, argv, inherited environment variables, or logs.
- Provider tests: 35 passed; focused Electron lifecycle/security tests: 99 passed; all Electron tests: 914 passed; acceptance tests: 30 passed; complete Edge suite: 2430 passed, 0 failed. `npm run typecheck`, `node --check` for the changed CommonJS modules, `npm run build:dist`, and `npm run verify:desktop-build-input` passed.
- Reversible live smoke started an inactive real profile and proved loopback readback, full-chain Facebook HTTP 200, an interactive browser Facebook page, browser egress equal to the GOST relay egress, confirmed browser close, and exact original-proxy restoration. The temporary smoke script, AdsPower daemon, SunBrowser, and GOST process were removed/stopped afterward.
- `openspec validate add-system-upstream-proxy-chain --strict` passed. No new installer was built, signed, notarized, published, installed, or customer-tested for this pivot.

Installed-runtime compatibility follow-up (2026-07-27):
- Edge implementation commit: `a744852`, pushed to `codex/add-system-upstream-proxy-chain` and fast-forwarded to `origin/master`.
- Installed macOS runtime resolution now ignores packaged GOST overrides but no longer invokes `codesign`, compares Team ID/Identifier, or runs `gost -V` before launch. It retains fixed packaged resources, compatible manifests, executable bits and target architecture; actual GOST process/readiness and Native child startup remain the availability evidence.
- Electron `afterSign` and final release verification remain strict for App/GOST/Native Developer ID identity, Team ID, Identifier, architecture and GOST version.
- Focused runtime/artifact/packaging/lifecycle tests: 24 passed; complete Edge suite: 2447 passed, 0 failed; `npm run typecheck`, `npm run build:dist`, `npm run verify:desktop-build-input`, and strict OpenSpec validation passed.
- OL package branch `release/20260727-ol-arm64-runtime-lite` was created from `a744852`, then fast-forwarded and pushed at `54005cd` to include the concurrent latest Edge proxy-repair commits before the final rebuild. The mounted arm64 payload passed deep App and strict nested-artifact verification with version `0.3.25`, `aidcpCloudDefaultEnv=ol`, and `aidcpClientAuthUrl=http://123.56.253.183:8088/capi`.
- A temporary App copy was outer-only ad-hoc re-signed to `TeamIdentifier=not set`: the strict release verifier rejected it as expected, while installed-runtime resolution returned `gost=true` and `native=true`. The temporary copy was moved to Trash after the reversible smoke.
- Local Developer ID signed-only DMG rebuilt from `54005cd`: `/Users/baitianxing/codes/aidcp-edge.wt/release-20260727-ol-arm64-runtime-lite/dist-electron-ol-arm64-signed-20260727-runtime-lite/AIDCP-0.3.25-arm64.dmg`, SHA-256 `f08b9cc073632d0e2356d70f4fd385038396bdf797cc83bda5971e1151c5f50e`. Notarization was explicitly disabled; no upload, deployment, installation, or customer-machine verification is claimed.
-->
