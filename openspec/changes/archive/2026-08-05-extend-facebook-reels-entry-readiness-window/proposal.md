## Why

A live OL Facebook session needed about 20 seconds to move from `/reels/` through `/reel/` to a canonical `/reel/<id>`, but Native stopped its entry-readiness check after 8 seconds. The browser eventually reached Reels, yet the early generic timeout broke browsing continuity and left Cloud waiting for the 240-second idle watchdog.

## What Changes

- Extend only the initial and single retry Facebook Reels entry document-readiness windows from 8 seconds to 30 seconds through one named Native constant.
- Preserve the separate 15-second canonical Reel identity/card hydration window, the one-retry bound, cancellation/deadline gates, blocker handling, and canonical success proof.
- Add regression and timeout-budget coverage for the 30-second entry-readiness contract.
- Keep the existing 180-second Facebook scroll request/admission/engine/session budget and 240-second Cloud idle watchdog because the bounded worst-case entry path remains below both ceilings.
- Do not change other Facebook navigation readiness windows, Cloud behavior, protocol fields, packaging, installation, deployment, or real-account execution.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `facebook-reels-browse`: allow each authorized Reels entry navigation attempt up to 30 seconds to reach a ready document while retaining canonical Reel-card success requirements and bounded recovery.

## Impact

- Owning repo: `aidcp-edge` Native Facebook Reels entry executor and focused Native/timeout-contract tests.
- Control repo: OpenSpec delta and validation/delivery evidence.
- No Cloud, Console, protocol, database, dependency, or configuration change.
- No Edge installer build or installed-client update unless separately requested.
