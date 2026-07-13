## Context

The Facebook publish media upload UI currently accepts image files and sends each one as Base64 JSON to the existing panel API. Operators may upload phone or WeChat originals that are several megabytes and thousands of pixels on the long edge. Facebook can accept those files, but the later browser-side Facebook composer often spends a long time uploading and transcoding them, leaving the operator-facing UI stuck on "posting".

This change is intentionally frontend-only. The cloud API, stored media model, publish command protocol, and edge browser execution remain unchanged.

## Goals / Non-Goals

**Goals:**

- Convert admin-uploaded Facebook publish images to compressed JPEG before they enter the media pool.
- Preserve the full image content: no crop, no stretch, no aspect-ratio change.
- Keep operator feedback honest by showing compressed size when compression happens.
- Reject files that cannot be converted to a smaller JPEG before upload, so the media pool does not keep oversized originals.

**Non-Goals:**

- No server-side image processing pipeline in this change.
- No change to existing 10MB upload hard limit.
- No change to generated publish images, curated reference images, or edge `upload_image`.
- No preservation of animation or alpha channels; this upload path produces static JPEG publish素材.

## Decisions

1. **Compress in the console browser before upload.**

   This keeps CPU cost on the operator machine, reduces API payload size, and avoids adding ECS image-processing dependencies. Alternative considered: server-side `sharp`; rejected for this narrow upload path because it adds deployment/runtime cost and does not reduce the panel upload request size.

2. **Use 600KB as the target size, not a skip threshold.**

   Every accepted upload is decoded, rendered to canvas, and encoded as JPEG. The encoder tries bounded quality and size candidates to get near or below 600KB. If no JPEG candidate is smaller than the source, the file is rejected rather than uploaded as an oversized original.

3. **Use bounded, aspect-preserving canvas compression with JPEG output.**

   All accepted inputs use the same output type: `image/jpeg`. Transparent pixels are composited onto a white background because JPEG has no alpha channel. The implementation never crops, never pads, and never changes aspect ratio.

4. **Reject conversion failures instead of falling back to originals.**

   The old conservative fallback kept uploads flowing but allowed PNG originals to remain large. The new rule treats decode/encode/no-smaller-candidate as a local validation failure and leaves the file out of the queue.

## Risks / Trade-offs

- Browser canvas APIs can fail for unusual images → show a validation error and require another file/export.
- Compression may not reach 600KB for every large image → upload the smallest smaller JPEG candidate; reject only when no smaller JPEG exists.
- PNG transparency is flattened to white → acceptable for Facebook post素材, but not suitable for workflows that require alpha preservation.
- Client-side compression adds a short wait before the file appears in the pending queue → the queue label will show the resulting size so the wait is explainable.
