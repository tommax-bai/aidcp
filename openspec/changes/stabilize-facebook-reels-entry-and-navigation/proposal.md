## Why

The installed Facebook runtime can reach a Reels page whose active video is readable while DOM control topology does not yield a unique navigation axis, so Native returns `not_started/no_target` before trying the verified keyboard actuators and Cloud eventually releases the session idle. Separately, a configured Reels-primary entry is rendered as a generic page scroll and may navigate an exact background target without bringing that target forward, leaving the operator looking at Feed while Edge reports Reels entry progress.

## What Changes

- Make verified Reel identity transition, not pre-dispatch DOM axis classification, authoritative for selecting a working `ArrowRight` or `ArrowDown` actuator.
- Bound active keyboard probing to one attempt per direction, re-probe the same Reel before every later write, stop after the first observed transition, and preserve ambiguous outcomes when no canonical next Reel is proven.
- Keep DOM topology as an ordering hint and safe pointer-fallback locator rather than a prerequisite for keyboard input.
- Keep the first configured-primary or evidence-based Reels entry navigation background-first. Only when bounded readback confirms that the exact target did not enter a ready Reels surface, activate that same target once, re-probe it, and retry the navigation at most once while retaining canonical-card postconditions.
- Render Reels-entry `page.scroll` commands as “进入 Reels” with a safe reason-specific summary; reserve “页面滚动” for ordinary page scrolling and preserve the existing delivery-versus-success disclaimer.
- Do not add protocol fields, Cloud policy, JavaScript scrolling, unbounded retries, blind clicks, installer packaging, or real-account validation.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-reels-native-scroll`: allow bounded, postcondition-driven keyboard direction probing when structural axis evidence is absent or stale.
- `facebook-reels-navigation`: treat DOM axis as an input-order hint while retaining exact-target identity checks, late-movement suppression, and honest ambiguous termination.
- `facebook-reels-browse`: recover one confirmed ineffective configured-primary or fallback Reels entry navigation with one exact-target foreground activation and at most one fresh navigation retry while still requiring canonical Reels-card confirmation.
- `edge-companion-ui`: label Reels-entry command intent separately from ordinary page scrolling without claiming execution or platform success.

## Impact

- Owning repo: `aidcp-edge` Native Facebook executor, embedded Facebook router contracts, and Electron command-diagnostic projection/rendering.
- Focused Native fake-CDP/router tests and companion UI parser/rendering tests.
- Control repo OpenSpec deltas and implementation evidence.
- No Cloud wire-shape or database change, no deployment, and no desktop package or installed-client replacement.
