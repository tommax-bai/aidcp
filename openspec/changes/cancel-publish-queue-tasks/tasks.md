## 1. Console Cancellation Behavior

- [x] 1.1 Extend the Console delegated-task view with cancellation-request evidence and add a versioned cancel mutation on the Publish Queue page.
- [x] 1.2 Add a per-task confirmation control, corresponding-task pending state, truthful terminal versus safe-boundary feedback, and cancel-in-progress rendering.
- [x] 1.3 Refresh delegated-task and publish-lifecycle truth after successful cancellation, and refresh without retry after version conflicts while preserving failed task cards.
  <!-- `aidcp-console`: `DelegatedTaskView.cancelRequested`, CAS `POST /api/delegated-tasks/:id/cancel`, per-card Popconfirm/loading, terminal versus safe-boundary messages, and delegated-task plus lifecycle invalidation implemented in the isolated worktree. -->

## 2. Regression Coverage

- [x] 2.1 Cover confirmation dismissal, exact task id/version submission, pending duplicate prevention, immediate terminal removal, and query refresh.
- [x] 2.2 Cover planning-task cancellation-in-progress, version-conflict refresh, and human-readable failure feedback without raw codes.
  <!-- Focused `ContentPage.test.tsx`: 37/37 passed with one worker; the first max-only worker command ran no tests because Vitest min/max conflicted, then the explicit min=1/max=1 rerun passed. Existing jsdom getComputedStyle warnings remain non-fatal. -->

## 3. Validation and Delivery

- [x] 3.1 Run focused and full Console tests, typecheck, and production build from the isolated worktree.
  <!-- `aidcp-console`: focused ContentPage 37/37; full Vitest with min/max workers 1: 35 files, 225 passed, 1 pre-existing skipped; `npm run typecheck` passed; production build passed with 3725 modules and the existing large-chunk warning only. -->
- [x] 3.2 Run `openspec validate cancel-publish-queue-tasks --strict` and record implementation evidence.
  <!-- `openspec validate cancel-publish-queue-tasks --strict` passed on 2026-07-20. -->
- [ ] 3.3 Rebase, integrate, and push the Console and control-repo changes without force.
  <!-- Console feature commit ready for integration: `aidcp-console` `a716686`. -->
- [ ] 3.4 Deploy rebuilt Console assets from the clean default checkout to `dev`, then verify served assets, routes, health, and readiness without restarting Cloud.
