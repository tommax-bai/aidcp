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
  <!-- Corrected production build passed (3724 modules). Structural render covers one direct Overview link, five desktop flyout triggers, hover/click menus, and a 14-item/6-group narrow menu. Deployed CSS confirms the 960px grouped-menu breakpoint and no secondary-row selector. Pixel-width authenticated browser verification remains open: local and dev browser sessions correctly stopped at login, and no authentication bypass was introduced. -->
- [x] 3.3 Run `openspec validate group-admin-console-navigation --strict` and record implementation evidence.
  <!-- `openspec validate group-admin-console-navigation --strict` passed on 2026-07-20. -->

## 4. Integration and Development Deployment

- [x] 4.1 Commit the console implementation, rebase and fast-forward it onto the latest `aidcp-console` default branch, and push without force.
  <!-- aidcp-console `694db0f51c7968d22e0fa9a597b522b7531fb545`; pushed ff-only to `origin/master` and canonical master synchronized. Full Vitest passed with constrained workers after two unrelated high-concurrency flakes were reproduced as focused passes. -->
- [x] 4.2 Commit and push the OpenSpec artifacts with console commit, validation, deployment, and deviation evidence.
  <!-- Control-repo artifact commit stages only `openspec/changes/group-admin-console-navigation/`; unrelated existing untracked paths remain untouched. Dependency deviation: this console repo has no package lock, so `npm ci` was impossible; the worktree used a physical `npm install --prefer-offline --no-package-lock` tree instead. -->
- [x] 4.3 Deploy the rebuilt console assets from the clean default checkout to `dev`, then verify HTTP health and the served navigation asset.
  <!-- Target `dev` passed `scripts/deploy-target dev --check`. Backup: `/opt/aidcp/console.bak.20260720-120345.tar.gz`. Deployed canonical `aidcp-console/master` commit `694db0f` assets `index-BO0GCDOY.js` + `index-Cq1Utq7V.css`; remote asset markers verified. `aidcp-cloud.service` active; 8787/8088/8090 listening; `/`, `/content`, `/accounts`, and `/api/health` returned HTTP 200. No service restart or unrelated service change. -->

## 5. Visual Acceptance Correction: Floating Group Menus

- [x] 5.1 Replace the rejected persistent secondary-row design in the proposal, design, and behavior contract with single-row desktop group navigation and non-layout floating menus.
  <!-- Updated after operator visual review on 2026-07-20; the approved direction keeps Overview direct and gives multi-destination groups hover, click, and keyboard-accessible floating menus. -->
- [x] 5.2 Replace the persistent desktop destination row with compact per-group floating menus while preserving current group/destination state and the existing narrow menu.
  <!-- Implemented in the console worktree: Overview stays direct; the other five semantic buttons open route-derived vertical menus on hover/click, retain boundary-aware active state, and leave the existing narrow grouped menu unchanged. -->
- [x] 5.3 Add focused interaction coverage and rerun console tests, typecheck, and build.
  <!-- AppShell focused 14/14; full console Vitest 34 files, 210 passed and 1 pre-existing skipped; `npm run typecheck` passed; production build passed with 3724 modules and assets `index-BDsxPzec.js` + `index-B5zsgl89.css`. Worktree dependencies are physical; no lockfile exists, so installation used `npm install --prefer-offline --no-package-lock` instead of impossible `npm ci`. -->
- [ ] 5.4 Visually verify desktop hover/click behavior and narrow navigation without overflow or page displacement.
  <!-- Automated interaction and structural checks passed, but authenticated pixel inspection remains operator-gated; the controlled local/dev browser reached the normal login page and no bypass was attempted. -->
- [x] 5.5 Run strict OpenSpec validation and record the correction's implementation evidence.
  <!-- `openspec validate group-admin-console-navigation --strict` passed after the floating-menu contract and implementation evidence were updated. -->
- [x] 5.6 Commit, rebase, fast-forward to the latest defaults, push without force, and deploy the corrected static assets to `dev` from the clean console checkout.
  <!-- Console `b76e65277aa603e05678f1d776c3f517c302bb67` was rebased on the latest `origin/master`, revalidated, fast-forward pushed, and synchronized to the clean canonical checkout. Target `dev` passed `scripts/deploy-target dev --check`; backup `/opt/aidcp/console.bak.20260720-143657.tar.gz` was created before deploying canonical assets `index-B81tMW9v.js` + `index-B5zsgl89.css`. Served assets contain `group-nav-menu__link`/`group-nav-dropdown` and omit the removed secondary-row CSS marker; `/quotas` and `/api/health` returned HTTP 200, `aidcp-cloud.service` remained active, and 8787/8088/8090 remained listening without a restart. The control artifact commit stages only this change directory. -->

## 6. Visual Acceptance Correction: Compact Desktop Flyout

- [x] 6.1 Record the approved compact flyout dimensions, left-edge anchoring, lighter hierarchy, and open-trigger state in the design.
- [x] 6.2 Apply the compact desktop flyout styling and open-state treatment without changing routes, grouping, or the narrow menu.
  <!-- Implemented only in `AppShell.tsx`, its focused test, and scoped navigation CSS: desktop menus now anchor `bottomLeft`, expose controlled open state, rotate the chevron, and use the approved compact visual tokens. -->
- [x] 6.3 Rerun focused/full console tests, typecheck, build, and strict OpenSpec validation.
  <!-- AppShell focused 14/14, typecheck, production build (3724 modules; worktree assets `index-xfLE92oz.js` + `index-KtBLIlMd.css`), and strict OpenSpec validation passed. Full Vitest under current shared-machine load reached 213 passed/1 skipped with one unrelated 5s timeout in `WechatChannelsReplySettings.scope.test.tsx`; the same scope test passed all assertions in isolation with a diagnostic-only 20s CLI budget (13.1s test body). The repository timeout configuration was not changed. Earlier four unrelated timeouts likewise passed in isolated default-budget reruns (Facebook 8/8, WeChat 36/36). -->
- [x] 6.4 Commit and fast-forward both repositories, deploy from the clean console default checkout to `dev`, and verify the served assets and health endpoints.
  <!-- Console commit `8b111c94a8cf2851078eac2c55c0f9fef8730ee9` was rebased onto the latest `origin/master`, revalidated, fast-forward pushed, and synchronized to the clean canonical checkout. Target `dev` passed `scripts/deploy-target dev --check`; backup `/opt/aidcp/console.bak.20260720-151331.tar.gz` was created before deploying canonical assets `index-D0u9T3on.js` + `index-BWIuhYCB.css`. Served assets contain the controlled open-state, `bottomLeft`, 176px flyout, 6px gap, and rotated-chevron markers; `/accounts` and `/api/health` returned HTTP 200, `aidcp-cloud.service` remained active, and 8787/8088/8090 remained listening without a restart. The control artifact commit stages only this change directory. -->
