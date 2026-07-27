## Why

The Native Facebook first-post selector currently re-probes only 450 ms after each smooth scroll. On slower group feeds, all bounded scroll rounds can finish before the first post hydrates, producing an incorrect `no_candidates` outcome even though the page would render a commentable post shortly afterward.

## What Changes

- Keep the existing bounded same-group scrolling behavior and maximum round count.
- After every first-post scroll completes, wait an additional fixed 2 seconds before probing the rendered feed for eligible posts.
- Preserve the existing no-search, no-group-switch, canonical-permalink, comment-affordance, and honest-failure requirements.
- Add focused regression coverage for the post-scroll settle interval and probe ordering.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-scheduled-comment`: Require a fixed 2-second hydration settle between each first-post scroll and the following candidate probe.

## Impact

- Edge Native Facebook page engine and its bundled router fragment.
- Focused Native/router tests and generated artifact integrity checks.
- No protocol, Cloud, Console, persistence, configuration, or deployment contract changes.
