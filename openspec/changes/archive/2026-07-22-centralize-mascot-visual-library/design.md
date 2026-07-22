## Context

`aidcp-edge/docs/design/mascot/` contains eight reusable concept PNGs plus guidance for visual identity, semantic selection, generation, and production derivation. These materials are not wired into Edge. The control repository already owns the broader design system and the transparent mascot state/animation library under `docs/design/mascot-transparent/`, while Edge separately owns three packaged 512px runtime images.

The migration must separate shared source ownership from application packaging: design sources and cross-product rules belong in `aidcp`, but an Electron build cannot safely depend on a sibling checkout being present.

## Goals / Non-Goals

**Goals:**

- Establish `aidcp/docs/design/mascot/` as the canonical home for the reusable visual action library.
- Keep the concept PNGs byte-identical during relocation.
- Connect the action library to the existing transparent-state library and document which asset family to use.
- Remove the redundant/misplaced shared source directory from Edge without changing its runtime behavior.

**Non-Goals:**

- Replacing, renaming, regenerating, or optimizing Edge's packaged runtime PNGs.
- Changing renderer state mapping, UI copy, animation, protocol, APIs, dependencies, or package output.
- Introducing a cross-repository runtime import, submodule, symlink, or build-time network fetch.

## Decisions

### Keep shared sources under `aidcp/docs/design/`

The visual action library will retain its existing `mascot/README.md` and `mascot/assets/` structure under the control repository. This keeps the links self-contained and places it beside `mascot-transparent/`, the existing shared mascot state and animation set.

An alternative was to place the files at the repository root. That would make product-design assets top-level peers of orchestration and OpenSpec directories and would break the established `docs/design/` organization, so it is rejected.

### Keep runtime packaging assets local to Edge

The three files under `aidcp-edge/src/electron/renderer/assets/` remain unchanged. Shared source ownership does not imply that application builds should reach into another checkout. Future Edge, Console, or Cloud UI work must derive or copy the selected asset into that application's own packaging tree and validate the copy there.

An alternative was to make Edge import the control-repository path. That would make clean clones, CI, and desktop packaging depend on a sibling repository layout, so it is rejected.

### Relocate the current library without image transformation

The eight concept PNGs will be copied byte-for-byte into the control repository, verified by SHA-256, and then removed from the isolated Edge change. The README will be adjusted only for ownership, relative cross-links, and application-consumer wording.

Regenerating or re-encoding the images during the move is rejected because it would mix content changes with ownership migration and make integrity review harder.

## Risks / Trade-offs

- [Risk] Consumers may confuse shared source art with packaged assets. → Mitigation: document the source-versus-runtime boundary in the shared README and spec.
- [Risk] One repository receives files while the other still retains the old copy. → Mitigation: validate both Git diffs together and record both commit SHAs in `tasks.md`.
- [Risk] Binary corruption or accidental transformation during transfer. → Mitigation: compare per-file SHA-256 hashes before committing.
- [Trade-off] Runtime consumers keep local copies. → This intentionally duplicates selected production assets to preserve independent builds; the control repository remains the source for reusable design concepts.

## Migration Plan

1. Create an isolated `aidcp-edge` worktree named `centralize-mascot-visual-library`.
2. Copy `docs/design/mascot/` into `aidcp/docs/design/mascot/` and update its shared-ownership guidance and cross-links.
3. Remove only `docs/design/mascot/` from the Edge worktree; retain all files under `src/electron/renderer/assets/`.
4. Verify source/destination hashes, references, focused Edge tests, typecheck, and strict OpenSpec validation.
5. Commit and fast-forward the Edge change, then commit the control-repository artifacts and shared assets.

Rollback is a Git revert in each repository. No deployed service, database, or package state is involved.

## Open Questions

None. The existing repository layout and current references determine the ownership and packaging boundary.
