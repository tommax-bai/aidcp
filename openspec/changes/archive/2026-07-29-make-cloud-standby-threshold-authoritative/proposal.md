## Why

Edge persists an invisible `browserColdStandbyMinWaitMs` value and takes the
maximum of that value and Cloud's advertised threshold. A value materialized by
an older client can therefore silently override current Cloud policy across
upgrades even though customers have no UI for viewing or changing it.

## What Changes

- Make Cloud's `browserStandby.minWaitMs` the single policy authority for the
  cold-standby wait threshold.
- **BREAKING** Remove Edge's persisted setting and environment override for the
  wait threshold, and stop taking `max(local, cloud)`.
- Ignore legacy `browserColdStandbyMinWaitMs` values immediately after upgrade
  and omit them from subsequent settings reads and writes.
- Keep the existing wire field, visible local enable switch, three-minute
  post-wake hold, authentication/task/in-flight safety gates, and deterministic
  wake paths unchanged.
- Treat a missing, malformed, or unavailable Cloud hint as insufficient
  evidence to enter a new standby cycle.
- Update protocol documentation, diagnostics, and regression coverage to state
  the single-authority behavior explicitly.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `browser-cold-standby`: Cloud owns the wait threshold; Edge validates and
  safely executes the current Cloud hint without a hidden local threshold veto.

## Impact

- `aidcp-edge`: cold-standby decision helper, Electron settings migration, and
  focused lifecycle/settings tests.
- `aidcp-cloud`: source comments and focused contract coverage only; Cloud's
  existing hint shape and runtime behavior remain unchanged.
- `aidcp`: `browser-cold-standby` specification and `docs/protocol.md`.
- Existing clients keep their old conservative behavior until a new Edge build
  is installed; no protocol version bump or Cloud deployment is required.
