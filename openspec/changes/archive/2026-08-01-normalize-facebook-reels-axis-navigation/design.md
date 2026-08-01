## Context

The Reels router currently admits navigation controls only when their raw rectangles are 36–68 pixels, fully inside the viewport, and separated from the active video by fixed pixel gaps. Those gates exclude two observed Facebook layouts:

- a horizontal rail whose disabled previous and enabled next controls are viewport-scale transparent side overlays, partially outside the viewport;
- a vertical rail whose compact previous/next pair sits in the outer part of the narrow gutter beside a wide landscape video, closer than the fixed right-gap threshold.

The Rust actuator already maps a resolved vertical axis to `ArrowDown` and a horizontal axis to `ArrowRight`. Its initial keyboard path intentionally does not require a clickable fallback target, but the router currently omits `axis` whenever its compact-button locator fails.

## Goals / Non-Goals

**Goals:**

- Resolve one navigation axis from stable, viewport-normalized control topology.
- Keep axis evidence separate from pointer-target eligibility.
- Preserve keyboard-first, same-target identity verification and fail-closed ambiguity handling.
- Cover the observed horizontal-overlay and outer-vertical-rail layouts at multiple viewport sizes.

**Non-Goals:**

- Blindly trying both keyboard axes when structure is inconclusive.
- Treating input dispatch, route hydration, coordinate movement, or document scroll as proof of a new Reel.
- Changing protocol v2, Cloud recovery/accounting, pacing, or Feed scrolling.
- Clicking a viewport-scale transparent overlay.
- Packaging or releasing an Edge installer.

## Decisions

### Use clipped, normalized topology for axis evidence

The router will clip every visible button rectangle to the current viewport, require a bounded visible fraction and normalized span, then compare it with the clipped active-video rectangle. All tolerances used for axis classification will be proportions of the viewport or active video; raw control dimensions and fixed pixel gaps will not admit or reject an axis. Labels that identify reaction or media actions are excluded before semantic or unknown structural pairing.

A horizontal hypothesis normally requires a previous/next pair on opposite sides of the video with substantial vertical overlap and aligned vertical centers. When Facebook renders no previous control, one unique explicitly next-labelled control may also prove horizontal topology only if it is adjacent to the video, occupies substantial viewport width and height, substantially overlaps the video's height, and fills most of the remaining right-side gutter through the viewport edge. This admits both compact side arrows and the observed side overlay without treating a generic compact `Next` beside a small video as directional proof. A vertical hypothesis requires semantically identified previous/next roles in the same outer right-side lane, aligned horizontally and ordered from previous above to next below. Unknown same-side controls never establish a vertical rail because an arbitrary two-control reaction column has indistinguishable geometry; unknown structural pairing remains available only for opposite-side horizontal controls. Defining the vertical lane relative to the remaining video-to-viewport gutter additionally excludes the inner reaction column without assuming a fixed distance from the video.

The router will accept an axis only when exactly one forward hypothesis remains. Disabled previous controls may establish the pair. A single generic next label, competing rails, or multiple forward targets remains inconclusive.

Alternative considered: expand the existing pixel ranges for the two observed screenshots. Rejected because browser size and video aspect ratio change the same layout's raw dimensions and gaps.

### Separate axis evidence from a safe pointer fallback

Axis classification considers structural candidates with a meaningful visible fraction, including partially offscreen overlays. Pointer eligibility is evaluated only after the unique axis and forward control are known. The forward control must be enabled, fully visible, occupy a bounded minimum and maximum proportion of the viewport, and remain the topmost actionable element at its center point. A large overlay may therefore return `axis:horizontal`, `found:false`, and no coordinates. An occluded or disabled forward control returns no axis and blocks every input, while a disabled previous control may still be a read-only structural anchor.

The Rust actuator explicitly admits `found:false` keyboard navigation only for `next_control_not_click_safe`; every other no-pointer reason remains pre-dispatch. The initial key still requires a fresh matching `axis`, while `found` and coordinates are required for the later button fallback.

Alternative considered: click the visible center of a large transparent overlay. Rejected because the overlay can cover unrelated controls and its raw center may not represent the arrow underneath it.

### Retain the existing keyboard-first actuator and postcondition

For a fresh matching target, Rust will continue to dispatch exactly one axis-specific key first: `ArrowDown` for vertical and `ArrowRight` for horizontal. The existing vertical-only wheel and safe button fallbacks remain unchanged. Regression coverage will explicitly exercise `axis` with `found:false` so future code cannot re-couple keyboard navigation to a clickable button.

Every input remains bound to the same active `videoKey` and optional canonical `noteId`; success still requires a distinct active video and a canonical post-transition Reel card on the same CDP target/page. No second-axis probe is introduced.

## Risks / Trade-offs

- [Facebook introduces another control topology] → Return a pre-dispatch no-target result until that structure is observed and specified; do not guess an axis.
- [A reaction column resembles a vertical pair in another locale] → Require semantic previous/next roles for vertical pairing; never use two unknown same-side controls as a vertical rail.
- [Normalized tolerances admit both axes] → Return `ambiguous:true` and dispatch zero input.
- [A stale rail is almost entirely offscreen] → Require a minimum clipped-to-raw visible fraction before it may establish an axis.
- [A compact target is covered at dispatch time] → Require a fresh center-point hit test and withhold the axis as well as pointer coordinates.
- [The keyboard does not move a layout whose overlay is not pointer-safe] → Return the existing ambiguous post-dispatch failure rather than clicking the overlay.

## Migration Plan

Implement and validate the router and Native regression tests in an isolated Edge worktree, then integrate the source change onto Edge `master`. The output shape and Rust behavior remain backward compatible, so no data migration or coordinated Cloud deployment is required. Rollback is a source revert. Installed clients remain unchanged until a separately authorized desktop package/release.

## Open Questions

None.
