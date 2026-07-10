## Why

macOS desktop installers are currently built unsigned, so Gatekeeper treats downloaded AIDCP builds as untrusted and users see blocking risk prompts on first install/open. We now have an Apple Developer Program membership, Developer ID Application certificate, and App Store Connect API key, so the CI-built macOS artifacts should become signed, notarized, stapled, and release-gated.

## What Changes

- Enable Developer ID Application signing for macOS Electron builds in GitHub Actions.
- Enable Apple notarization via `notarytool` credentials supplied through GitHub Actions secrets.
- Add explicit macOS entitlements required by Electron hardened-runtime signing.
- Add CI verification gates for signatures, notarization stapling, and Gatekeeper assessment before artifact upload succeeds.
- Update the desktop release checklist so unsigned builds are no longer considered publishable macOS artifacts.

## Capabilities

### New Capabilities
<!-- None. -->

### Modified Capabilities
- `edge-desktop-packaging`: macOS distributable artifacts must be Developer ID signed, notarized, stapled, and verified before publication.

## Impact

- `aidcp-edge/package.json`: macOS `electron-builder` signing/notarization configuration.
- `aidcp-edge/build/*.plist`: signing entitlements.
- `aidcp-edge/.github/workflows/build-desktop.yml`: macOS signing secret materialization and verification gates.
- `aidcp-edge/docs/release-desktop.md`: release checklist updates.
- GitHub Actions repository secrets: certificate and App Store Connect API key values are required, but secret values must not enter source, logs, docs, or OpenSpec tasks.
