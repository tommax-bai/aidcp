## 1. Establish the migration lane

- [x] 1.1 Create the isolated `aidcp-edge` worktree/branch `centralize-mascot-visual-library` and inventory the eight source PNG hashes.
  <!-- repo=aidcp-edge; base=ca6df3b; validation=clean isolated worktree and eight SHA-256 hashes captured; deployment=n/a; deviations=none -->

## 2. Centralize shared mascot sources

- [x] 2.1 Copy the eight concept PNGs into `aidcp/docs/design/mascot/assets/` without transforming them.
  <!-- repo=aidcp; commit=2846c0f; validation=eight destination PNGs present; deployment=n/a; deviations=none -->
- [x] 2.2 Move the visual action library guidance into `aidcp/docs/design/mascot/` and cross-link it with the existing transparent-state library.
  <!-- repo=aidcp; commit=2846c0f; validation=bidirectional documentation links and design-system reference present; deployment=n/a; deviations=none -->
- [x] 2.3 Remove `aidcp-edge/docs/design/mascot/` while preserving all Electron runtime mascot assets and renderer mappings.
  <!-- repo=aidcp-edge; commit=27ca9de; validation=design source removed, three runtime assets present with no diff; deployment=n/a; deviations=none -->

## 3. Validate ownership and behavior boundaries

- [x] 3.1 Verify byte-for-byte PNG integrity, destination completeness, source removal, runtime asset presence, and repository references.
  <!-- repos=aidcp,aidcp-edge; commits=aidcp:2846c0f,aidcp-edge:27ca9de; validation=eight SHA-256 pairs byte-identical, old Edge path absent on origin/master, three runtime assets and mappings present; deployment=n/a; deviations=none -->
- [x] 3.2 Run focused Edge companion/UI tests and `npm run typecheck` in the isolated worktree.
  <!-- repo=aidcp-edge; commit=27ca9de; validation=223 focused tests, 29 acceptance tests, 2191 full tests and typecheck passed; deployment=n/a; deviations=full rerun used the identical canonical Electron 31 executable because macOS removed the fresh worktree app bundle after launch timeout -->
- [x] 3.3 Run `openspec validate centralize-mascot-visual-library --strict`.
  <!-- repo=aidcp; commit=2846c0f; validation=strict OpenSpec validation passed; deployment=n/a; deviations=none -->

## 4. Integrate and record delivery

- [x] 4.1 Commit, rebase, fast-forward integrate, and push the Edge documentation removal to `origin/master`.
  <!-- repo=aidcp-edge; commit=27ca9de; validation=rebased onto d88e490 and ff-pushed to origin/master after all gates passed; deployment=n/a; deviations=canonical checkout sync deferred because its local master is ahead 1 and behind 2 -->
- [x] 4.2 Record repository SHAs and validation evidence, then commit and push the control-repository change to `origin/main`; no deployment or Edge package is required.
  <!-- repo=aidcp; commit=2846c0f; validation=implementation and Edge SHAs recorded, strict OpenSpec validation passed; deployment=not required for documentation/assets; deviations=none -->
