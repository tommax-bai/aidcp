## Why

The desktop client currently renders the Facebook slow-start curve explanation and help entry whenever the slow-start row is visible, even when Cloud has confirmed another operation mode. This makes inactive cold-start behavior look applicable and can mislead operators about the current environment.

## What Changes

- Keep the slow-start selector available for eligible Facebook environments, but show its curve help entry and explanatory copy only when the last Cloud-confirmed environment mode is `slow_start` (active or graduated).
- Preserve non-optimistic behavior during writes: pending enable/disable feedback does not invent a new guidance visibility state before Cloud readback.
- Add renderer regression coverage for confirmed off, active, graduated, pending, unknown, and cross-environment states.
- Record the current data-authority boundary: the help table is static client content and is not fed by the editable Cloud global slow-start curve. Making the full table dynamic is not part of this focused presentation fix.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-companion-ui`: Slow-start curve guidance is conditional on the last Cloud-confirmed slow-start selection instead of appearing whenever the selector row is visible.

## Impact

- `aidcp-edge`: slow-start row markup, renderer state application, and focused renderer tests.
- `aidcp` OpenSpec delta for the existing companion UI capability.
- No Cloud route, database, protocol-v2, dependency, deployment, packaging, or OL change.
