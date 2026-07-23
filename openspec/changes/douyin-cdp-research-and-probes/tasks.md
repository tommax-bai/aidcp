## 1. Isolated Edge setup and fixtures

- [x] 1.1 Create `/Users/baitianxing/codes/aidcp-edge.wt/douyin-cdp-research-and-probes` on branch `codex/douyin-cdp-research-and-probes` from the latest `origin/master`, without modifying the canonical Edge checkout.
- [x] 1.2 Install a physical worktree-local dependency tree with `npm ci --prefer-offline` when needed; do not symlink `node_modules`.
- [ ] 1.3 Add sanitized Douyin fixtures for a logged-out Jingxuan grid, hidden verification iframe, visible verification blocker, access restriction, internal content scroller, target ambiguity, and an authenticated detail surface after it has been observed live.

## 2. Profile ownership and page-state preflight

- [ ] 2.1 Add an independent `src/douyin/probes/` module and types for connection mode, surface, blocker, browse, like, comment, and publishing research results; do not export it through any production command router.
- [x] 2.2 Implement the AdsPower API connection path with exact requested-profile and start-page marker confirmation.
- [ ] 2.3 Implement the attach-only `DevToolsActivePort` fallback with process user-data-dir and exact marker proof, and ensure this path cannot close the existing browser.
- [x] 2.4 Implement visible structural classification for access restriction, challenge, unavailable page, login required, and ready states, including the hidden-iframe false-positive guard.
- [ ] 2.5 Add focused tests for exact ownership, mismatched profile refusal, attach-only lifecycle, blocker priority, hidden verification iframe, and logged-out public browsing.

## 3. Surface-aware bounded browsing

- [ ] 3.1 Implement `jingxuan_grid` discovery using de-duplicated `data-aweme-id` values and the unique vertically scrollable container that owns work-card descendants.
- [ ] 3.2 Exclude navigation and horizontal tab scrollers, avoid `window` as an implicit target, and report `surface_ambiguous` when the content container is not unique.
- [x] 3.3 Implement `video_detail_modal` by sending a trusted pointer event to the unique visible card cover, matching the resulting `modal_id` to the source `data-aweme-id`, and requiring active-feed/modal-ready structures; report `page_not_hydrated` for URL-only skeletons.
- [ ] 3.4 Implement bounded advancement with before/after work-id evidence, `advanced`, `no_change`, `blocked`, and ambiguity results.
- [ ] 3.5 Add tests for grid de-duplication, internal-scroll selection, virtual/reused node re-probing, detail target changes, bounded no-change, and honest browse counts.

## 4. Gated interaction probes

- [x] 4.1 Implement a default-shadow like probe using `AIDCP_DOUYIN_PROBE_LIKE=1` plus exact `AIDCP_DOUYIN_PROBE_CONFIRM_PROFILE` as mandatory real-action gates.
- [x] 4.2 Implement unique current-work and `video-player-digg` discovery, but keep real clicking disabled with `state_unknown` until sanitized positive and negative liked-state fixtures prove a stable state mapping; then add `already_active`, at-most-one click, same-work confirmation, and `ui_confirmed` versus `postcondition_unknown` evidence.
- [ ] 4.3 Implement a comment fill-only API that rechecks the work id, requires one visible work-bound comment editor, explicitly excludes the `发一条弹幕吧` danmaku input, enters text through CDP, and reports only length/match plus `submitted=false`.
- [ ] 4.4 Add static and runtime tests proving the comment path has no send-control lookup, Enter-family dispatch, form submission, submit parameter, or submit environment flag.
- [ ] 4.5 Add tests for missing gates, wrong profile, logged-out state, already-liked state, target/control ambiguity, target change, fill readback failure, and no repeated click.

## 5. Gated follow, collection, messaging, and live probes

- [x] 5.1 Implement independent default-shadow follow and collection probes with exact profile confirmation, single-action budgets, one-way already-done behavior, stable modal identity, and post-action UI confirmation.
- [x] 5.2 Add validated follow and collection state fixtures; keep either real action disabled with `state_unreadable` until its positive and negative mapping is proven.
- [x] 5.3 Implement a single-conversation private-message reply probe gated by `AIDCP_DOUYIN_PROBE_DM_REPLY=1`, exact profile confirmation, proven one-to-one type, proven inbound direction, and the exact allowlist `好的`/`ok`, without reporting identities or message bodies.
- [x] 5.4 Implement separate live ordinary-chat and comment-targeted reply probes with independent gates, exact texts `1111` and `666`, one-room/one-action budgets, and no fallback from targeted reply to ordinary chat.
- [x] 5.5 Add focused tests for missing/mismatched gates, invalid texts, already-followed/collected states, unreadable action state, ambiguous/inbound-unconfirmed DM targets, live target ambiguity, single-submit budgets, and redacted reports.
- [x] 5.6 Add an exact-match `我知道了` interaction-prompt dismissal with post-dismissal target hit-testing, and test that ambiguous or persistent overlays block social actions.
- [x] 5.7 Add sanitized known-group and known-private fixtures that prove group-specific structures, private direction classification, and zero input/submit for group or unknown conversation types.

