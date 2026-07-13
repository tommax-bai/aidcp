## Context

The Facebook publish media upload UI currently accepts image files and sends each one as Base64 JSON to the existing panel API. Operators may upload phone or WeChat originals that are several megabytes and thousands of pixels on the long edge. Facebook can accept those files, but the later browser-side Facebook composer often spends a long time uploading and transcoding them, leaving the operator-facing UI stuck on "posting".

This change is intentionally frontend-only. The cloud API, stored media model, publish command protocol, and edge browser execution remain unchanged.

## Goals / Non-Goals

**Goals:**

- Compress large admin-uploaded Facebook publish images before they enter the media pool.
- Skip compression for files at or below 600KB to avoid unnecessary quality loss.
- Preserve the full image content: no crop, no stretch, no aspect-ratio change.
- Keep operator feedback honest by showing compressed size when compression happens.
- Keep upload failure semantics unchanged: per-file failures remain retryable.

**Non-Goals:**

- No server-side image processing pipeline in this change.
- No change to existing 10MB upload hard limit.
- No change to generated publish images, curated reference images, or edge `upload_image`.
- No unsafe GIF compression that would silently drop animation frames.

## Decisions

1. **Compress in the console browser before upload.**

   This keeps CPU cost on the operator machine, reduces API payload size, and avoids adding ECS image-processing dependencies. Alternative considered: server-side `sharp`; rejected for this narrow upload path because it adds deployment/runtime cost and does not reduce the panel upload request size.

2. **Use 600KB as a skip threshold, not a hard output guarantee.**

   Files at or below 600KB are uploaded unchanged. Files above 600KB are decoded and compressed; if no candidate is smaller than the original, the original is retained. This preserves correctness and avoids replacing a valid image with a larger re-encode.

3. **Use bounded, aspect-preserving canvas compression.**

   JPEG/WebP inputs are candidates for lossy quality reduction and optional proportional downscale. PNG inputs may be proportionally downscaled while preserving PNG output type. The implementation never crops, never pads, and never changes aspect ratio.

4. **Skip GIF compression.**

   Canvas re-encoding an animated GIF would usually keep only one frame. GIFs therefore keep existing validation and upload behavior.

## Risks / Trade-offs

- Browser canvas APIs can fail for unusual images → fall back to original file and keep upload working.
- Compression may not reach 600KB for every large image → upload the smallest smaller candidate rather than looping indefinitely or over-degrading quality.
- PNG photos may remain large because PNG is lossless → preserving transparency and type is safer than converting to JPEG without explicit operator intent.
- Client-side compression adds a short wait before the file appears in the pending queue → the queue label will show the resulting size so the wait is explainable.
