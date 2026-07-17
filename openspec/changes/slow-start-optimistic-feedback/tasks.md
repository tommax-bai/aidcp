## 1. Renderer Mutation State

- [x] 1.1 Replace the global slow-start pending boolean with env-scoped pending/error feedback that preserves authoritative snapshots.
- [x] 1.2 Render immediate opening/closing feedback, busy semantics, and a visible waiting-for-cloud message without locally inventing day or quota values.
- [x] 1.3 Reconcile successful PUT receipts into the originating environment with cloud-returned `slowStart` and `dayQuotas`; roll failures back to snapshot truth and retain the reason.

## 2. Visual Treatment

- [x] 2.1 Add a compact pending treatment for the slow-start row and badge that remains legible while the switch is disabled.
- [x] 2.2 Keep pending and error feedback isolated when the selected environment changes.

## 3. Verification

- [x] 3.1 Add jsdom coverage for immediate enable/disable pending states, stale snapshot resistance, successful receipt reconciliation, and failure rollback/error persistence. <!-- focused renderer smoke: 50 pass / 0 fail -->
- [x] 3.2 Run focused Electron renderer tests, then the required Edge acceptance, full test, and typecheck sequence. <!-- focused 50/50; pre-integration acceptance 23/23 + full 1657/1657 + typecheck 0; post-rebase acceptance 23/23 + full exit 0 + typecheck 0 -->
- [x] 3.3 Run `openspec validate slow-start-optimistic-feedback --strict` and record validation evidence and implementation commit SHAs in this checklist. <!-- strict pass; aidcp-edge 0d38116 landed origin/master (rebased from be579de) -->

## 4. Closeout

- [x] 4.1 Commit and push the Edge implementation branch; do not package or release an installer without an explicit request. <!-- aidcp-edge 0d38116 ff-pushed origin/master; no installer built -->
- [x] 4.2 Commit and push the control-repo OpenSpec branch, preserving the dirty canonical checkout and documenting that no cloud deployment is required. <!-- aidcp 13341e3 + closeout follow-up; canonical checkout untouched; renderer-only change, no cloud deploy -->
