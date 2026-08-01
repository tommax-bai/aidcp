## Why

Facebook Reels exposes the same navigation relationships at different browser sizes through very different control rectangles: a horizontal layout may use viewport-scale transparent side overlays, while a vertical layout may place a compact previous/next pair in an outer column beside a wide video. The current absolute pixel gates reject both structures, so the Native driver reports `no_target` and dispatches no navigation input.

## What Changes

- Infer one vertical or horizontal Reels navigation axis from normalized relationships among the active video, viewport, and previous/next controls instead of fixed control sizes or pixel gaps.
- Exclude reaction/media controls and almost entirely offscreen remnants before forming navigation hypotheses.
- Treat disabled previous controls and non-click-safe overlays as read-only axis evidence without clicking them.
- Keep pointer eligibility separate from axis evidence so a proven axis can still use the trusted keyboard path when no safe button target exists.
- Dispatch only the proven axis's CDP key first: `ArrowDown` for vertical layouts and `ArrowRight` for horizontal layouts.
- Refuse keyboard input for a disabled forward control and require a center-point hit test before exposing any pointer fallback.
- Preserve fresh same-target/page/video probes, axis-specific fallbacks, identity-change verification, and fail-closed behavior for absent or competing axis evidence.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-reels-navigation`: Define viewport-normalized structural axis evidence independently from safe pointer-target eligibility.
- `facebook-reels-native-scroll`: Require the axis-specific CDP key to remain the first write when structure proves an axis even if no safe button fallback exists.

## Impact

- Edge Native router: `native/page-engine/src/facebook-router/00-shared.js`
- Edge router contract fixtures for horizontal overlays, outer vertical rails, competing controls, and multiple viewport sizes
- Edge Native Rust regression coverage for keyboard-first dispatch with axis-only evidence
- No protocol-v2, Cloud, data-model, configuration, installer, or release change
