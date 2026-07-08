# Design - curated-reference-images

## 1. Design Position

This change adds visual reference support to curated-note rewrite creation. It keeps the existing architecture split:

- Edge extracts observable page facts and performs browser actions.
- Cloud owns persistence, orchestration, model calls, risk posture and publish pipeline.
- Console exposes operator controls and review surfaces.

The new capability must preserve three existing red lines:

- Do not silently fake success.
- Do not directly reuse third-party original images as publish images.
- Do not collapse publish image decisions and image generation execution into one role.

## 2. Current State

- Edge `NoteDetailPayload` contains `noteId/title/content/author/likeCount/collectCount/url`, but no image data.
- Edge can browse image carousel pages through `note.browse_images`, but this is only a behavior action and reports only `browsed=N`.
- Cloud `curated_content` stores text, counts, source URL, topics and bot action marks; no image field exists.
- Console `PanelCuratedContent` mirrors the cloud row shape and has no image field.
- Manual rewrite passes a text-only `referenceNote` into `PublishScheduler.triggerManual`.
- `ImageProvider.generate(prompt)` is text-only in the current code abstraction.

## 3. Data Model

Add an optional image snapshot to note rows:

```ts
export interface CuratedReferenceImage {
  index: number;
  sourceUrl?: string;
  ossUrl?: string;
  width?: number;
  height?: number;
  alt?: string;
  captureStatus: 'stored' | 'url_only' | 'fetch_failed' | 'unsupported';
  capturedAt: number;
}
```

DDL:

```sql
ALTER TABLE curated_content
  ADD COLUMN IF NOT EXISTS reference_images JSONB NOT NULL DEFAULT '[]'::jsonb;
```

Why JSONB instead of a child table for the first version:

- Each note only needs a small ordered list.
- Console and publish paths read the row as a whole.
- Existing curated store is self-initializing and already has row-level retention.

Hard limits:

- Store only for `content_type='note'`.
- Keep at most `AIDCP_CURATED_REFERENCE_IMAGE_LIMIT` images per row, hard cap 30 (raised from 9 by change raise-curated-scrape-image-cap; decoupled from the publish-side ≤9 platform limit).
- Empty or invalid arrays become `[]`.
- Existing retention deletes DB rows; object cleanup can be a follow-up sweeper if storage growth becomes material.

## 4. Edge Extraction

Extend `NoteContent` and `NoteDetailPayload` with:

```ts
images?: Array<{
  index: number;
  url: string;
  width?: number;
  height?: number;
  alt?: string;
}>;
```

Extraction rules:

- Scope to the note detail container, not the whole document.
- Prefer real carousel slides: `.swiper-slide:not(.swiper-slide-duplicate) img`.
- Fallback to existing image selectors used by the image browsing probe: `.note-slider-img`, `[class*="media"] img`.
- Prefer `currentSrc`, then `src`, then best candidate from `srcset`, then `data-src`.
- Exclude `blob:`, `data:`, empty strings, avatar images, emoji and duplicate URLs.
- Preserve visual order by DOM order.
- If no images are found, report `images: []` or omit the field. Do not fail the note detail report.

Open point for implementation:

- If real XHS image URLs cannot be fetched by cloud because of anti-hotlinking, add a later command where edge captures current carousel image bytes or screenshot and uploads them through cloud. That is deliberately not MVP because it makes edge heavier.

## 5. Cloud Ingestion and Storage

Cloud receives `note.detail.images` and normalizes it into `CuratedReferenceImage[]`.

Storage paths:

- Model-admitted curated notes: `CuratedNoteEvaluator.admit` passes image refs to `upsertObservation`.
- Bot collect auto-admission: `lastObservedNoteByAccount` keeps the latest note images, then `markBotAction('collect')` can create/update a curated row with them.
- Existing rows: `upsertObservation` replaces image snapshot with the latest normalized snapshot; `markBotAction` only fills images when the row is created or when current row has none, so a bot action does not erase already stored images.

OSS stabilization:

- A cloud helper attempts to fetch each `sourceUrl`, validates it as an image by content-type/magic bytes, and uploads to OSS under `curated/<accountId>/<sourceId>/<index>`.
- On success: write `captureStatus='stored'`, `ossUrl=<stable URL>`.
- On fetch/upload failure: write `captureStatus='fetch_failed'` and keep `sourceUrl` for operator visibility.
- If no object store is configured: write `captureStatus='url_only'`; do not block curated admission.

This mirrors generated-image OSS semantics: failure reduces availability but must not create fake URLs.

## 6. Console UX

List:

- Add a compact thumbnail column for note rows.
- Show first usable image: `ossUrl ?? sourceUrl`.
- If no image, show an unobtrusive empty state.

