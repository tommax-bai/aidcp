## 1. Isolated setup

- [x] 1.1 Create the matching `aidcp-edge` worktree on `codex/client-draft-image-lightbox` and install a physical worktree-local dependency tree with `npm ci --prefer-offline`. <!-- aidcp-edge worktree created from origin/master; npm ci added 365 packages with no shared dependency link -->

## 2. Client lightbox implementation

- [x] 2.1 Add one reusable, accessible draft-image dialog to the Electron renderer shell with close controls and no network or approval behavior. <!-- aidcp-edge index.html + renderer.js -->
- [x] 2.2 Bind draft thumbnails to double-click open behavior and keep the dialog synchronized with the current record and server-authoritative image list. <!-- recordId + image URL truth check; close review also closes lightbox -->
- [x] 2.3 Add viewport-bounded contain-mode lightbox styling and a zoom affordance without changing the existing gallery or delete-confirm layout. <!-- contain-mode dialog, zoom-in cursor, focused thumbnail ring -->

## 3. Regression validation

- [x] 3.1 Add focused renderer tests for double-click open, single-click/delete isolation, close controls, and stale-context cleanup. <!-- companion-ui.test.ts covers click/dblclick, button/backdrop/Escape, delete confirmation, new record and stale fallback -->
- [x] 3.2 Run the focused Electron UI tests and `npm run typecheck` in the edge worktree. <!-- PASS: companion-ui + content-workspace 83/83; PASS: tsc --noEmit -->

## 4. Integration and contract closeout

- [x] 4.1 Run `openspec validate client-draft-image-lightbox --strict` and record validation evidence and scope deviations in this task file. <!-- PASS 2026-07-20; deviations: none; no protocol/cloud/package changes -->
- [x] 4.2 Commit the edge implementation, rebase on current `origin/master`, rerun required validation, fast-forward push to `origin/master`, and sync the canonical edge checkout without building an installer. <!-- aidcp-edge 48e21da; rebased; post-rebase 83/83 + typecheck PASS; pushed HEAD:master; canonical ff synced -->
- [x] 4.3 Record the landed edge commit and final verification boundary in this task file so the completed change is ready to archive. <!-- landed: aidcp-edge 48e21da; source-only UI change; no Cloud/API/protocol/deploy/package action required or performed -->
