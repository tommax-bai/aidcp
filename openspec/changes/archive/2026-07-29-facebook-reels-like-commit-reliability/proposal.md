## Why

Facebook Reels currently dispatches one raw CDP pointer sequence and then only waits for a selected-state witness. Live dev evidence shows this path can receive and dispatch the command yet repeatedly return `state_unchanged`, while the hardened ordinary-Feed path already handles Facebook controls whose first event is ignored or only opens a reaction picker.

## What Changes

- Make Reel likes re-probe the same active Reel immediately before every write and bind all verification to that canonical Reel.
- Select the commit mechanism from observed control state: use the proven in-page activation path for the primary React control, and when the first activation opens a reaction picker, locate the unique Like item inside that visible picker and commit it with trusted CDP pointer events.
- Dispatch at most one primary activation and at most one picker commit; never retry a click after Reel movement or indeterminate verification.
- Add bounded, redacted diagnostics for the selected control, commit path, picker observation, and terminal verification reason.
- Preserve existing Cloud probability, quota, risk, cooldown, accounting, and user-visible success rules: only a same-Reel positive selected-state receipt is success.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-note-scoped-targeting`: extend exact-target like actuation and post-condition requirements to the dedicated Reels surface, including per-control event semantics and scoped reaction-picker fallback.

## Impact

- Edge: `src/facebook/reels-reader.ts` and focused Facebook Reel tests.
- Control contracts: one delta requirement under `facebook-note-scoped-targeting` plus implementation/validation evidence.
- No protocol, Cloud policy, database, Console, installer, or deployment change is required.