Detail modal:

- Show ordered image strip above or below body.
- Each image opens the stored/source URL in a new tab with `noopener`.
- Show capture status in secondary text for debugging.

Rewrite trigger:

- Replace the single popconfirm with a small confirm modal when images exist.
- Default option: `带图参考`.
- Secondary option: `仅文本参照`.
- Disable image reference automatically when no usable `ossUrl/sourceUrl` exists.
- The HTTP body adds `useReferenceImages?: boolean`, default true when images exist.

## 7. Publish Pipeline Wiring

Extend `TriggerInput.generateInput.referenceNote`:

```ts
referenceNote?: {
  sourceId: string;
  title: string;
  body: string;
  topics: string[];
  author?: string;
  images?: CuratedReferenceImage[];
}
```

Scheduler:

- Keep the existing empty body guard unchanged.
- Truncate body as today.
- Limit image refs to usable URLs and to the configured max.
- Preserve account isolation because the row is read by `getOneForAccount`.

Image roles:

- `ImageSetPlanner` still watches `createdContent`, but can read `trigger.generateInput.referenceNote.images` from the context snapshot.
- It should prefer an image count and theme rhythm compatible with the reference set when present, while still serving the newly written content.
- `ImagePromptComposer` adds visual-reference instructions into prompts: borrow composition, color mood, visual hierarchy and sequencing; do not copy exact text, watermark, people, logo, product identity or layout pixel-for-pixel.
- `ImagePlan` carries `referenceImages` or per-image references to `ImageGenerator`.
- `ImageGenerator` is still the only role that calls image providers.

Provider contract:

```ts
export interface ImageGenerateOptions {
  referenceImages?: string[];
  referenceMode?: 'style' | 'composition' | 'storyboard';
}

export interface ImageProvider {
  generate(prompt: string, options?: ImageGenerateOptions): Promise<ImageResult>;
}
```

Provider behavior:

- Provider supports reference images: call the provider's image-reference or image-edit endpoint with URLs/base64 as required.
- Provider does not support reference images: return a structured unsupported result, or generate prompt-only with an explicit `referenceUsed:false` result. The pipeline must record and surface this; it must not claim image reference was used.
- Per-image timeout and partial success semantics remain unchanged.

## 8. Approval and Audit

Approval cards should show:

- Generated image thumbnails as today.
- A small note that this was a reference-image rewrite when applicable.
- Whether reference images were actually used, skipped, unsupported or unavailable.

Publish log can keep the final generated images as today. If audit detail is needed, add metadata under existing `publish_metadata`, not new top-level columns:

```json
{
  "referenceNote": {
    "sourceId": "...",
    "imageCount": 3,
    "imageReferenceUsed": true,
    "imageReferenceStatus": "used|unsupported|unavailable|skipped"
  }
}
```

## 9. Testing Strategy

Edge:

- Unit test image extraction from carousel, duplicate slides, missing images, data/blob filtering.
- Protocol type test for `NoteDetailPayload.images`.

Cloud:

- Curated store DDL adds `reference_images` without breaking existing DB.
- `upsertObservation` stores normalized images.
- `markBotAction('collect')` creates row with images and does not erase existing images.
- OSS relocation success/failure/status cases.
- Panel list/getOne returns image refs.
- `create-post` rejects non-note/empty-body as before and passes image refs only when requested.

Publish:

- Scheduler carries `referenceNote.images`.
- Image roles keep unique output keys and do not deadlock.
- Provider unsupported reference path is visible and does not claim success.
- ImageGenerator partial success semantics remain: failed reference generation drops that generated image, not the whole set.

Console:

- Thumbnail renders when images exist.
- Detail modal shows ordered images.
- Rewrite confirm sends `useReferenceImages` correctly.
- Empty/no-image rows still behave as text-only rewrite.

Validation:

- `openspec validate curated-reference-images --strict`.
- edge: acceptance tests relevant to note extraction, then `npm test`, `npm run typecheck`.
- cloud: focused unit tests, then `npm test`, acceptance if protocol/publish touched, `npm run typecheck`.
- console: targeted tests, `npm run typecheck`, `npm test` and build if UI touched.

## 10. Rollout

Recommended implementation order:

1. Protocol and extraction behind optional field, all consumers tolerate missing images.
2. Curated storage and panel display.
3. Manual rewrite passes images but image pipeline still text-only if provider work is not ready.
4. Provider reference support and publish audit.
5. Production deploy after all sibling repo tests and OpenSpec validation pass.

This allows a safe intermediate state: images can be collected and inspected before they affect generated posts.
