## Context

The existing desktop workflow intentionally disables macOS signing: `build.mac.identity = null` in `aidcp-edge/package.json`, `CSC_IDENTITY_AUTO_DISCOVERY=false` in `build-desktop.yml`, and release docs describe the app as unsigned. Local verification of the existing app shows an ad-hoc signature, no TeamIdentifier, failed `spctl`, and no stapled ticket.

The repository now has the required signing material configured as GitHub Actions secrets:

- `MAC_CSC_LINK`: Developer ID Application `.p12`, base64 encoded.
- `MAC_CSC_KEY_PASSWORD`: `.p12` export password.
- `APPLE_API_KEY_BASE64`: App Store Connect API `.p8`, base64 encoded.
- `APPLE_API_KEY_ID`: App Store Connect API key id.
- `APPLE_API_ISSUER`: App Store Connect API issuer id.
- `APPLE_TEAM_ID`: Apple team id.

Secret values are runtime-only CI inputs. They must not be committed, logged, or copied into OpenSpec task notes.

## Design

### Electron Builder Configuration

Remove `mac.identity = null` and let `electron-builder` sign using `CSC_LINK`/`CSC_KEY_PASSWORD`. Keep hardened runtime enabled, add explicit entitlements, and set `notarize: false` so the release scripts own notarization through explicit `notarytool` calls with request ids, polling, longer timeouts, and failure logs.

Use build-resource entitlements:

- `build/entitlements.mac.plist`
- `build/entitlements.mac.inherit.plist`

The entitlements are limited to Electron's hardened-runtime needs: JIT, unsigned executable memory, and library validation disablement. Do not enable App Sandbox for this outside-Mac-App-Store distribution path.

### GitHub Actions Secret Materialization

The macOS job decodes `APPLE_API_KEY_BASE64` into a temporary `.p8` file and sets `APPLE_API_KEY` to that file path before invoking `scripts/build-desktop-macos.sh`. The script first builds signed `.app` bundles, notarizes and staples the x64/arm64 bundles in parallel through `scripts/notarize-and-staple.sh`, then builds dmg/zip distributables from the stapled app bundles and notarizes/staples each `.dmg` in parallel.

`CSC_LINK` can be supplied as the base64 `.p12` directly; `electron-builder` already supports this format. Apple notarization can remain `In Progress` longer than 60 minutes, so the workflow allows 2 hours per submission and a 6 hour macOS job cap while still failing closed if no accepted ticket is returned.

This avoids a long-running hidden notarization step inside `electron-builder` and keeps the script/workflow logs actionable: every notarization prints the Apple request id, polling status, timeout, and failure log when Apple rejects or does not complete the submission.

### Verification Gate

The macOS job must fail before artifact upload if any of these checks fail:

- `codesign --verify --deep --strict --verbose=2` for generated `.app` bundles.
- `spctl --assess --verbose --type exec` for generated `.app` bundles.
- `xcrun stapler validate` for generated `.app` bundles.
- `spctl --assess --verbose --type open --context context:primary-signature` for generated `.dmg` files.
- `xcrun stapler validate` for generated `.dmg` files.

This gate preserves the project invariant that missing trust state is not silently published as a successful installer.

### Local Builds

Developers may still run local unsigned/package experiments only if they explicitly opt out with local environment settings or do not publish the result. Release docs should distinguish local test packages from publishable CI artifacts. Published macOS artifacts must come from the signed GitHub Actions path.

## Risks

- **Notarization can fail after signing succeeds.** The CI gate fails the run and keeps artifacts unpublished.
- **Missing or malformed secrets can silently fall back to unsigned builds.** `forceCodeSigning` and verification commands make this fail closed.
- **Electron hardened runtime can break if entitlements are too narrow.** Use the standard Electron entitlements already expected by `electron-builder` templates.
- **Secrets in logs.** Workflow should avoid printing secret bodies; verification output may print certificate identity and team id only, not private key or API key material.
