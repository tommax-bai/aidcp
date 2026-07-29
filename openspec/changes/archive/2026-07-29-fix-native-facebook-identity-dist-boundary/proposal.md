## Why

The Native Facebook browse session imports pure post-identity classification from a TypeScript module that also embeds retired Facebook page-rule JavaScript. That dependency makes the production `dist` contain `facebook/cta-labels.js`, so the production-pruning gate correctly rejects a build that no longer has a Native-only dependency boundary.

## What Changes

- Separate pure Facebook post-identity parsing and Native presentation classification from the legacy DOM-helper bundle.
- Preserve the existing `facebook/post-identity` exports for remaining development-only TypeScript consumers while routing Native orchestration through the pure module.
- Add a build-level regression check and rebuild the production distribution so migrated Facebook page-rule JavaScript remains absent.
- Do not change Facebook target selection, action semantics, protocol payloads, or supported capabilities.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `native-facebook-behavior-parity`: Require the production dependency graph for Native Facebook orchestration to exclude retired TypeScript page-rule modules, including when pure identity helpers are shared.

## Impact

- Edge TypeScript module boundaries under `src/facebook/` and the Native browse-session import graph.
- Production `dist` pruning/verification tests.
- No Cloud, Console, protocol, database, installer, signing, or live-account behavior change.
