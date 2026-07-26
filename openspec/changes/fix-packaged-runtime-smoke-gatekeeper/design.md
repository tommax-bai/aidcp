## Context

`scripts/after-pack.cjs` validates the assembled ASAR and, for a same-platform/same-architecture build, launches the generated application executable with `ELECTRON_RUN_AS_NODE=1` to load `jsdom`, `tough-cookie`, and `ws` from the packaged archive. electron-builder invokes `afterPack` before its signing phase. On macOS, the generated bundle therefore has invalidated or absent signing state while still carrying downloaded-file provenance; Gatekeeper can block or move it to Trash before the smoke script runs.

The repository already installs and verifies a development Electron runtime through `scripts/ensure-electron-dev-signature.mjs`. Running that trusted Electron binary against the generated ASAR succeeds and exercises the same packaged JavaScript dependency closure without launching the unsigned intermediate application.

## Goals / Non-Goals

**Goals:**

- Preserve all current static ASAR, native artifact, and migrated-JavaScript leakage checks.
- Run the packaged JavaScript smoke on same-architecture macOS builds without launching the unsigned generated app.
- Fail with actionable evidence when the trusted runner is unavailable/invalid or the packaged smoke fails.
- Keep cross-architecture builds static-only, as they cannot safely execute the foreign target binary.

**Non-Goals:**

- Bypass or disable Gatekeeper, quarantine, XProtect, or code-signing requirements.
- Relax signed/notarized release gates.
- Change installed-client runtime behavior, package contents, cloud selection, or customer-auth URLs.
- Redesign Windows/Linux packaging where the observed macOS provenance failure does not apply.

## Decisions

1. **Use the repository's verified development Electron as the macOS smoke runner.**
   - For a same-architecture macOS target, resolve `node_modules/electron/dist/Electron.app/Contents/MacOS/Electron` and execute the smoke entry inside the generated `app.asar`.
   - Verify the runner bundle with `codesign --verify --deep --strict` before execution. A missing or invalid runner fails the build with guidance to repair dependencies/signing.
   - Rationale: the smoke is intended to prove that packaged JavaScript dependencies are loadable from ASAR. It does not need to launch the not-yet-signed product bundle.

2. **Keep the generated product executable for non-macOS same-architecture smoke.**
   - The observed blocker is macOS Gatekeeper acting between `afterPack` and signing. Avoid widening the change to platforms without evidence.

3. **Keep foreign-architecture builds static-only.**
   - Existing dependency-closure and artifact checks still run. The dynamic smoke remains skipped when target architecture differs from the host.

4. **Make child-process failures observable.**
   - Include bounded stdout/stderr and distinguish timeout/signal/exit failures in the thrown build error without converting any failure into success.

Alternatives considered:

- Disabling Gatekeeper or removing provenance attributes was rejected because it weakens the host security boundary and is not reproducible in CI/customer environments.
- Ad-hoc signing every generated intermediate App inside `afterPack` was rejected because deep signing is slow, mutates the artifact before the normal signing phase, and duplicates electron-builder responsibility.
- Moving the smoke to `afterSign` was rejected because unsigned local builds would still fail and the static ASAR gates appropriately belong immediately after packing.

## Risks / Trade-offs

- **The development Electron could differ from the packaged framework.** → Both are sourced from the same locked Electron dependency; tests assert deterministic runner resolution, and code-sign verification fails closed.
- **The trusted runner proves ASAR JavaScript loading but not product-bundle launch.** → Product-bundle trust remains covered by the existing signed/notarized release gates; native artifact structure remains checked separately during `afterPack`.
- **Child output could be noisy or contain unrelated environment data.** → Report only bounded stdout/stderr from the dedicated smoke script.
