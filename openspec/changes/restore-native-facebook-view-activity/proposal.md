## Why

Facebook Native-only browsing reports Feed/Reels cards to Cloud, but its Edge session adapter only projects a presence line for those reports. The legacy Facebook session also projected proven single-card Reels and strict single-video Feed batches into the desktop activity stream and local fallback view count, so the Native cutover currently makes real browsing invisible and undercounts it locally.

## What Changes

- Restore one truthful desktop read activity and one local fallback `views` increment for each newly reported single-card Reel.
- Reject non-Facebook, reserved-route, and non-Reel identities before projecting a Reel view.
- Restore the same projection for a Feed batch when it contains exactly one card classified as video; other non-video cards may coexist.
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

- `aidcp-edge/src/facebook/post-identity.ts`
- `aidcp-edge/src/facebook/facebook-session.ts`
- `aidcp-edge/src/native-page-engine/browse-session.ts`
- Focused Facebook identity, legacy session, and Native browse-session tests in `aidcp-edge`
- Edge companion activity and local fallback statistics only; no Cloud protocol, risk counter, browser command, selector, packaging, or deployment changes
