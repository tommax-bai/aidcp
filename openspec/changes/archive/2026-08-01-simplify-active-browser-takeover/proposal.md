## Why

Exact public-egress probing makes AdsPower Active-browser takeover depend on an extra endpoint, CDP network probing, and a stable one-request-to-one-IP assumption. Rotating or multi-egress proxies and transient probe failures can reject a usable Active browser, hide the original startup failure, and leave the browser running without a controllable Edge core.

## What Changes

- **BREAKING**: Attach directly whenever AdsPower reports a profile as Active; do not resolve, synchronize, preflight, or compare proxy state before that takeover.
- Remove expected proxy-egress acquisition, browser/direct public-egress probing, and exact egress-equality takeover gating.
- Keep Cloud-authoritative proxy resolution, exact AdsPower write/readback, system-upstream chaining, and Facebook reachability preflight for an Inactive profile before a fresh browser start.
- Simplify the Facebook proxy UI to configuration, reachability/preflight time, and session receive traffic; remove browser/direct public-egress fields and “verified egress” conclusions.
- Remove the terminal `adspower_active_proxy_takeover_rejected` lifecycle classification because Active takeover no longer produces that failure.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `pluggable-browser-provider`: Active AdsPower profiles are attached directly without proxy or public-egress gates.
- `facebook-proxy-preflight`: Preflight proves Facebook reachability only and no longer acquires expected public egress.
- `edge-fleet-console`: The proxy detail surface no longer displays browser/direct public-egress evidence.
- `system-upstream-proxy-chain`: Chain readiness and reachability remain distinct without browser public-egress evidence.

## Impact

- `aidcp-edge`: AdsPower provider launch, Electron startup ordering, proxy preflight, browser traffic observation, proxy status UI, and focused lifecycle/provider tests.
- Control specs: replace the prior Active egress-equality contract and remove public-egress display requirements.
- No Cloud API, database, protocol-v2, proxy credential, deployment, or installer change.
