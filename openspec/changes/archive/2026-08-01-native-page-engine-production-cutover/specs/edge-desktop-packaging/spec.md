## ADDED Requirements

### Requirement: Official desktop packages MUST include a compatible Native Page Engine

Every official package that advertises Xiaohongshu page automation SHALL include exactly one architecture-compatible Native Page Engine outside ASAR together with a manifest containing its platform, architecture, engine version, protocol version, capability digest, and SHA-256. Package construction and startup verification MUST fail honestly when the artifact or manifest is missing, mismatched, corrupted, or incompatible.

#### Scenario: macOS arm64 package is built
- **WHEN** CI builds the official macOS arm64 client
- **THEN** the package contains the arm64 Native executable and matching verified manifest under `extraResources`

#### Scenario: Artifact architecture is wrong
- **WHEN** a package stages an x64 artifact into an arm64 build or otherwise mismatches the target
- **THEN** package verification fails and no distributable is emitted

### Requirement: Nested Native artifacts MUST be signed and verified

On macOS, release construction SHALL sign the Native executable as a nested binary of the application bundle before the bundle itself is signed, notarized, and stapled. Release validation on macOS MUST verify the nested executable's own signature and its team identity against the outer bundle, the outer application and disk image's notarization, the manifest hash, the executable's architecture, and packaged startup behavior; a nested binary that resolves outside the signed resources directory MUST be rejected.

The Windows package flow SHALL stage the architecture-matched Native executable into the package, but it does not sign binaries and there is no nested-signature verification on that platform. Any artifact whose signature has not been verified — a Windows installer, or a local macOS build produced without Developer ID credentials — MUST be labelled by its actual signing state and MUST NOT be described or published as a signed distributable.

#### Scenario: Signed macOS package passes release gates
- **WHEN** the Native executable, app, and disk image have valid Developer ID signatures/notarization and the packaged smoke test starts the engine from resources outside ASAR
- **THEN** the macOS artifact may proceed to release review

#### Scenario: Inner signature is missing
- **WHEN** the outer app is signed but the nested Native executable fails signature verification
- **THEN** the release job fails and MUST NOT upload a distributable artifact

#### Scenario: Windows installer is produced
- **WHEN** the Windows package flow stages the x64 Native executable and emits an installer
- **THEN** the installer carries the architecture-matched executable
- **AND** it is recorded as unsigned and MUST NOT be presented as a signed distributable

### Requirement: Packaging MUST exclude migrated Xiaohongshu JavaScript core

The desktop build graph SHALL include only the selector-free Native facade for Xiaohongshu and MUST exclude migrated legacy browse/publish rule modules, source maps, and representative rule strings. This exclusion SHALL be verified against the final package, not inferred from TypeScript import reachability alone.

#### Scenario: ASAR contains a forbidden legacy module
- **WHEN** final-package inspection finds a migrated Xiaohongshu executor path or cleartext rule marker
- **THEN** the desktop build fails

#### Scenario: Ordinary non-Xiaohongshu code remains required
- **WHEN** a shared selector-free utility is still needed by another platform
- **THEN** it remains packaged only after dependency inspection proves it does not carry migrated Xiaohongshu page rules

