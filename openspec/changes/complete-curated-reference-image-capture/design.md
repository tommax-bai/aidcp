## Context

The existing curated reference image pipeline is functionally wired, but its capture is incomplete in two places:

- Edge extracts `note.detail.images` immediately after opening a note. `note.browse_images` later clicks through the carousel but only reports `browsed=N`, so lazy-loaded images discovered during browsing are not persisted.
- Cloud normalizes curated reference images with default limit 3 even though edge and console already tolerate up to 9, the platform graph/image-text cap.

Production currently shows 80 `image_text` curated rows, only 3 with images, and the maximum stored count is 3. This points to storage truncation plus open-time-only DOM capture, not a console display issue.

## Goals / Non-Goals

**Goals:**

- Preserve up to 9 curated reference images per image-text note.
- Refresh image snapshots after edge finishes browsing note carousel images.
- Keep existing account isolation, honest empty/failed states, duplicate filtering, and no-direct-reuse publish red line.
- Keep old cloud/edge compatibility because `images` remains optional.

**Non-Goals:**

- Do not backfill historical rows automatically.
- Do not add byte/screenshot upload from edge.
- Do not directly publish third-party original images.
- Do not change console API shape or publish provider behavior.

## Decisions

1. Use a second `note.detail` report after successful `note.browse_images`.

   Rationale: the existing cloud ingestion path already updates `lastObservedNoteByAccount` and curated admission with `detail.images`; reusing it avoids a new protocol event. The edge report must preserve the current note identity and existing extracted fields so cloud consumers can treat it as a fresher detail snapshot.

   Alternative considered: add `note.images` or `note.image_snapshot`. That would avoid another view event, but requires new cloud handler/event wiring and panel/store plumbing. For this small fix, the existing optional field path is enough.

2. Emit the post-browse detail report only after a successful carousel browse.

   Rationale: failed `browse_images` (`no_target`, click failure) should not create noise or wipe previous images. Existing store logic already preserves non-empty images when the incoming snapshot is empty, but avoiding unnecessary reports keeps downstream view/accounting effects smaller.

3. Raise curated reference image default limit to 9.

   Rationale: edge extraction hard cap and console preview cap are already 9. A cloud default of 3 is the only layer truncating otherwise usable snapshots. Keeping the hard cap at 9 preserves bounded storage.

4. Keep empty snapshot preservation unchanged.

   Rationale: current `upsertObservation` keeps existing `reference_images` when the incoming normalized snapshot is empty, and `markBotAction` only fills images when existing images are empty. This is the correct anti-regression behavior for failed/lazy loads.

## Risks / Trade-offs

- [Duplicate view accounting from reusing `note.detail`] -> `note.detail` currently increments view on every report. Implementation should avoid duplicate view inflation by marking image refresh reports, or the cloud handler should ignore refresh-only reports for view counting.
- [Stale text fields in post-browse report] -> Re-extract the full note content at refresh time rather than sending images-only payloads, so cloud row updates remain coherent.
- [DOM still only exposes current/neighbor images] -> Browsing should force lazy-loaded slides into DOM on most XHS layouts, but it is still best-effort. The system remains honest: unavailable images are not fabricated.
- [More OSS work per curated row] -> Limit remains capped at 9 and only curated/admitted rows relocate images.

## Migration Plan

1. Add optional protocol marker for image snapshot refresh if needed to avoid duplicate view accounting.
2. Update edge to re-extract and report after successful `browse_images`.
3. Raise cloud default limit to 9 and update tests.
4. Validate with focused edge/cloud tests and `openspec validate`.
5. Deploy cloud and edge through the normal default-branch release path when ready; existing rows require re-observation to populate additional images.
