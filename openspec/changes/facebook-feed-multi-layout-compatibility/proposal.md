## Why

Facebook currently serves at least two feed DOM layouts to local account environments. The existing Edge reader only recognizes the semantic `role="feed"` / `role="article"` layout, so accounts receiving the lightweight div layout expose real posts in the browser but report `no_feed`, never produce `page.cards`, and therefore never enter the browsing loop.

## What Changes

- Recognize both the semantic feed/article layout and the lightweight story-message layout with locale-neutral structural signals.
- Reuse the same feed-card discovery rules for initial scanning and in-feed target resolution so browsing does not regress after cards are reported.
- Continue to require an existing canonical post-shaped identity before a discovered card can be reported or targeted; cards that only expose ambiguous photo/video resource identifiers remain skipped.
- Preserve the existing semantic-layout behavior, bounded retries, blocker reporting, and fail-closed action semantics.
- Add regression coverage for both layouts and validate the alternate layout against a running local AdsPower Facebook environment through CDP.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-feed-continuity`: Feed-surface detection and card settling must support both observed Facebook feed layouts without treating an empty or unrelated page as a feed.
- `facebook-feed-browse`: Top-level card discovery and in-feed target resolution must use the same multi-layout rules while retaining stable-identity and no-fake-success guarantees.

## Impact

- Owning runtime: `aidcp-edge` only, primarily Facebook feed scanning and shared in-feed target helpers.
- Protocol, cloud orchestration, risk quotas, persistence, and database schemas are unchanged.
- Existing accounts on the semantic layout retain the current path; accounts on the lightweight layout can browse only posts with a reliable canonical identity.
