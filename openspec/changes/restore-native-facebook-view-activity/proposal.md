## Why

Facebook Native-only browsing reports Feed/Reels cards to Cloud, but its Edge session adapter only projects a presence line for those reports. The legacy Facebook session also projected proven single-card Reels and strict single-video Feed batches into the desktop activity stream and local fallback view count, so the Native cutover currently makes real browsing invisible and undercounts it locally.

## What Changes

- Restore one truthful desktop read activity and one local fallback `views` increment for each newly reported single-card Reel.
- Restore the same projection for a Feed batch only when it contains exactly one card and that card is classified as video.
- Deduplicate projected card identities for the lifetime of the Native Facebook browse session.
- Continue reporting later `note_detail` data to Cloud while suppressing its duplicate local read activity and fallback increment when the same canonical item was already projected from cards.
- Preserve ordinary multi-card and non-video Feed semantics.
- Add Native session parity tests derived from the legacy Facebook session behavior.

## Capabilities

### New Capabilities

- `native-facebook-view-activity`: Defines which proven Native Facebook Feed/Reels presentations become truthful desktop read activities, fallback view increments, and duplicate-suppression witnesses.

### Modified Capabilities

None.

## Impact

- `aidcp-edge/src/native-page-engine/browse-session.ts`
- Focused Native browse-session tests in `aidcp-edge`
- Edge companion activity and local fallback statistics only; no Cloud protocol, risk counter, browser command, selector, packaging, or deployment changes
