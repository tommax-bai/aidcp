## ADDED Requirements

### Requirement: macOS release artifacts are Developer ID signed and notarized

macOS desktop release artifacts SHALL be signed with an Apple Developer ID Application identity, use hardened runtime, pass Apple notarization, and have a stapled notarization ticket before they are published or referenced by the console download flow. A macOS installer produced without a valid Developer ID signature, without notarization acceptance, or without a stapled ticket MUST be treated as a failed release artifact and MUST NOT be uploaded or promoted as the current macOS client.

#### Scenario: GitHub Actions produces trusted macOS artifacts

- **WHEN** the desktop installer workflow builds macOS `dmg` and `zip` artifacts for release
- **THEN** each generated `.app` SHALL pass `codesign --verify --deep --strict`, Gatekeeper `spctl --assess --type exec`, and `xcrun stapler validate`
- **AND** each generated `.dmg` SHALL pass Gatekeeper primary-signature assessment and `xcrun stapler validate`

#### Scenario: signing or notarization material is missing

- **WHEN** the GitHub Actions macOS job lacks the Developer ID certificate, certificate password, App Store Connect API key, key id, or issuer id required for signing/notarization
- **THEN** the macOS build SHALL fail closed before artifact upload, rather than producing or publishing an unsigned installer

#### Scenario: local unsigned package is built for investigation

- **WHEN** a developer builds a local unsigned macOS package for quick investigation
- **THEN** that artifact MAY be used only for local testing and MUST NOT be published as a release/download artifact
