## 1. OpenSpec

- [x] 1.1 Create proposal, design, and spec deltas for complete curated reference image capture.
- [x] 1.2 Validate the change with `openspec validate complete-curated-reference-image-capture --strict`.
<!-- aidcp control repo: OpenSpec artifacts created; validation passed with `openspec validate complete-curated-reference-image-capture --strict` on 2026-07-05. -->

## 2. Cloud

- [x] 2.1 Raise curated reference image default limit to 9 while preserving hard cap and empty-refresh preservation.
<!-- aidcp-cloud b25fcb6: default curated reference image limit raised to 9; added refreshReferenceImages() that no-ops on empty snapshots and keeps the hard cap/normalization path. -->
- [x] 2.2 Add/update cloud tests proving the default stores 9 images and still caps overflow.
<!-- aidcp-cloud b25fcb6: curated-content-store tests cover default 9-image retention and refreshReferenceImages empty-input no-op/update behavior; existing cap test remains. -->
- [x] 2.3 Add protocol support for refresh-only note details so image refreshes do not increment view counts.
<!-- aidcp-cloud b25fcb6: NoteDetailPayload.refreshOnly and note.image_snapshot.arrived split refresh snapshots from normal note.detail/view counting; handler test proves no view event. -->

## 3. Edge

- [x] 3.1 Re-extract note content after successful `note.browse_images` and report updated images with a refresh-only marker.
<!-- aidcp-edge 223ca96: browse_images success re-runs noteExtractor and reports refreshOnly note.detail with the current observed carousel images. -->
- [x] 3.2 Add/update edge tests for post-browse image snapshot reporting and no-report on failed browse.
<!-- aidcp-edge 223ca96: browse-session tests assert refreshOnly image snapshot after successful carousel browsing and no fabricated snapshot on no_target. -->

## 4. Validation

- [x] 4.1 Run focused cloud tests for curated content store and protocol handler behavior.
<!-- 2026-07-05: focused cloud tests passed via `npx tsx --test test/cache/curated-content-store.test.ts test/handler-attribution.test.ts test/agents/curated-note-evaluator.test.ts`. -->
- [x] 4.2 Run focused edge browse/note extraction tests.
<!-- 2026-07-05: edge browse/note extraction coverage passed via full `npm test`; relevant tests include browse-session note.browse_images and note-extractor image extraction. -->
- [x] 4.3 Run required repo-level typecheck/tests for touched cloud and edge code.
<!-- 2026-07-05: `openspec validate complete-curated-reference-image-capture --strict` passed; aidcp-cloud `npm run typecheck` and `npm test` passed (1365 tests); aidcp-edge `npm run typecheck` and `npm test` passed (615 tests). aidcp-console `npm test` passed (50 pass, 1 skipped) and `npm run build` passed for desktop-download release. -->

## 5. Closeout

- [x] 5.1 Commit and push sibling repo changes on their default branches after validation.
<!-- pushed: aidcp-cloud b25fcb6 on master; aidcp-edge 223ca96 runtime fix and b1c35d3 version 0.2.4 on master; aidcp-console 0fe7260 download config on master. -->
- [x] 5.2 Update this tasks file with commits, validation notes, and deployment/publish notes.
<!-- deployment: aidcp-cloud b25fcb6 deployed to ECS 121.89.85.150 on 2026-07-05 17:47 CST from committed snapshot; backups /opt/aidcp/backups/aidcp-cloud-20260705-174712.tgz and .env; health active, :8787/:8090 listening, /api/health ok, /api/version ok, PG select 1 ok, Feishu WSClient onReady, refreshOnly code anchors verified, isales-scheduler/isales-api active. -->
<!-- publish: aidcp-edge 0.2.4 built by GitHub Actions run 28736743911; uploaded /opt/aidcp/downloads/AIDCP Setup 0.2.4.exe sha256 a08afe44a7bf41525dfa5c7ca060a4617c628c4ec21e78877c80f20cd87a546e, AIDCP-0.2.4-arm64.dmg sha256 958bcb8fd32e281d5d1507c6240643207cbdd7522d75d0705925708a6abbfd3f, AIDCP-0.2.4.dmg sha256 37e2268b2bcfa4ad07027c4fe850442fc9d6f7b7f3f9b88ecbc7da8abc4ab8da. -->
<!-- deployment: aidcp-console 0fe7260 deployed static bundle assets/index-07YYan57.js to ECS on 2026-07-05 17:58 CST; backup /opt/aidcp/backups/aidcp-console-20260705-175839.tgz; / 200, /api/health 200, bundle contains 0.2.4, three /downloads URLs returned 200 with expected content-length, aidcp-cloud and isales services active. -->
