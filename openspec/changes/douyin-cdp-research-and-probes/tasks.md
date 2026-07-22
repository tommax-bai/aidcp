## 1. Isolated Edge setup and fixtures

- [ ] 1.1 Create `/Users/baitianxing/codes/aidcp-edge.wt/douyin-cdp-research-and-probes` on branch `codex/douyin-cdp-research-and-probes` from the latest `origin/master`, without modifying the canonical Edge checkout.
- [ ] 1.2 Install a physical worktree-local dependency tree with `npm ci --prefer-offline` when needed; do not symlink `node_modules`.
- [ ] 1.3 Add sanitized Douyin fixtures for a logged-out Jingxuan grid, hidden verification iframe, visible verification blocker, access restriction, internal content scroller, target ambiguity, and an authenticated detail surface after it has been observed live.

## 2. Profile ownership and page-state preflight

- [ ] 2.1 Add an independent `src/douyin/probes/` module and types for connection mode, surface, blocker, browse, like, comment, and publishing research results; do not export it through any production command router.
- [ ] 2.2 Implement the AdsPower API connection path with exact requested-profile and start-page marker confirmation.
- [ ] 2.3 Implement the attach-only `DevToolsActivePort` fallback with process user-data-dir and exact marker proof, and ensure this path cannot close the existing browser.
- [ ] 2.4 Implement visible structural classification for access restriction, challenge, unavailable page, login required, and ready states, including the hidden-iframe false-positive guard.
- [ ] 2.5 Add focused tests for exact ownership, mismatched profile refusal, attach-only lifecycle, blocker priority, hidden verification iframe, and logged-out public browsing.

## 3. Surface-aware bounded browsing

- [ ] 3.1 Implement `jingxuan_grid` discovery using de-duplicated `data-aweme-id` values and the unique vertically scrollable container that owns work-card descendants.
- [ ] 3.2 Exclude navigation and horizontal tab scrollers, avoid `window` as an implicit target, and report `surface_ambiguous` when the content container is not unique.
- [ ] 3.3 After user-managed login and read-only inspection, implement the verified `video_detail` identity and advancement adapter without caching DOM nodes across navigation.
- [ ] 3.4 Implement bounded advancement with before/after work-id evidence, `advanced`, `no_change`, `blocked`, and ambiguity results.
- [ ] 3.5 Add tests for grid de-duplication, internal-scroll selection, virtual/reused node re-probing, detail target changes, bounded no-change, and honest browse counts.

## 4. Gated interaction probes

- [ ] 4.1 Implement a default-shadow like probe using `AIDCP_DOUYIN_PROBE_LIKE=1` plus exact `AIDCP_DOUYIN_PROBE_CONFIRM_PROFILE` as mandatory real-action gates.
- [ ] 4.2 Implement unique current-work and like-control discovery, `already_liked` one-way behavior, at-most-one click, same-work post-action confirmation, and `ui_confirmed` versus `ambiguous` evidence.
- [ ] 4.3 Implement a comment fill-only API that rechecks the work id, requires one visible editor, enters text through CDP, and reports only length/match plus `submitted=false`.
- [ ] 4.4 Add static and runtime tests proving the comment path has no send-control lookup, Enter-family dispatch, form submission, submit parameter, or submit environment flag.
- [ ] 4.5 Add tests for missing gates, wrong profile, logged-out state, already-liked state, target/control ambiguity, target change, fill readback failure, and no repeated click.

## 5. Publishing-path research and evidence

- [ ] 5.1 Implement a read-only publisher-surface probe that records only creator/upload route, file-input metadata, editor metadata, blockers, and candidate counts with `uploaded=false` and `submitted=false`.
- [ ] 5.2 Add static tests proving the publishing probe has no file selection, publish-text input, final publish-control lookup, Enter-family dispatch, form submission, or enable-submit flag.
- [ ] 5.3 Document the future official path and prerequisites: approved Douyin Open Platform application, user OAuth, `video.create`, fresh per-operation user approval, `/video/upload/`, `/video/create/`, returned item identity, and official list/data status checks.
- [ ] 5.4 Ensure reports return `official_api_unavailable` or `approval_required` when prerequisites are missing and never describe CDP final submission as a fallback.

## 6. Runner, privacy, and validation

- [ ] 6.1 Add a manual runner that defaults to read-only research, targets one explicit profile, emits bounded JSON evidence, and never reads or prints cookies, storage, tokens, phone numbers, request bodies, comments, or full content text.
- [ ] 6.2 Live-validate the read-only preflight and Jingxuan browse path on `k1evgky5`, including exact ownership, no visible blocker, logged-out classification, stable `data-aweme-id`, internal content scroller, and bounded no-change/advance evidence.
- [ ] 6.3 After the user manually logs into Douyin, live-validate only the read-only detail, like-shadow, comment-editor discovery, and publisher-surface discovery paths; do not enter text, upload a file, or perform an interaction without a new explicit authorization.
- [ ] 6.4 If and only if the user separately authorizes a real like, run it once with both gates and preserve same-work UI evidence; otherwise record the live real-action check as intentionally not run without weakening automated coverage.
- [ ] 6.5 Run the focused Douyin test suite and `npm run typecheck` in the Edge worktree, then run `openspec validate douyin-cdp-research-and-probes --strict` in the control worktree.
- [ ] 6.6 Record repo, commit SHA, validation results, live evidence boundaries, unrun gated actions, and deviations in concise HTML comments in this task file; do not merge, deploy, package, archive, or register production Douyin support without separate authorization.
