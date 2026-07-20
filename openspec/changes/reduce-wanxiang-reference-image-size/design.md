## Context

`WanxiangClient` currently separates ordinary generation (`defaultSize`) from generation with image inputs (`referenceSize`). Ordinary generation defaults to `1024*1024`; reference generation defaults to the provider preset `2K`, which preserves the final input image's aspect ratio at roughly 4.19 megapixels. Both defaults can already be overridden independently by environment variables.

Recent live outputs confirm that the `2K` reference path commonly produces 4.7–6.0 MiB PNGs. These bytes cross the provider-to-cloud-to-OSS path and are then downloaded and uploaded sequentially by Edge during Xiaohongshu publication.

## Goals / Non-Goals

**Goals:**

- Make `1K` the zero-configuration Wanxiang reference-image preset.
- Preserve the existing runtime override and request-shape semantics.
- Prove with focused tests that only the reference-image default changes.
- Deploy the committed default to `dev` and verify the running artifact/config boundary.

**Non-Goals:**

- No image transcoding, resizing, or recompression after generation.
- No change to image count planning, reference-image ordering, or reference fidelity auditing.
- No change to ordinary Wanxiang generation, Seedream generation, or deterministic text cards.
- No automatic `ol` rollout and no mutation of existing OSS images or pending drafts.

## Decisions

1. **Change the constructor fallback, not the deployment environment.** `referenceSize` will fall back to `1K` after checking the explicit constructor option and `AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE`. This makes the product default portable and testable while retaining instant operator rollback through the existing override.

2. **Keep provider presets instead of introducing fixed dimensions.** Wanxiang's `1K` preset continues to preserve the last reference image's aspect ratio. Fixed `1080*1440` would change visual-reference geometry and is outside this latency-only change.

3. **Keep the output format untouched.** PNG-to-JPEG/WebP conversion could reduce bytes further, but it introduces quality, text-legibility, alpha, and format-policy decisions. This change isolates the resolution lever first.

4. **Verify the three request branches independently.** Focused tests will cover reference images with no override (`1K`), reference images with an explicit override, and generation without references (`1024*1024`).

## Risks / Trade-offs

- [Risk] Fine text or small details in generated imagery may be less legible at `1K`. → Preserve the environment override for immediate rollback and keep deterministic text cards at 1728×2304.
- [Risk] Lower pixel count may not reduce PNG bytes by exactly 75% for every scene. → Treat the pixel reduction as deterministic and measure real output byte reduction separately during runtime observation.
- [Risk] A stale deployed file could leave runtime at `2K`. → Deploy only from the integrated clean `master`, compare the relevant file checksum, restart the documented service, and verify the active default with a non-billing request-shape probe or focused runtime test.

## Migration Plan

1. Land the code and tests on `aidcp-cloud/master`.
2. Deploy the clean default checkout to `dev` through the documented backup/rsync/restart flow.
3. Verify service health and that no `AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE` override masks the new default.
4. Roll back without code reversion by setting `AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE=2K` and restarting, or by reverting the commit and redeploying.

## Open Questions

None for this scoped change. Post-generation compression can be evaluated separately after observing real `1K` output quality and transfer size.
