# Tasks - curated-reference-images

> One Codex session = this OpenSpec change = implementation branches/worktrees of the same name in sibling repos. Record implementation commits with `<!-- <repo> <sha> note -->`.

## 1. Control Repo

- [x] 1.1 Add OpenSpec proposal/design/tasks/spec deltas for curated reference images. <!-- aidcp control: proposal/design/tasks + five spec deltas drafted -->
- [x] 1.2 Validate with `openspec validate curated-reference-images --strict`. <!-- 2026-07-04 strict valid -->
- [x] 1.3 Update `docs/protocol.md` when protocol changes are implemented. <!-- note.detail.images example added to protocol docs -->

## 2. aidcp-edge - Note Image Extraction

- [x] 2.1 Extend `src/comm/protocol.ts` `NoteDetailPayload` with optional ordered `images`.
- [x] 2.2 Extend `src/browse/note-extractor.ts` `NoteContent` and extraction logic for carousel images, with dedup/filter/limit.
- [x] 2.3 Extend `src/browse/browse-session.ts` note detail report to include extracted images.
- [x] 2.4 Add/extend tests for carousel images, duplicate swiper slides, missing images and invalid URL filtering.
- [x] 2.5 Run edge acceptance tests relevant to note extraction, then `npm test` and `npm run typecheck`. <!-- aidcp-edge 5dc3bbe1995b1425143f6530e0dcf30e3f16fa0a; npm test 610 pass / 1 gated skip; npm run typecheck passed -->

## 3. aidcp-cloud - Protocol, Storage, OSS

- [x] 3.1 Sync `src/comm/protocol.ts` and event types/handler mapping for `note.detail.images`.
- [x] 3.2 Extend `src/cache/curated-content-store.ts` with `reference_images JSONB`, DTOs, normalization, `upsertObservation`, `markBotAction`, `selectForCreation`, `listForPanel`, and `getOneForAccount`.
- [x] 3.3 Extend `lastObservedNoteByAccount`, `CuratedNoteEvaluator.admit`, and bot collect auto-admission to carry image snapshots.
- [x] 3.4 Add best-effort OSS relocation helper for curated reference images with honest `stored/url_only/fetch_failed/unsupported` status.
- [x] 3.5 Add cloud tests for DDL, image normalization, upsert/collect merge, OSS success/failure and panel DTOs. <!-- aidcp-cloud 131c0b62b0281900bf0f44322830ffb5702136b8 -->

## 4. aidcp-console - Curated Page UX

- [x] 4.1 Mirror `referenceImages` in `src/types/api.ts`.
- [x] 4.2 Add thumbnail column and detail image strip to `CuratedContentPage`.
- [x] 4.3 Replace image-bearing rewrite popconfirm with a confirm modal that can send `useReferenceImages`.
- [x] 4.4 Add/extend tests for thumbnails, text-only fallback and request body. <!-- aidcp-console 390b4a68e848f5c345b7bfc363c9c5f45505ba34 -->

## 5. aidcp-cloud - Publish Reference Pipeline

- [x] 5.1 Extend `TriggerInput.generateInput.referenceNote` and `PublishScheduler.ReferenceNote` with capped usable image refs.
- [x] 5.2 Extend panel action API body with `useReferenceImages?: boolean`; default true only when usable images exist.
- [x] 5.3 Update `ImageSetPlanner` and `ImagePromptComposer` to incorporate visual reference guidance without changing role ownership.
- [x] 5.4 Extend `ImagePlan` and `ImageProvider.generate` to accept optional reference images.
- [x] 5.5 Implement provider support or explicit unsupported-reference reporting in `WanxiangClient` and `SeedreamClient`. <!-- current Wanxiang/Seedream path explicitly reports unsupported; no direct image reuse -->
- [x] 5.6 Extend `ImageGenerator` audit/result handling so `referenceUsed` / unsupported / unavailable is visible and never silently claimed.
- [x] 5.7 Add focused publish tests for reference-note image plumbing, provider unsupported path, partial image success and no deadlock. <!-- aidcp-cloud 131c0b62b0281900bf0f44322830ffb5702136b8 -->

## 6. Final Validation

- [x] 6.1 cloud: `npm test`, relevant acceptance tests, `npm run typecheck`. <!-- npm run typecheck passed; npm run build passed; npx tsx --test test/**/*.test.ts 1336 pass / 1 gated skip after one flaky heartbeat rerun; npm test script still discovers 0 tests on Windows due quoted glob -->
- [x] 6.2 console: targeted tests, `npm test`, `npm run typecheck`, build. <!-- aidcp-console 390b4a68e848f5c345b7bfc363c9c5f45505ba34; targeted CuratedContentPage 8 pass; full vitest 40 pass / 1 skip; typecheck + build passed; jsdom getComputedStyle warnings are pre-existing non-fatal output -->
- [x] 6.3 control: `openspec validate curated-reference-images --strict`. <!-- 2026-07-05 strict valid after implementation tasks update -->
- [ ] 6.4 If deployment is requested, follow the repo deployment sequence: tests green, backup ECS cloud/env, rsync only intended files, restart `aidcp-cloud.service`, healthcheck service/ports/Feishu/PostgreSQL.
