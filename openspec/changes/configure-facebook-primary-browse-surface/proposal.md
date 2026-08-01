## Why

Facebook browsing sessions currently enter the ordinary Feed first in every operation mode and reach Reels only after an empty, unreportable, or exhausted Feed. Operators need one environment-level choice that makes Reels the normal starting list while keeping the four operation modes independent from the selected content surface.

## What Changes

- Add an environment-level Facebook primary browse surface with two values: `feed` and `reels`.
- Default new Facebook environments to `reels` and migrate existing Facebook environments to `reels`.
- Present Facebook operation mode as one four-way client choice and primary browse surface as a separate `Feed / Reels` choice during creation and existing-environment editing.
- When `reels` is selected, Cloud discards the initial Feed observation before evaluation or accounting, authorizes the existing Edge Reels entry path, and starts the selected operation mode only after a reportable Reel card arrives.
- Preserve the current Feed path, including evidence-based Reels fallback, when `feed` is selected.
- Reuse the existing Reels reader, navigation, action, receipt, and postcondition paths; do not add a second Edge Reels executor.
- **BREAKING** Existing Facebook environments change from implicit Feed-first behavior to an explicit Reels primary surface after migration.
- Deliver source only. Client packaging, DEV/OL deployment, old-client notices, capability negotiation, and compatibility fallback are outside this change.

## Capabilities

### New Capabilities

- `facebook-primary-browse-surface`: Environment configuration, migration default, customer client controls, session-start arbitration, and truthful Reels-entry confirmation for the primary browse surface.

### Modified Capabilities

- `facebook-reels-browse`: Allow Cloud to authorize Reels because it is the configured primary surface, not only because Feed fallback evidence exists.
- `facebook-feed-continuity`: Prevent the initial Feed observation from entering evaluation or accounting when Reels is primary while preserving the existing Feed fallback evidence rules.
- `adspower-environment-provisioning`: Persist and return the Reels-default primary surface during Facebook environment creation.
- `edge-companion-ui`: Present one mutually exclusive operation-mode choice and one independent Feed/Reels choice for the selected Facebook environment.

## Impact

- **Control/contracts**: New capability plus deltas for Reels entry, Feed continuity, provisioning, client presentation, and protocol documentation.
- **Cloud/data**: Additive migration and environment policy projection/write changes, existing-environment backfill, customer API support, and session-start surface arbitration.
- **Edge**: Creation/edit controls and a new configured-primary reason that reuses `FacebookBrowseSession.enterReels()`.
- **Console**: No UI change required; existing writes must preserve the primary-surface field when they do not edit it.
- **Delivery**: Source changes and local validation only; no installer, package, DEV deployment, OL deployment, or live Facebook action.
