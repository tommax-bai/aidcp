# Tasks — self-contained-ads-runtime

> Reconciled on 2026-08-03 against current `aidcp-edge` `master`. `[x]` means source/automated evidence exists; `[~]` means explicitly cancelled and is not acceptance evidence.

## 1. Delivered source

- [x] 1.1 Build-stage the pinned AdsPower CLI, keep it outside development dependencies, place it under `extraResources`, and enforce packaged dependency/architecture gates. <!-- aidcp-edge: c3586e4, b8c9b83, 4e8b251, 680b188, f4c1323; current package/build scripts inspected 2026-08-03. Installer contents/signing remain owned by edge-desktop-packaging. -->
- [x] 1.2 Stage the template to application `userData` by application/package/content identity, atomically refresh changed templates, roll back failures, and stop the registered managed daemon before replacement. <!-- aidcp-edge: 9569fec; focused staging/runtime/lifecycle tests recorded by that change. -->
- [x] 1.3 Split service and per-version kernel ensures; establish one CLI-reported base, one key resolver, cached-base read recovery, metadata-only service gating, and managed-daemon shutdown on application quit. <!-- aidcp-edge: 12bac1d plus current main.cjs/ads-runtime.cjs source inspected 2026-08-03. The original eager warm-up/leave-daemon design was not retained. -->
- [x] 1.4 Align environment creation to the current pre-provisioned `aidcp` group contract: `group/list` then `user/create`, with `group/create` structurally forbidden. <!-- aidcp-edge: c86bd94; current ads-write-api.cjs allowlist and focused tests inspected 2026-08-03. -->
- [x] 1.5 Use V2 per-profile browser lifecycle in core and Electron paths, with bounded exact loopback CDP adoption and CDP-dark stop confirmation. <!-- aidcp-edge: e67fac4; 82 focused tests, acceptance 24/24, full Edge 1789/1789, typecheck, and live read-only reconciliation recorded in the original task evidence. -->
- [x] 1.6 Prove installed pinned kernels locally before cloud catalogue reads, classify bounded catalogue failures safely, and reject older timestamped renderer status snapshots. <!-- aidcp-edge: 1e09769; focused runtime/renderer 131/131, full Edge 3045 plus 1 gated skip, acceptance 38/38, typecheck, and local executable proof recorded in the original task evidence. No package/install/release was performed for this commit. -->
- [x] 1.7 Preserve Windows Node 24 build-time staging without direct `npm.cmd` spawn and prefer the patched staged runtime in development. <!-- aidcp-edge: 1f36bb4; build:ads-runtime, 20 focused runtime tests, typecheck. Windows installer packaging remains outside this task's acceptance claim. -->

## 2. Artifact reconciliation

- [x] 2.1 Reconcile proposal, design, spec deltas, and tasks with current source; remove duplicated packaging authority, deleted `group/create`, obsolete devDependency/eager-warmup/leave-daemon claims, speculative fallback-port/seat/download recovery, and stale progress. <!-- control-only cleanup on 2026-08-03; validated with git diff --check and openspec validate self-contained-ads-runtime --strict. -->

## 3. Cancelled scope

- [~] 3.1 Shared-key seat/concurrency exit classification and richer quota UX. <!-- Cancelled 2026-07-25; never implemented. -->
- [~] 3.2 Broad disk-full, partial-download, cancellable-download, and automatic kernel-floating recovery. <!-- Cancelled 2026-07-25; the later narrow local-kernel proof in 1.6 remains delivered. -->
- [~] 3.3 Automatic coexistence with an external AdsPower desktop service or guaranteed fallback port. <!-- Removed as unsupported by current source; managed CLI conflict now fails visibly. -->

## 4. Cancelled real-machine acceptance

> Items 4.1–4.4 were last touched on 2026-07-30. On 2026-08-03 the user cancelled every real-machine acceptance item inactive for more than three days. They MUST NOT be reported as passed.

- [~] 4.1 Fresh operator Mac install with no external AdsPower/CLI: create environment, download kernel once, and open a fingerprint browser without key input.
- [~] 4.2 Quarantined/translocated DMG staging from packaged Resources to application `userData`.
- [~] 4.3 Coexistence with an external AdsPower desktop service on 50325 using a guaranteed fallback port.
- [~] 4.4 Multi-operator shared-key seat-ceiling behavior.
