## Why

The dev WeChat Channels account has active authentication and healthy reads, but outbound comment and DM testing cannot reach the platform because the Cloud per-channel write controls are still false, the Edge adapter requires previously completed write probes, and no write descriptors are enabled. The operator has explicitly requested a dev-only escape hatch so the real send path can be exercised and calibrated.

## What Changes

- Add an explicit unverified-write test mode that Electron injects only for an unpackaged development client connected to the named `dev` Cloud environment.
- In that mode, allow comment-reply and DM-text capability projection to bypass the prior-write-probe evidence gate and the two Cloud per-channel write booleans; retain scoped/versioned Cloud controls, authentication, identity, healthy reads, global/local write gates, kill switches, endpoint circuits, approval, risk-state, idempotency, and result-verification gates.
- Let the existing Cloud global interaction-write switch admit the exact pre-0046 schema when `AIDCP_DEPLOY_ENV=dev`, without changing the PostgreSQL database still shared by dev and ol.
- For reviewed dev sends, skip the post-login cooldown and quota-only RiskController denial that otherwise keep a zero-default `dm_reply` from ever reaching a real test. Restricted/frozen risk states and the interaction policy's account/thread limits remain active.
- Distinguish Cloud-local rate admission from a real WeChat rate-limit response in the client message.
- Add candidate comment-create and DM-send descriptors derived from the currently loaded first-party WeChat Channels bundle, while labeling them as unverified test evidence rather than captured production evidence.
- Accept a send as confirmed only when the platform response contains the channel-specific server identifier; schema drift, rejection, lost responses, and verification failures remain failed or ambiguous.
- Keep packaged clients and `ol`/custom Cloud environments fail-closed.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `wechat-channels-interaction`: permit an explicit, dev-only unverified write test path without weakening production capability truth or send-result honesty.

## Impact

- Edge: WeChat Channels feature flags, probes, request descriptors, send payloads/ack parsing, Electron child-process environment injection, diagnostics, and tests.
- Cloud: simple dev-deployment legacy-schema gating, reviewed-send cooldown/quota compatibility, diagnostics, and tests; migration `0046` remains unapplied.
- Control: OpenSpec delta and validation evidence.
- Deployment: Edge source integration without an installer, plus Cloud dev source/config deployment. The running unpackaged dev client must be restarted to apply the new child-process environment.
