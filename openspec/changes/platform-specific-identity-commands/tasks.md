## 1. Protocol and control contract

- [x] 1.1 Add `identity.read_current`, `identity.read_self_profile`, and correlated `identity.observed` payloads to the synchronized Cloud/Edge protocol types and command routing; remove the self-capture `direct` field from `profile.open`.
- [x] 1.2 Update `docs/protocol.md` with the fixed side effects, platform strategy, capability negotiation, result correlation, and version-skew rejection contract.

<!-- Evidence: aidcp-cloud bbe0052; aidcp-edge 785244d; aidcp control 0a87371. Protocol v2 acceptance passed in both repos. Deployment is tracked in 4.5; no contract deviations. -->

## 2. Cloud platform orchestration

- [x] 2.1 Add an exhaustive `identityCapture` strategy to every Cloud `PlatformRegistryEntry`, with Xiaohongshu self-profile, Facebook current-page, and WeChat Channels unsupported declarations.
- [x] 2.2 Change startup nickname enrichment to generate a capture id, send the platform-selected identity command, and complete only from matching `identity.observed` results.
- [x] 2.3 Gate each identity command on negotiated Edge support; remove legacy `self.profile.capture → profile.open{direct}` and ensure Facebook current-page completion sends no Feed restore.
- [x] 2.4 Add focused Cloud tests for platform exhaustiveness, command selection, capability skew, result correlation, empty nickname honesty, and strategy-specific restore behavior.

<!-- Evidence: aidcp-cloud bbe0052. Focused identity/acceptance tests passed; post-rebase full suite 3321 passed, 10 skipped, 0 failed; typecheck passed. DEV deployment is tracked in 4.5; no deviations. -->

## 3. Edge and Native execution

- [x] 3.1 Add exact semantic page-command capabilities to browser drivers/hello and route the new Cloud commands and result without a JavaScript fallback; reject legacy `profile.open{direct}` before execution.
- [x] 3.2 Split Native startup bootstrap, runtime current-page identity, and bound self-profile identity commands; declare exact per-adapter command sets in the manifest and platform support matrix.
- [x] 3.3 Implement Facebook current-page identity with a hard no-navigation contract and reject self-profile/ordinary profile commands before CDP dispatch.
- [x] 3.4 Implement Xiaohongshu bound self-profile identity without caller-supplied target identity and return the correlated identity observation.
- [x] 3.5 Add focused TypeScript/Rust/fake-CDP tests for manifest-driver agreement, platform mismatch rejection, zero-navigation Facebook reads, canonical Xiaohongshu self navigation, legacy-direct rejection, and typed observations.

<!-- Evidence: aidcp-edge 785244d. TypeScript full suite 2285 passed; typecheck passed; Rust 52 tests passed; fmt and Clippy passed. Unsigned darwin-arm64 Native artifact and desktop build input verified. No installer or real-account acceptance was performed; x86_64-apple-darwin remains uninstalled. No implementation deviations. -->

## 4. Validation, integration, and DEV delivery

- [x] 4.1 Run Cloud focused acceptance, full tests, and typecheck; record concise evidence.
- [x] 4.2 Run Edge focused acceptance, full tests, typecheck, Native Rust tests/Clippy, and Native/package-input verification; record the installer and real-account validation boundary.
- [x] 4.3 Run `openspec validate platform-specific-identity-commands --strict` and update all completed task evidence.
- [x] 4.4 Commit, rebase, fast-forward integrate, and push control/Edge/Cloud changes through their eligible default branches without force.
- [ ] 4.5 Deploy the integrated Cloud default branch to DEV only, verify service/listener/health/Feishu/PostgreSQL, and report that installed Edge clients remain unchanged until a separate package/release.

<!-- Validation: aidcp-cloud bbe0052 and aidcp-edge 785244d passed the checks recorded above; control 0a87371 passed strict OpenSpec validation. All three feature branches were rebased, fast-forward integrated, and pushed to their eligible defaults without force; DEV delivery remains pending. -->
