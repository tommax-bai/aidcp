## Why

Facebook may open Reels on the valid `/reel/` landing route with one visible active video but no canonical Reel id; the id appears only after advancing. The Native driver currently treats that state as `no_target` before dispatch and hard-codes the vertical `ArrowDown` / downward-wheel / lower-button layout, so anonymous entry stalls and horizontally paged Reels cannot advance.

## What Changes

- Separate “one active Reel is structurally resolved” from “that Reel has a canonical platform identity”; allow one bounded bootstrap advance from `/reel/` without fabricating or hashing a `noteId`.
- Detect the forward-navigation axis from fresh, active-video-relative control geometry and dispatch only the matching forward key: `ArrowDown` for vertical layouts or `ArrowRight` for horizontal layouts.
- Keep the vertical wheel fallback only for a freshly proven vertical layout; never use it as a horizontal actuator.
- Generalize the fail-closed next-control locator to vertical and horizontal navigation rails while preserving unique-target, fresh-probe, and no-double-dispatch guarantees.
- Require the bootstrap postcondition to yield one canonical `/reel/<id>` card before reporting progress or counting a view; dispatched-but-unverified navigation remains an honest failed/ambiguous outcome rather than `not_started`.
- Preserve strict identity requirements for Reel reads and write interactions after bootstrap.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-reels-navigation`: Make the trusted-input ladder axis-aware and define bounded anonymous-entry bootstrap semantics.
- `facebook-reels-native-scroll`: Resolve a unique active video without requiring a pre-action `noteId`, distinguish pre-dispatch target failure from post-dispatch unconfirmed movement, and retain canonical identity as the success gate.
- `facebook-reels-browse`: Admit `/reel/` only as a non-reportable navigation bootstrap surface while continuing to require `/reel/<id>` for cards and interactions.

## Impact

- Edge Native Rust: `native/page-engine/src/facebook/reels.rs`, `native/page-engine/src/facebook.rs`
- Edge Native router: `native/page-engine/src/facebook-router/00-shared.js`
- Edge contract/unit fixtures for Reel probe decoding, axis selection, button geometry, dispatch order, and outcome phases
- No protocol-v2 shape change, Cloud data-model change, description-hash identity, compatibility knob, or package/release action
