## 1. Contract and protocol

- [x] 1.1 Add OpenSpec design/spec/tasks for browser cold standby.
- [x] 1.2 Extend `ui.snapshot` protocol/types/docs with optional `browserStandby`.
  <!-- aidcp-cloud + aidcp-edge: UiBrowserStandbyPayload added to mirrored protocol.ts; docs/protocol.md updated. -->

## 2. Cloud wait estimation

- [x] 2.1 Add a deterministic browser-standby hint builder with default-on env switch, threshold, and warmup.
  <!-- aidcp-cloud 6be48be: src/comm/browser-standby.ts, default enabled, 20min threshold, 90s warmup. -->
- [x] 2.2 Thread the hint into UI snapshot publishing for per-account edge sessions.
  <!-- aidcp-cloud 6be48be: UiSnapshotService and server wiring include browserStandby on hello/usage refresh snapshots. -->
- [x] 2.3 Add focused cloud tests for eligible quota waits, disabled switch, short waits, no waits, and snapshot forwarding.
  <!-- validation: ./node_modules/.bin/tsx --test test/comm/browser-standby.test.ts test/comm/ui-snapshot.test.ts test/acceptance/protocol-contract.test.ts (pass, with temporary node_modules symlink removed after run). -->

## 3. Edge lifecycle

- [x] 3.1 Add protocol/UI-event sanitization for `browserStandby`.
  <!-- aidcp-edge c6622e4: uiSnapshotToLines sanitizes browserStandby into structured [ui-event]. -->
- [x] 3.2 Add edge local default-on switch, hint normalization, and safety decision helper.
  <!-- aidcp-edge c6622e4: browser-cold-standby.cjs + renderer setting toggle default enabled. -->
- [x] 3.3 Add Electron supervisor cold-standby scheduling, close, wake, and manual-cancel behavior.
  <!-- aidcp-edge c6622e4: lifecycle.standby keeps cloud connection while closing browser; wake timer/manual/cloud-command wake paths added. -->
- [x] 3.4 Add focused edge tests for event forwarding, decision logic, defaults, and lifecycle source guards.
  <!-- validation: ./node_modules/.bin/tsx --test test/flows/ui-event-lines.test.ts test/electron/browser-cold-standby.test.ts test/client/core-lifecycle.test.ts test/electron/lifecycle-contract.test.ts test/electron/renderer-smoke.test.ts test/acceptance/protocol-contract.test.ts (pass, with temporary node_modules symlink removed after run). -->

## 4. Validation and closeout

- [x] 4.1 Run relevant cloud tests/typecheck.
  <!-- validation: targeted cloud tests pass; npm run typecheck pass. Initial npm test attempt accidentally invoked full glob and failed due worktree dependency resolution, not test failures. -->
- [x] 4.2 Run relevant edge tests/typecheck.
  <!-- validation: targeted edge tests pass; npm run typecheck pass. Initial npm test attempt accidentally invoked full glob and was interrupted after dependency-resolution failures. -->
- [x] 4.3 Run `openspec validate browser-cold-standby-next-action --strict`.
  <!-- validation: openspec validate browser-cold-standby-next-action --strict pass. -->
- [x] 4.4 Commit/push scoped changes and record commit SHAs/validation notes.
  <!-- commits: aidcp-cloud 6be48be, aidcp-edge c6622e4; control commit amended with this record. Push pending after final clean status. -->
