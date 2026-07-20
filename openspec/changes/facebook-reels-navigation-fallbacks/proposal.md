## Why

Facebook Reels accepts keyboard and small wheel navigation, but the first implementation relied only on the far-right button. A real So La run proved that the button probe includes unrelated header controls and rejects the first Reel when the previous control is disabled, so Cloud-issued scrolling stops without moving the video.

## What Changes

- Navigate to the next Reel with a verified fallback ladder: ArrowDown first, then one randomly sized 70–100px wheel gesture, then the far-right next control.
- Verify route or active-video identity after every input and continue to the next method only when the current method does not move the Reel.
- Tighten the button fallback to the Reel navigation rail, allow a single enabled next control on the first Reel, and keep ambiguous targets fail-closed.
- Report method-level failure reasons in Edge logs while preserving the existing protocol-level truthful `no_target` result.
- Add regression coverage for keyboard success, wheel fallback and random range, first-Reel button layout, ambiguity, and unchanged identity.

## Capabilities

### New Capabilities

- `facebook-reels-navigation`: Defines ordered, human-like and post-condition-verified navigation between Facebook Reels.

### Modified Capabilities

None.

## Impact

- Affects only `aidcp-edge` Facebook Reels navigation and its focused tests.
- Does not change Edge/Cloud protocol types, Cloud scheduling, risk accounting, or other platforms.
- No new dependency and no Edge installer build are required.
