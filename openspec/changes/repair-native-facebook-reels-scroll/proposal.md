## Why

Facebook production page execution now runs Native-only, but Native `page.scroll` still treats Reels as an ordinary document and calls `window.scrollBy`. On the Reels snap surface that can leave the active video unchanged while returning another normal `page.cards`, causing a high-rate false-progress loop and bypassing the Cloud-provided `dwellMs`.

## What Changes

- Route Native Facebook scroll execution by observed list surface instead of sharing one document-scroll branch.
- Restore Reels-specific forward navigation with bounded trusted inputs and require the active Reel identity to change before reporting new cards.
- Honor Cloud-provided `page.scroll.dwellMs` against the last `page.cards` arrival time before actuating either Feed or Reels scrolling.
- Return an honest failed action result when Reels cannot prove movement; never convert `moved=false` into normal browsing progress.
- Add regression coverage for Reels navigation, no-change termination, dwell timing, and unchanged Feed behavior.

## Capabilities

### New Capabilities

- `facebook-reels-native-scroll`: Native-only Facebook Reels forward navigation, identity verification, and honest no-change behavior.

### Modified Capabilities

- `command-pacing`: Require the Native Facebook path to consume `page.scroll.dwellMs` using the existing page-cards timing anchor rather than dropping the field.

## Impact

- Affected repository: `aidcp-edge`.
- Affected runtime: Rust Native Page Engine and its TypeScript session facade/tests.
- Existing protocol message names and payload fields remain unchanged; Cloud orchestration and risk ownership remain unchanged.
- This source change does not itself build, sign, or publish a desktop installer.
