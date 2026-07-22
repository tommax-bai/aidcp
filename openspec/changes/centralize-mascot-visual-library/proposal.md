## Why

Reusable AIDCP mascot concepts and their semantic usage rules currently live in the Edge implementation repository even though they are shared product-design assets. Centralizing their source-of-truth in the control repository keeps brand guidance available to Edge, Cloud, Console, documentation, and future surfaces without making one client repository the owner.

## What Changes

- Move the reusable mascot visual action library, source PNGs, generation anchors, and semantic usage guidance from `aidcp-edge/docs/design/mascot/` to `aidcp/docs/design/mascot/`.
- Cross-link the action library with the existing shared transparent-state and animation library under `aidcp/docs/design/mascot-transparent/`.
- Keep the three Electron runtime PNGs under `aidcp-edge/src/electron/renderer/assets/`; they remain application packaging inputs rather than shared design sources.
- Verify the relocated PNGs byte-for-byte and confirm that Edge runtime rendering and tests continue to use their existing packaged assets.

## Capabilities

### New Capabilities

- `shared-mascot-visual-library`: Defines ownership, semantic selection, and runtime-consumption boundaries for reusable AIDCP mascot assets.

### Modified Capabilities

None.

## Impact

- Control repository: adds `docs/design/mascot/`, updates shared design documentation, and records the ownership contract.
- Edge repository: removes the misplaced design-source directory while retaining all runtime assets and application references.
- No protocol, API, product behavior, deployment, package, or dependency changes.
