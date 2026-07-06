## Context

精选内容池 now stores curated note reference images up to the platform-safe cap of 9. The参照洗稿 path, however, still has independent 3-image caps in the cloud publish pipeline:

- `PublishScheduler` freezes only the first 3 images into `referenceNote.images`.
- `buildReferenceImageGuidance` includes only the first 3 URLs in prompt guidance.
- `ImageGenerator` passes only the first 3 URLs to the image provider.

The console content page reads `publish_metadata.referenceImageAudit.requestedCount`, so it honestly displays 3 because the cloud pipeline really only requested 3.

## Goals / Non-Goals

**Goals:**

- Use up to 9 valid reference images from the selected curated source row when参照洗稿 is triggered with image reference mode.
- Keep a single shared cap so scheduler freeze, prompt guidance, provider input, and audit cannot drift back to different values.
- Keep audit wording honest: requested/usable counts reflect the images actually made available to the generation pipeline.

**Non-Goals:**

- Do not change curated-image extraction, relocation, or storage limits.
- Do not change generated image count planning; this only expands reference images, not output image count.
- Do not publish or reuse source images directly.
- Do not change provider/model configuration.

## Decisions

1. Add a shared cloud constant for publish reference-image guidance count.

   The limit is a pipeline contract, not a UI setting. A shared exported constant avoids the current three independent `3` literals. The value is 9 to match the curated reference image hard cap and platform image upper bound.

2. Keep invalid URL filtering before counting.

   The scheduler and generator continue to filter blank or unusable `ossUrl/sourceUrl` values. The audit counts the frozen valid snapshots and separately computes usable URL count, preserving existing honesty semantics.

3. Keep historical records unchanged.

   Existing `publish_log` rows already froze 3 images and should continue to display 3. Only new参照洗稿 runs after deployment will show up to 9 when the source row has that many usable images.

## Risks / Trade-offs

- Larger provider requests may be rejected or slower for some providers -> keep the cap at 9 and retain existing provider failure/status handling (`unavailable`, `unsupported`, partial image failure).
- More reference URLs in prompt guidance may consume more prompt tokens -> guidance includes only URLs plus small metadata, and remains bounded at 9.
- Existing tests may encode the old cap -> update tests to assert the new cap and the shared constant behavior.
