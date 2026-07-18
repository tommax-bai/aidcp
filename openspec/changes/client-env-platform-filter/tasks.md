## 1. Edge implementation

- [x] 1.1 Create the isolated `aidcp-edge` worktree for `client-env-platform-filter`.
- [x] 1.2 Add the expanded-rail platform filter control, default `all` renderer state, filtered list/count/empty-state rendering, and visible-selection synchronization.
- [x] 1.3 Pass the filtered environment ID scope through `fleet:startAll`, preserve it across force confirmation, and make the main process intersect requested IDs with live roster handles.

## 2. Validation and closeout

- [x] 2.1 Add renderer regression coverage for default-all, each platform filter, empty results, selection synchronization, and filtered/force start-all payloads.
- [x] 2.2 Add focused coverage for the main-process scoped start-all boundary and run focused Electron tests.
- [x] 2.3 Run the Edge acceptance suite, full test suite, and typecheck.
- [x] 2.4 Run strict OpenSpec validation and record repository commits, validation results, and any deviations in this task file.
- [x] 2.5 Rebase, commit, fast-forward push the Edge and control changes to their default branches; no Edge package or runtime deployment is required.

<!--
Implementation evidence (2026-07-18):
- aidcp-edge commit: 2dd3993 (rebased and fast-forward pushed to `origin/master`)
- focused: `tsx --test test/electron/fleet-console.test.ts test/electron/fleet.test.ts` -> 64/64 passed
- acceptance: `npm run test:acceptance` -> 24/24 passed (real-machine E2E remained gated)
- full suite before integration: `npm test` -> 1727/1727 passed
- integration rerun after rebase: acceptance 24/24, full suite 1729/1729, typecheck passed
- typecheck: `npm run typecheck` -> passed
- OpenSpec: `openspec validate client-env-platform-filter --strict` -> passed
- deployment/package: not applicable; this is an Edge desktop source change and no installer was requested
-->
