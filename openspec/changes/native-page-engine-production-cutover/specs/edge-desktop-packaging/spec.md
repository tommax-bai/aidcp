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

Release construction SHALL sign the Native executable before signing/notarizing the containing macOS app and SHALL include the matching executable in the Windows signing/package flow. Release validation MUST verify the inner executable, outer application/installer, manifest hash, and packaged startup behavior; an unsigned local artifact MUST NOT be described or published as distributable.

#### Scenario: Signed macOS package passes release gates
- **WHEN** the Native executable, app, and disk image have valid Developer ID signatures/notarization and the packaged smoke test starts the engine from resources outside ASAR
- **THEN** the macOS artifact may proceed to release review

#### Scenario: Inner signature is missing
- **WHEN** the outer app is signed but the nested Native executable fails signature verification
- **THEN** the release job fails and MUST NOT upload a distributable artifact

### Requirement: Packaging MUST exclude migrated Xiaohongshu JavaScript core

The desktop build graph SHALL include only the selector-free Native facade for Xiaohongshu and MUST exclude migrated legacy browse/publish rule modules, source maps, and representative rule strings. This exclusion SHALL be verified against the final package, not inferred from TypeScript import reachability alone.

#### Scenario: ASAR contains a forbidden legacy module
- **WHEN** final-package inspection finds a migrated Xiaohongshu executor path or cleartext rule marker
- **THEN** the desktop build fails

#### Scenario: Ordinary non-Xiaohongshu code remains required
- **WHEN** a shared selector-free utility is still needed by another platform
- **THEN** it remains packaged only after dependency inspection proves it does not carry migrated Xiaohongshu page rules

