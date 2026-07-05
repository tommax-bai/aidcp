## 1. OpenSpec

- [x] 1.1 Create proposal, design, and `console-static-entry-routing` spec delta.
- [x] 1.2 Validate `add-intro-html-route` with `openspec validate --strict`.
  <!-- 2026-07-05 local: openspec validate add-intro-html-route --strict passed. -->

## 2. aidcp-console

- [x] 2.1 Work in a clean console worktree/branch for this change.
  <!-- aidcp-console worktree: ../aidcp-console.wt/add-intro-html-route on codex/add-intro-html-route from origin/master. -->
- [x] 2.2 Add `/intro.html` as a hidden protected route alias that redirects to `/`.
- [x] 2.3 Add focused route regression coverage for unauthenticated and authenticated `/intro.html` loads.

## 3. Validation And Release

- [x] 3.1 Run focused console route tests.
  <!-- aidcp-console worktree: npm test -- src/routes.intro.test.tsx passed (3 tests). -->
- [x] 3.2 Run full console validation (`npm test` and `npm run build`).
  <!-- aidcp-console worktree: npm test passed (48 passed, 1 skipped); npm run build passed. Existing React Router/jsdom warnings and Vite chunk-size warning only. -->
- [x] 3.3 Update task notes with commits, validation, and deployment outcome.
  <!-- commits: aidcp-console 7339c4f pushed to master. -->
  <!-- validation: openspec validate add-intro-html-route --strict passed; aidcp-console npm test -- src/routes.intro.test.tsx passed (3 tests); npm test passed (48 passed, 1 skipped); npm run build passed. -->
  <!-- deployment: ECS 121.89.85.150 console static release updated from clean origin/master snapshot 7339c4f; backup /opt/aidcp/console.bak.20260705-164801.tar.gz; rsync dist/ to /opt/aidcp/console; local /intro.html 200 references assets/index-EI7Eq13v.js; public /intro.html 200; browser load redirects to /login and renders login page, no console errors; /api/health 200; ports 8088/8090/8787 listening; PostgreSQL accepting connections; Feishu WSClient onReady; aidcp-cloud active; isales-scheduler/isales-api active. -->
- [x] 3.4 Commit, push, and deploy the console static release if validation passes.
