## Why

The desktop shell can retain a previous browser generation's `proxyRuntime=verified` snapshot after the Edge core or browser has stopped. Because the renderer prioritizes that snapshot over a newer preflight result, a stopped environment can still show “代理已验证”, contradicting the current runtime-evidence contract and obscuring the current startup decision.

## What Changes

- Bind proxy runtime evidence to the live browser/core generation that produced it.
- Invalidate the old runtime snapshot when the browser generation ends, including intentional stop, abnormal child exit, and a new start that is blocked before a replacement core is spawned.
- Preserve the existing separation between proxy configuration, startup preflight, browser egress observation, and the stricter Active-browser takeover gate.
- Add lifecycle and renderer regressions proving expired evidence cannot mask a stopped state or a newer failed preflight while live current-generation evidence still takes precedence.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `proxy-runtime-observability`: Require browser egress evidence to become invalid as soon as its owning browser/core generation is no longer live, not only when a replacement browser generation starts.
- `facebook-proxy-preflight`: Allow preflight to yield only to current browser-generation evidence, so a failed replacement startup cannot be masked by an expired runtime result.
- `edge-fleet-console`: Prevent stopped environments from rendering historical proxy verification, IPs, timestamps, or session traffic as current.

## Impact

- **Edge:** Electron environment lifecycle projection, proxy runtime normalization/view logic, and focused lifecycle/runtime tests.
- **Control:** focused deltas to the existing runtime-evidence, preflight-projection, and fleet-console contracts.
- **Unchanged:** Cloud proxy authority, preflight reachability and cache semantics, AdsPower proxy synchronization, protocol v2, risk state, and Native Page Engine behavior.
