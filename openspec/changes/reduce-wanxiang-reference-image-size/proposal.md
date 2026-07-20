## Why

Wanxiang reference-image generation currently requests the `2K` preset, producing roughly 4.19-megapixel PNGs that are commonly 5–6 MiB each. A multi-image Xiaohongshu post therefore incurs avoidable cloud relocation, edge download, and sequential browser-upload latency even though the publishing surface does not need that source resolution.

## What Changes

- Change the default Wanxiang size for requests that contain reference images from `2K` to `1K`.
- Preserve the existing `AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE` override so an operator can explicitly restore `2K` or select another provider-supported size without a code change.
- Keep Wanxiang generation without reference images at its existing default, keep deterministic text-card output at 1728×2304, and keep Seedream sizing unchanged.
- Add focused request-shape tests proving reference-image calls use `1K` by default while configured overrides and non-reference calls retain their existing semantics.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `publish-multi-image`: Change the Wanxiang reference-image request default to `1K` while preserving explicit runtime override and unrelated image routes.

## Impact

- Code: `aidcp-cloud/src/publish-agent/wanxiang-client.ts` and its focused tests.
- Runtime: newly generated Wanxiang reference-image outputs on `dev` become approximately one quarter of the current pixel count; existing OSS objects and pending drafts are unchanged.
- Configuration: no migration or new variable; the existing `AIDCP_WANXIANG_REFERENCE_IMAGE_SIZE` override remains authoritative.
- Deployment: cloud runtime behavior changes and therefore requires normal `dev` deployment and live request-shape verification; `ol` remains unchanged unless explicitly released.
