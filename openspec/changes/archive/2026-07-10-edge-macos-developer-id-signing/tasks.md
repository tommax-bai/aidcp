## 1. OpenSpec

- [x] 1.1 Create proposal, design, tasks, and edge desktop packaging spec delta. <!-- aidcp control repo: proposal/design/tasks/spec delta created for edge-macos-developer-id-signing -->

## 2. aidcp-edge macOS Signing Configuration

- [x] 2.1 Update `package.json` mac build config to require code signing, hardened runtime, explicit entitlements, and explicit CI-owned notarization. <!-- aidcp-edge package.json: removed null identity; added forceCodeSigning and explicit entitlements; disabled electron-builder built-in notarize so workflow owns notarytool -->
- [x] 2.2 Add Electron hardened-runtime entitlement plist files under `build/`. <!-- aidcp-edge build/entitlements.mac*.plist added with Electron hardened runtime entitlements -->

## 3. GitHub Actions

- [x] 3.1 Update `build-desktop.yml` to materialize Apple API key and use signing/notarization secrets. <!-- aidcp-edge workflow: preflight secrets, decode APPLE_API_KEY_BASE64 to temp .p8, pass CSC_* and APPLE_API_* env into scripts/build-desktop-macos.sh -->
- [x] 3.2 Add macOS verification gates for `.app` signatures, Gatekeeper assessment, stapled tickets, and `.dmg` trust state before artifact upload. <!-- aidcp-edge scripts/build-desktop-macos.sh + scripts/notarize-and-staple.sh: notarize/staple app bundles and DMGs with parallel x64/arm64 waits and 2h Apple timeout; verify app/dmg with codesign/spctl/stapler before upload-artifact -->

## 4. Release Documentation

- [x] 4.1 Update `docs/release-desktop.md` so macOS releases require signed GitHub Actions artifacts and verification output. <!-- aidcp-edge docs/release-desktop.md updated from unsigned flow to Developer ID notarized CI flow -->

## 5. Validation

- [x] 5.1 Run `openspec validate edge-macos-developer-id-signing --strict`. <!-- aidcp control repo: strict validation passed -->
- [x] 5.2 Run `npm run typecheck` and `npm test` in `aidcp-edge`. <!-- aidcp-edge: typecheck passed; npm test passed 660 tests, 0 failures -->
- [x] 5.3 Confirm required GitHub Actions secrets are present without reading values. <!-- GitHub repo tommax-bai/aidcp-edge: required secret names present; values not read -->
