## Why

Operators read "daily" risk quotas as the local calendar day, and the companion UI already reports usage from the current Asia/Shanghai day. The current 24-hour sliding `day` window can block browsing while the UI still shows spare "today" quota, making normal quota backpressure look like a stuck client.

## What Changes

- Change risk quota semantics so `minute` and `hour` remain sliding burst windows, while `day` uses the Asia/Shanghai calendar day.
- Make `quota:day` retry timing release at the next local midnight instead of when the oldest event exits a 24-hour window.
- Keep existing quota numbers, risk states, persistence tables, and "quota saturation is backpressure, not a risk signal" behavior.
- Update operator-facing docs so "daily" quota means local calendar day consistently across cloud gating and companion UI usage.

## Capabilities

### New Capabilities

- None.

### Modified Capabilities

- `interaction-risk-gating`: Daily risk quota windows change from 24-hour sliding windows to Asia/Shanghai calendar-day windows.

## Impact

- Affected code: `aidcp-cloud/src/risk/`, `aidcp-cloud/src/server.ts`, today-aggregation stores, and risk/quota usage tests.
- Affected docs/contracts: `docs/risk-control.md`, `docs/protocol.md`, `docs/acceptance-tests.md`, and the `interaction-risk-gating` OpenSpec requirement.
- No protocol message shape changes and no database schema changes are expected.
