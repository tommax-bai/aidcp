## 1. Edge implementation

- [x] 1.1 Restore the draft-review approve/cancel handler to call the existing `publishApproval` IPC with the selected environment, requestId, decision, and current content version.
- [x] 1.2 Keep the review page open and show named Cloud rejection reasons on failure; close and project only the accepted approval decision on `ok:true`.
- [x] 1.3 Preserve delegated candidate controls for their independent entry points while ensuring the draft-review approval buttons never create delegated tasks.

## 2. Regression coverage

- [x] 2.1 Update renderer tests to prove approval clicks call `publishApproval`, do not call `delegatedTaskDraft`, and pass the authoritative versioned payload.
- [x] 2.2 Add success/failure behavior coverage: success closes and projects the decision; failure keeps the review page open, shows the named reason, and does not mutate approval state.
- [x] 2.3 Run focused Electron approval/content-workspace tests, acceptance tests, the full Edge suite, syntax checks, and typecheck without packaging.
  <!-- After rebase: focused companion + client RPC tests 67/67; acceptance 24/24; syntax and typecheck pass. Full suite ran 1747 tests: 1745 pass, with two unrelated baseline failures reproduced unchanged on canonical master (`core-log-severity` static contract and Windows JWT 0600 mode assertion). No packaging invoked. -->

## 3. OpenSpec and integration

- [x] 3.1 Run `openspec validate restore-client-direct-publish-approval --strict` and record validation evidence plus the Edge commit SHA in this checklist.
  <!-- Strict validation passed; final rebased aidcp-edge implementation commit `d7bb280` on branch `restore-client-direct-publish-approval`. -->
- [x] 3.2 Rebase the isolated Edge worktree onto the latest `origin/master`, rerun required validation, and fast-forward the default branch without force-pushing.
  <!-- Rebased onto `origin/master` at `1f36bb4`, reran focused 67/67 + acceptance 24/24 + typecheck/syntax, then fast-forward pushed aidcp-edge/master to `d7bb280`; no force-push. -->
- [x] 3.3 Record that no Cloud deployment or Edge package was performed; register any required real-machine/package follow-up separately.
  <!-- No Cloud runtime change/deployment and no Edge package. Real-machine/package follow-up registered as `docs/real-machine-acceptance-backlog.md` 93.10. -->
