## 1. Edge presentation

- [x] 1.1 Default the slow-start help and copy to hidden, then reveal them only from the last confirmed active/graduated view while resetting them for hidden, loading, and error states.
  <!-- aidcp-edge: static help/copy default hidden; renderer reveals them from confirmed view.checked and resets them for row-hidden/loading/error paths. Pending target state never drives guidance visibility. -->
- [x] 1.2 Add focused renderer regressions for confirmed off/active/graduated guidance visibility, non-optimistic pending writes, and unknown/cross-environment isolation.
  <!-- aidcp-edge: `npx tsx --test test/electron/renderer-smoke.test.ts` passed 109/109 in 38.6s. Coverage asserts default/unknown/error/off hidden, active/graduated visible, pending uses the prior confirmed visibility, and A late receipts do not alter B. -->

## 2. Validation and integration

- [x] 2.1 Run focused Edge tests, Edge typecheck, `git diff --check`, and `openspec validate hide-inactive-facebook-slow-start-guidance --strict`; record exact evidence and the static-table authority boundary.
  <!-- 2026-08-03 validation: Edge renderer smoke passed 109/109 in 38.6s; `npm run typecheck` passed; Edge and control `git diff --check` passed; strict OpenSpec validation passed. Authority audit: the Edge help table remains literal HTML, while Cloud target-global `slowStart.totalDays/dailyCaps` is editable and the customer env slow-start route returns only state/totalDays plus optional current-day quotas. The full table is not backend-linked; no Cloud/API expansion was made in this scoped fix. -->
- [x] 2.2 Commit and push the isolated Edge branch, fast-forward it to the current default branch after rebase and validation, and close out without packaging, installing, deploying, or touching OL.
  <!-- aidcp-edge `e49808688907b94819de68081a08e28879f51c32` was committed on `codex/hide-inactive-facebook-slow-start-guidance`, pushed, then fast-forwarded to `origin/master`; the canonical master synced to the same commit while preserving its unrelated `dist-electron.backup-20260803-143101/`. No Edge package/build/install, Cloud/Console change, deployment, database action, or OL action was performed. -->
