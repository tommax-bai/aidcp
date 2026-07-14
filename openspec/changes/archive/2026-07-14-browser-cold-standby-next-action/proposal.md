## Why

Long quota rests and inactive windows can leave AdsPower/Chrome browsers open for many minutes while no safe automatic action can run. Keeping the browser open preserves state, but it burns memory/CPU across multi-environment fleets and makes resource pressure worse.

## What Changes

- Add a cloud-side next-action wait estimate that explains when an account is next eligible to perform automated browser work.
- Add an optional browser cold-standby hint to the existing edge UI snapshot stream.
- Add an edge-side cold-standby controller that, when enabled, closes the browser during long eligible waits and restarts the environment shortly before the forecasted wake time.
- Add a runtime switch for cold standby, default enabled, with a conservative threshold and warmup buffer.
- Keep hard blockers honest: captcha, login, manual intervention, environment occupancy, and unknown wait causes must not be converted into guessed wake times.

## Capabilities

### New Capabilities
- `browser-cold-standby`: cloud-generated long-wait forecasts and edge-side browser cold standby behavior.

### Modified Capabilities

## Impact

- `aidcp-cloud`: risk/session wait estimation, `ui.snapshot` protocol payload, and focused tests.
- `aidcp-edge`: protocol types, UI-event sanitization, Electron supervisor lifecycle, settings/env switch, and focused tests.
- `docs/protocol.md`: optional cold-standby snapshot fields.
- OpenSpec: new behavior contract and task tracking.
