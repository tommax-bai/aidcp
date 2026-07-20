## 1. Edge command diagnostic events

- [x] 1.1 Add a pure command-diagnostic formatter with active-command classification, stage vocabulary, short correlation keys, and per-command payload-summary whitelists.
- [x] 1.2 Emit received, rejected, dispatched, and directly observable plan-step result events from `EdgeClient` without changing command routing or handler concurrency.
- [x] 1.3 Remove raw plan reason, action identifiers, and result detail from the existing command receipt/result log lines.

## 2. Electron projection and developer UI

- [x] 2.1 Add a defensive Electron-side structured-line parser and per-environment 50-item/30-minute diagnostic projection through the existing fleet status channel.
- [x] 2.2 Redact structured diagnostic JSON from the raw-log stream while preserving a fixed safe trace line.
- [x] 2.3 Add the developer-details command list with safe stage labels, summary, time, correlation id, empty state, current-environment isolation, and no ordinary activity entries.

## 3. Verification and documentation

- [x] 3.1 Add EdgeClient tests for active command families, rejection paths, stage honesty, unknown fields, and sensitive payload non-disclosure.
- [x] 3.2 Add Electron parser/renderer tests for validation, bounded retention, stage upsert, environment switching, null-safe legacy status, and raw-log redaction.
- [x] 3.3 Run focused Edge tests, the full Edge test suite, and Edge typecheck; record exact results.
  <!-- aidcp-edge: focused command/client/electron/renderer 129/129; acceptance 26/26 with real-machine E2E gated by AIDCP_E2E=1; full suite 2001/2001; npm run typecheck passed. No real platform action or packaged-client validation was performed. -->
- [x] 3.4 Update the Edge interface description and run strict OpenSpec validation.
  <!-- aidcp: docs/design/edge-ui-interface-spec-v1.md updated; openspec validate client-engine-command-diagnostics --strict passed. -->

## 4. Integration

- [x] 4.1 Commit the Edge and control-repo changes with explicit pathspecs and record commit SHAs, validation, and the no-package/no-runtime-deploy boundary in this checklist.
  <!-- aidcp-edge commit=5938be7; control artifacts/docs are committed with this task update. Source validation only: no desktop installer/package, installed-client acceptance, Cloud deploy, or real platform action. -->
- [ ] 4.2 Rebase/integrate serially onto the latest eligible default branches, rerun required gates, and push without force.