## 6. Publishing-path research and evidence

- [ ] 6.1 Implement a read-only publisher-surface probe for `creator.douyin.com/creator-micro/content/upload` that records the single-file video input metadata, the absence of a pre-upload editor, blockers, and candidate counts with `uploaded=false` and `submitted=false`.
- [ ] 6.2 Add static tests proving the publishing probe has no file selection, publish-text input, final publish-control lookup, Enter-family dispatch, form submission, or enable-submit flag.
- [x] 6.3 Document the future official path and prerequisites: approved Douyin Open Platform application, user OAuth, `video.create`, fresh per-operation user approval, `/video/upload/`, `/video/create/`, returned item identity, and official list/data status checks.
- [ ] 6.4 Ensure reports return `official_api_unavailable` or `approval_required` when prerequisites are missing and never describe CDP final submission as a fallback.

## 7. Runner, privacy, and validation

- [x] 7.1 Add manual runners that default to read-only research, target one explicit profile, emit bounded JSON evidence, and never print cookies, storage, tokens, phone numbers, identities, message/comment bodies, or full content text.
- [ ] 7.2 Live-validate the read-only preflight and Jingxuan browse path on `k1evgky5`, including exact ownership, no visible blocker, logged-out classification, stable `data-aweme-id`, internal content scroller, and bounded no-change/advance evidence.
- [x] 7.3 After the user manually logs into Douyin, live-validate the trusted-click `modal_id` detail path, unique like-shadow control, comment-versus-danmaku discrimination, creator upload landing page, and shadow follow/collection/DM/live discovery paths.
- [ ] 7.4 With the user's explicit authorization, run at most one follow, one collection, one private DM reply `好的`, one live ordinary chat `1111`, and one comment-targeted live reply `666`; preserve honest UI evidence and report unavailable/ambiguous actions without substitution.
- [x] 7.5 Keep ordinary work-comment submission, file selection, and final publishing unrun unless separately authorized; record these as intentionally not run without weakening automated coverage.
- [x] 7.6 Run the focused Douyin test suite and `npm run typecheck` in the Edge worktree, then run `openspec validate douyin-cdp-research-and-probes --strict` in the control worktree.
- [x] 7.7 Record repo, commit SHA, validation results, live evidence boundaries, unrun gated actions, and deviations in concise HTML comments in this task file; do not merge, deploy, package, archive, or register production Douyin support without separate authorization.
- [x] 7.8 With the user's explicit authorization, run at most one real like on `k1evgky5`; require a proven unliked pre-state, exact profile gate, same-modal post-state, and no retry after any ambiguous dispatch.

<!-- Implementation evidence (2026-07-22): aidcp-edge commits 11022ec and 49aeb4e on codex/douyin-cdp-research-and-probes; 21/21 focused tests passed; npm run typecheck passed. Research summary: docs/research/douyin-web-cdp-research-2026-07-23.md. The worktree uses a physical npm ci --prefer-offline dependency tree. No production router, deployment, package, merge, or archive was performed. -->
<!-- Live evidence correction: exact profile k1evgky5 and its start-page marker were confirmed. One follow and one collection reached same-modal positive UI states; one live chat 1111 was submitted, its editor cleared, and one exact message node was read back. The earlier allowlisted DM reply of length 2 cleared its editor but was later identified by the user as a group conversation, so it is a misclassification deviation rather than valid private-DM evidence. The page exposed no unique comment-bound live reply control, so 666 was not sent and ordinary chat was not used as a substitute. -->
<!-- One-time like evidence: the independently gated runner confirmed a unique unliked heart fixture and hit-ready control on modal 7651537512803945743, then dispatched exactly one click. Its original state mapping returned postcondition_unknown and did not retry. A subsequent read-only check on the same modal found the exact video-player-is-digged state and red 90x94 animation; the corrected mapping reports active/digged_state, with sanitized positive/negative fixture coverage. -->
<!-- Intentional exclusions: ordinary work-comment submission, file selection, upload, draft creation, and final publishing were not run. Initial pointer attempts were intercepted by a first-use overlay and produced no state change; after the user identified it, the exact visible 我知道了 button was dismissed and target hit-testing was added. Unchecked tasks remain open for the broader browse, comment-fill, publishing-surface, and automatic DevToolsActivePort research scope. -->
