## Why

Facebook startup authentication can report a terminal failure and exit while the AdsPower browser it started remains open. The same failure is retained structurally, but the main presence line ignores it and falls back to `待命中`.

## What Changes

- Before exiting on a terminal Facebook authentication failure, call the existing confirmed close operation for the owned AdsPower browser and report confirmed browser closure to Electron.
- Make the existing `loginFlow.failed` fact win over the generic non-running `待命中` presence fallback.

## Capabilities

### Modified Capabilities

- `facebook-browser-environment`: Close the owned startup browser on terminal authentication failure.
- `edge-fleet-console`: Display retained terminal authentication failure in the main presence line.

## Impact

- `aidcp-edge` startup authentication exit and renderer view logic.
- No new states, retry loops, compatibility paths, manual-session retention, Cloud/protocol/schema changes, or installer release.
