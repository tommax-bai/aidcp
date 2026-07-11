## Why

The Electron companion currently shows minute/hour quota windows as `待刷新`
once their snapshot expiry passes, but it cannot tell the operator when cloud
expects the next usable quota slot. Cloud already computes quota retry timing
for risk backpressure, so hiding that timing makes the client less actionable
than the runtime really is.

## What Changes

- Extend cloud-supplied `ui.snapshot.dailyUsage.windows` with optional
  refresh timing for rolling quota windows when cloud can compute it.
- Keep the existing `expiresAt` stale-snapshot marker, but distinguish it from
  the next quota release/refresh time exposed to the operator.
- Preserve backward compatibility: older edges ignore the new fields, and new
  edges continue to handle old snapshots without fabricating timing.
- Update the Electron expanded daily usage detail to show a concrete refresh
  hint such as a countdown or local clock time instead of only `等待云端快照`
  when authoritative timing is present.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `edge-companion-ui`: daily usage window snapshots expose optional
  cloud-derived refresh timing and Electron displays it without guessing.

## Impact

- `aidcp-cloud`: `ui.snapshot.dailyUsage` protocol type and snapshot assembly
  for account usage windows.
- `aidcp-edge`: mirrored protocol type, `ui.snapshot` to `[ui-event]`
  sanitization, Electron main-process normalization, and renderer copy.
- Tests in cloud `ui-snapshot`/usage coverage and edge UI event/Electron
  companion coverage.
