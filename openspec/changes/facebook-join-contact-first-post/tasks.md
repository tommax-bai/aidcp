## 1. Isolated Development Setup

- [x] 1.1 Create matching `codex/facebook-join-contact-first-post` worktrees for `aidcp-edge`, `aidcp-cloud`, and `aidcp-console`, preserving canonical checkouts and unrelated changes
- [x] 1.2 Install physical worktree-local dependencies with `npm ci --prefer-offline`
  <!-- 2026-07-27: Edge/Cloud used npm ci --prefer-offline. Console has no package-lock.json, so npm ci is structurally unavailable; used npm install --prefer-offline --no-package-lock to keep dependencies physical without creating an unrelated lockfile. -->

## 2. Edge First-Post and Target-Bound Read

- [x] 2.1 Extend the synchronized Edge/Cloud `note.open` payload contract with the optional Facebook first-commentable-group-post selection and container fields
- [x] 2.2 Implement bounded group-feed first-post selection in `FacebookCommentExecutor` without search or fallback to a later/different targeting mode
- [x] 2.3 Bind Facebook post text, discussion sample, and editor readiness to the requested canonical post identity and fail honestly on target-context mismatch
- [x] 2.4 Route Facebook `note.open` first-post requests through the handler and return the selected permalink as `note.detail.noteId`
- [x] 2.5 Add Edge unit/contract tests for first-post selection, no-candidate failure, handler routing, and background-feed context exclusion

## 3. Cloud Routing and Scheduled Join-Contact

- [x] 3.1 Treat empty Facebook keywords as a valid generated-comment configuration while keeping template-without-template fail-closed
- [x] 3.2 Add a Cloud Edge step that requests first-post open through `note.open` and validates the returned canonical permalink
- [x] 3.3 Route Facebook comment runs to search when keywords exist and directly to first-post open when they do not, preserving dedupe, approval, validation, audit, and no cross-mode fallback
- [x] 3.4 Make Facebook scheduled `contact_comment` pass `joinFirst=true` with automatic priority and configured approval, while preserving non-Facebook behavior and standalone join-only wiring
- [x] 3.5 Update generated-comment prompts so empty-keyword mode is grounded in post/discussion context without an empty or fabricated keyword instruction
- [x] 3.6 Add Cloud tests for both targeting branches, scheduled join-contact options, standalone join isolation, and prompt/config behavior

## 4. Console and User-Facing Copy

- [x] 4.1 Render Facebook `contact_comment` as “加群评论（联系）” in the automation page while keeping non-Facebook labels compatible
- [x] 4.2 Allow clearing all Facebook comment keywords without an empty-keyword warning or a “当前使用群内首帖” status indicator
- [x] 4.3 Update Facebook scheduled notification copy and add/update Console/Cloud copy tests

## 5. Contract and Validation

- [x] 5.1 Document the extended `note.open` payload and first-post semantics in `docs/protocol.md`
- [x] 5.2 Run focused Edge Facebook executor/handler/protocol tests, full Edge tests required for a protocol/comment change, and Edge typecheck
  <!-- 2026-07-27: focused 114/114 passed; npm test 2455 passed, 1 gated skip; npm run typecheck passed. -->
- [x] 5.3 Run focused Cloud comment scheduler/content scheduler/config/prompt/protocol tests, full Cloud tests required for a protocol/comment change, and Cloud typecheck
  <!-- 2026-07-27: focused 197/197 passed; module-boundary focused 14/14 passed; npm test 3683 passed, 11 gated skips; npm run typecheck passed. -->
- [x] 5.4 Run focused Console tests and Console typecheck/build validation
  <!-- 2026-07-27: focused 29/29 passed; full suite 277 passed, 1 enum snapshot skip; typecheck and production build passed. An earlier concurrent three-repo run hit unrelated 5s UI-test timeouts; isolated full rerun passed. -->
- [x] 5.5 Run `openspec validate facebook-join-contact-first-post --strict` and record validation evidence/deviations in this task file
  <!-- 2026-07-27: openspec validate facebook-join-contact-first-post --strict passed; openspec status reports 4/4 artifacts complete. -->

## 6. Integration and DEV Delivery

- [x] 6.1 Commit explicit scoped changes in each owning repository and the control repository with validation evidence
  <!-- Owner commits: Edge 20e1a09, Cloud 6a6c5e5, Console 9896919. Control evidence is committed by the commit containing this task record. -->
- [x] 6.2 Rebase each feature branch on the latest default branch, rerun required validation, and fast-forward integrate/push serially
  <!-- 2026-07-27: all three branches were already based on current origin/master; pushed serially and canonical master checkouts fast-forwarded cleanly. -->
- [x] 6.3 Run DEV deployment preflight, deploy eligible Cloud runtime changes from the clean default checkout, and verify service/listener/health/log evidence
  <!-- 2026-07-27 DEV only: deploy-target check passed; backups cloud.bak.20260727-211223.tar.gz, cloud/.env.bak.20260727-211223, console.bak.20260727-211223.tar.gz. Eight Cloud runtime files and the built Console were hash-verified. Migration status: content/automation/api pending=0. Stop→start only aidcp-cloud.service; active, NRestarts=0, 8787/8090/8091 listening, panel/client health ok, PostgreSQL ready, schema gates passed in enforce mode, automation writer lock held, Feishu WS onReady, public DEV console served the new asset, isales-api remained active. -->
- [x] 6.4 Record final repo SHAs, deployment boundary, and real-account acceptance status; do not package Edge or touch OL
  <!-- Final source SHAs: Edge 20e1a09, Cloud 6a6c5e5, Console 9896919. Cloud/Console deployed to DEV; OL untouched; no Edge installer/package built. Read-only Tianxing Bai probe established stable first-post permalink/content and exposed the background-post context bug fixed here. Post-change real-account comment submission was intentionally not run because the installed Edge was not repackaged and a platform write requires explicit pre-submit confirmation. -->
