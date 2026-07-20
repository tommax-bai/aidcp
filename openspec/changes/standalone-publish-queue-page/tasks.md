## 1. Route and Page Ownership

- [x] 1.1 Register `/publish-queue` as a labelled destination in the Content navigation group and cover route/group activation.
- [x] 1.2 Move queue queries, lifecycle selection, legacy fallback, and rendering into a standalone Publish Queue page.
- [x] 1.3 Remove the queue surface and queue polling from Content page while preserving its candidate filters, detail modal, and approval actions.

## 2. Queue Information Design

- [x] 2.1 Add summary tiles for active drafts, explicit waiting-human drafts, and not-yet-started queued tasks with honest loading/error states.
- [x] 2.2 Present active lifecycle detail, queued work, empty states, and raw diagnostics in a clear responsive page hierarchy.
- [x] 2.3 Add a waiting-human handoff to the Content page without duplicating or guessing candidate approval behavior.

## 3. Validation

- [x] 3.1 Add focused tests for the independent route, Content-page separation, summary counts, lifecycle truth, queued-task filtering, handoff, and legacy fallback.
  <!-- Focused ContentPage + AppShell + route tests: 46/46 passed. -->
- [x] 3.2 Run focused and full console tests, typecheck, production build, and responsive visual verification.
  <!-- aidcp-console: focused ContentPage + current flyout AppShell + route tests 48/48 after rebasing latest master; full Vitest single-worker 34 files, 210 passed, 1 pre-existing skipped; `npm run typecheck` and `npm run build` passed (3724 modules; existing large-chunk warning only). Browser verification passed at 1440x1000 and 390x844: the desktop Content flyout contains Content / Publish Queue / Curated / Schedule, no document overflow, three summary tiles remain bounded, narrow navigation names `内容 · 发布队列`, and the eight-stage strip owns its horizontal overflow. Waiting-human handoff targets `/content?status=pending_approval`, whose pending-only switch was verified checked. -->
- [x] 3.3 Run `openspec validate standalone-publish-queue-page --strict` and record implementation evidence.
  <!-- `openspec validate standalone-publish-queue-page --strict` passed on 2026-07-20. -->

## 4. Integration and Development Deployment

- [x] 4.1 Commit the console implementation, rebase and fast-forward it onto the latest `aidcp-console` default branch, and push without force.
  <!-- aidcp-console `b9b5879280f27dd33a6ebb5f24b8ae14c708ea99`; rebased onto `d18337c`, resolved the concurrent grouped-navigation test against the current flyout model, fast-forwarded canonical master, and pushed `master` without force. -->
- [x] 4.2 Commit and push the OpenSpec artifacts with console commit, validation, deployment, and deviation evidence.
  <!-- Control artifacts commit `6a34eae49ef855ce6252cd8a801b48a2e23bc10c` was fast-forwarded to canonical main and pushed. This follow-up evidence update records the completed console commit, validation, browser checks, dev backup, deployed assets, and health results. -->
- [x] 4.3 Deploy rebuilt console assets from the clean default checkout to `dev`, then verify HTTP health and the served publish-queue route/assets.
  <!-- Target `dev` passed `scripts/deploy-target dev --check`. Backup: `/opt/aidcp/console.bak.20260720-150228.tar.gz`. Deployed clean canonical `aidcp-console/master` commit `b9b5879` assets `index-MfdeLsKa.js` + `index-D0qPl7t5.css`; remote JS contains `/publish-queue` and `发布队列`. `aidcp-cloud.service` remained active with `NRestarts=0`; 8787/8088/8090 were listening; panel health returned `{"ok":true}`; `/`, `/content`, `/publish-queue`, and proxied `/api/health` returned HTTP 200. Public dev route and both assets also returned HTTP 200. No service restart or unrelated service change. -->
