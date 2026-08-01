## Why

Every Native Facebook `page.scroll` currently activates the bound AdsPower page before Edge knows whether the command will produce any input. Routine Feed and Reels browsing therefore repeatedly covers the operator's desktop, even though the only recovery signal that expresses prolonged browse inactivity is the Cloud watchdog's existing `idle_recover_nudge` reason.

## What Changes

- Allow Native Facebook `page.scroll` to activate its exact bound target only when the command reason is `idle_recover_nudge`.
- Remove foreground activation from all other automatic Facebook scroll reasons, including routine Feed, Search, Reels, resume, continuation, rescan, and failed-action recovery scrolls.
- Remove the separate unconditional foreground activation from the in-scroll Feed recovery-control click; it continues to re-locate the target immediately before trusted pointer input and to require the existing same-page postcondition.
- Preserve explicit operator foreground actions such as showing a browser or guided login, and preserve non-Facebook behavior.
- Reuse the existing `page.scroll.reason` value; do not add a message type, retry, timeout, fallback, or configuration knob.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `native-facebook-behavior-parity`: Restrict automatic Facebook scroll foreground activation to watchdog recovery commands and require ordinary scrolls to remain in the background.
- `browse-loop-resilience`: Remove unconditional foreground activation from the Feed recovery-control click while preserving fresh coordinate location, one trusted pointer sequence, and same-page verification.

## Impact

- Affected Edge code: Native Facebook `page_scroll` routing and Feed recovery control.
- Affected validation: fake-CDP ordering/count assertions for routine, watchdog, no-target, and Feed recovery scrolls.
- Affected contracts: OpenSpec deltas and `docs/protocol.md`; the existing Cloud-to-Edge payload shape and command mapping remain unchanged.
- Delivery boundary: Edge source behavior changes, but no desktop installer is built or released by this change.
