## Why

Facebook Reels exposes an inline author Follow control beside the active video, but the Edge Reels driver only supports reading, advancing, and liking. A live probe on the authorized `Tianxing Bai` AdsPower profile confirmed that `Salon de Comolis` has one unique inline `关注` control on Reel `1964804494173822`, and that a trusted click changes the same control to `已关注`; the production path now needs the same target binding and truthful verification.

## What Changes

- Add a Reel-specific follow executor that binds the command to the canonical active Reel and the uniquely associated inline author Follow control.
- Extend `interaction.follow` with an optional Reel `noteId` target so a delayed command cannot follow whichever author happens to be visible later.
- Treat an already-followed state as the existing truthful `ok:true, reason:'already_followed'` no-op; report a real new follow only after the same Reel exposes a Following state.
- Route Facebook `interaction.follow` to this executor only while the session is in Reels mode; ordinary Facebook Feed remains unsupported and fail-closed.
- Keep the durable probe read-only by default and require an explicit real-follow flag plus an exact author match before it can click.
- Do not add an automatic Reel follow-selection policy in this change. Cloud strategy must explicitly decide and send a note-bound follow command; this change supplies and validates the actuator without inventing a follow probability.

## Capabilities

### New Capabilities

- `facebook-reels-inline-follow`: Defines active-Reel follow targeting, trusted input, same-Reel post-condition verification, truthful receipts, and gated live probing.

### Modified Capabilities

- `facebook-note-scoped-targeting`: Extends exact canonical Reel identity binding to the Reel-specific `interaction.follow` path.

## Impact

- `aidcp-edge`: `FacebookReelsReader`, Facebook command routing, protocol payload type, focused Reel tests, and the live probe script.
- `aidcp-cloud`: protocol payload type compatibility only; no follow-decision or automatic selection change.
- Control/docs: OpenSpec delta and `docs/protocol.md` payload documentation.
- No database schema, Console UI, installer build, automatic follow probability, or non-Reel Facebook follow behavior changes.
