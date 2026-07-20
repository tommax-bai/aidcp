## 1. Navigation Model

- [x] 1.1 Add the six-group catalog and assign every visible console route to exactly one group while preserving existing URLs.
- [x] 1.2 Add pure active-navigation derivation and focused tests for group membership, direct routes, nested routes, settings context, and prefix boundaries.

## 2. Header Surfaces

- [x] 2.1 Replace the flat desktop destination strip with labelled primary groups and a persistent current-group destination row.
- [x] 2.2 Add a labelled grouped narrow-width navigation menu while retaining Download, Settings, and User actions.
- [x] 2.3 Update header styles to remove the icon-only collapse and keep desktop, compact desktop, and narrow layouts bounded.

## 3. Validation

- [x] 3.1 Run focused navigation tests and the console typecheck.
  <!-- aidcp-console worktree: focused AppShell + route tests 15/15; full Vitest 76/76 files, 205 passed, 1 pre-existing skipped; `npm run typecheck` passed. -->
- [ ] 3.2 Build the console and visually verify representative desktop and narrow widths without horizontal header overflow.
  <!-- `npm run build` passed (3724 modules). Structural render covers six desktop groups, the three-item Content row, and a 14-item/6-group narrow menu. Deployed CSS confirms the 960px grouped-menu breakpoint. Pixel-width browser verification remains open: the local/live shell requires an authenticated session, and the browser rejected an embedded preview page; no bypass was attempted. -->
- [x] 3.3 Run `openspec validate group-admin-console-navigation --strict` and record implementation evidence.
  <!-- `openspec validate group-admin-console-navigation --strict` passed on 2026-07-20. -->

## 4. Integration and Development Deployment

- [x] 4.1 Commit the console implementation, rebase and fast-forward it onto the latest `aidcp-console` default branch, and push without force.
  <!-- aidcp-console `694db0f51c7968d22e0fa9a597b522b7531fb545`; pushed ff-only to `origin/master` and canonical master synchronized. Full Vitest passed with constrained workers after two unrelated high-concurrency flakes were reproduced as focused passes. -->
- [x] 4.2 Commit and push the OpenSpec artifacts with console commit, validation, deployment, and deviation evidence.
  <!-- Control-repo artifact commit stages only `openspec/changes/group-admin-console-navigation/`; unrelated existing untracked paths remain untouched. Dependency deviation: this console repo has no package lock, so `npm ci` was impossible; the worktree used a physical `npm install --prefer-offline --no-package-lock` tree instead. -->
- [x] 4.3 Deploy the rebuilt console assets from the clean default checkout to `dev`, then verify HTTP health and the served navigation asset.
  <!-- Target `dev` passed `scripts/deploy-target dev --check`. Backup: `/opt/aidcp/console.bak.20260720-120345.tar.gz`. Deployed canonical `aidcp-console/master` commit `694db0f` assets `index-BO0GCDOY.js` + `index-Cq1Utq7V.css`; remote asset markers verified. `aidcp-cloud.service` active; 8787/8088/8090 listening; `/`, `/content`, `/accounts`, and `/api/health` returned HTTP 200. No service restart or unrelated service change. -->
