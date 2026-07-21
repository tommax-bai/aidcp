## Why

Facebook Reels already records one Cloud `view` whenever Edge proves that a new Reel is active, but the desktop activity stream only shows a “读” entry after a later `note.open`. This makes “今日进展” increase while “今天做了这些” omits the corresponding real browse action.

## What Changes

- Emit one readable “读” activity entry whenever Edge reports a newly active Reel card.
- Describe the evidence honestly as “看了” or “浏览了”, not as having finished or deeply read the video.
- Reuse the Reel card’s actual author and summary when present, with a generic fallback when metadata is missing.
- Suppress a later duplicate `note.open` activity entry for the same Reel while still forwarding its `note.detail` and preserving Cloud accounting.
- Keep ordinary Facebook Feed/detail activity behavior and Cloud `dailyUsage` authority unchanged.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-companion-ui`: Require every newly reported Facebook Reel view to appear once in “今天做了这些” as a truthful “读” activity without double-counting a later open of the same Reel.

## Impact

- `aidcp-edge`: Facebook Reel/session activity projection, companion UI event type/wording, and focused tests.
- Control repo: OpenSpec delta and validation record.
- No Cloud behavior, protocol, database, Console, deployment, or installer changes.
