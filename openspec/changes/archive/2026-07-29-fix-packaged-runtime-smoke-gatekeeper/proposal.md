## Why

The macOS `afterPack` hook executes the newly assembled `AIDCP.app` before electron-builder signs it. On hosts that enforce Gatekeeper provenance, macOS blocks or moves that unsigned intermediate app to Trash, so a valid arm64 package build fails after the static ASAR checks even though the packaged runtime itself is loadable.

## What Changes

- Keep the existing packaged dependency-closure, native artifact, and migrated-JavaScript leakage gates.
- Execute the packaged ASAR runtime smoke with a verified same-version, same-architecture development Electron runtime instead of launching the unsigned intermediate `AIDCP.app`.
- Fail honestly when the trusted smoke runner is missing, has the wrong architecture/version, or the packaged runtime cannot load.
- Add regression coverage for runner selection and for the macOS Gatekeeper-safe execution boundary.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-desktop-packaging`: Require packaged runtime smoke validation to avoid executing an unsigned macOS intermediate application while preserving fail-closed artifact validation.

## Impact

- Edge packaging hook: `aidcp-edge/scripts/after-pack.cjs`.
- Edge packaging contract tests under `aidcp-edge/test/electron/`.
- No cloud, console, protocol, database, or installed-client runtime behavior changes.
