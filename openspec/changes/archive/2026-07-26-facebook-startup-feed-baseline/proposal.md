## Why

Facebook Native-only browsing currently scans whichever page the persisted fingerprint browser last closed on. If that page is a Reel, profile, group, search result, or detail page, the new automation session can misclassify it as the current list surface and stall or continue an unauthorized excursion instead of starting from Feed.

## What Changes

- Establish the canonical Facebook home Feed before the first card scan of every new or resumed automatic browse session.
- Perform the reset in the Native Facebook adapter with trusted CDP navigation, then report cards only from the resulting Feed page.
- Preserve Cloud authority over later transitions to Reels, search, detail, groups, and publish surfaces.
- Keep Xiaohongshu and WeChat Channels startup behavior unchanged.
- Add regression coverage proving a persisted non-Feed page cannot become the Facebook session baseline.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-feed-continuity`: Require every Facebook automatic browse start/resume to establish the canonical Feed before its initial scan.

## Impact

- Affected repository: `aidcp-edge`.
- Affected runtime: Rust Native Page Engine Facebook command routing and focused Native tests.
- No protocol, Cloud orchestration, risk-state, database, or configuration changes.
- Source delivery only; this change does not package, sign, or release a desktop installer.
