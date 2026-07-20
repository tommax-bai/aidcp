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
- [x] 3.3 Rebase, integrate, and push the Console and control-repo changes without force.
  <!-- Both branches were rebased against current origins with no changes, then fast-forward pushed and synced to clean canonical defaults: `aidcp-console/master` `a716686`; `aidcp/main` OpenSpec artifacts `80183e1`. No force push. -->
- [x] 3.4 Deploy rebuilt Console assets from the clean default checkout to `dev`, then verify served assets, routes, health, and readiness without restarting Cloud.
  <!-- Target `dev` passed `scripts/deploy-target dev --check`. Backup: `/opt/aidcp/console.bak.20260720-232410.tar.gz`. Built and deployed clean canonical `aidcp-console/master` `a716686`: `index-B6mMKwv_.js` SHA-256 `1e889c59b65d1e8dfcea0931e5c11786a43ab3c4dee1af37fdf48dce30ca2e43`, `index-D92vcMm-.css` SHA-256 `d6203ccd52b7652fe1ab5e1cb5324396c63b036bcf170b8a4bf8b5c0246aeed1`; local, remote file, and served HTTP hashes matched. `/`, `/content`, `/publish-queue`, and `/api/health` returned 200; direct panel health returned `{"ok":true}`; Cloud remained active/running with `NRestarts=0`; 8787/8088/8090 listened and PostgreSQL accepted connections. No Cloud restart or unrelated service change. Authenticated browser acceptance was not completed: the in-app browser reached the login gate without a session, and the selected Chrome profile lacked the control extension; no real queued task was cancelled. -->
