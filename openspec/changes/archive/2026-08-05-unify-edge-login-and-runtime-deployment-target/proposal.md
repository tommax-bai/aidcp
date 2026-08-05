## Why

The desktop client can currently switch its automation WebSocket target while a baked or explicit customer-auth URL continues to serve login and data requests from another deployment. This allows mixed DEV/OL authority, reuses target-agnostic local sessions, and makes a single environment label unable to describe the client honestly.

## What Changes

- Replace independently resolved official URLs with one persisted `dev | ol` deployment target selected before login. The target resolves customer login, token refresh, customer data APIs, environment ownership, and automation WebSocket endpoints as one built-in tuple.
- Add the DEV/OL selector to the login gate. Changing target while authenticated becomes an explicit logout-and-return-to-login transition that stops automation before any new-target request is allowed.
- Bind tokens, encrypted credential prefill, visible-environment authority, pending Cloud mutations, and actual automation receipts to a deployment target. Legacy target-less sessions fail closed and require one fresh login.
- **BREAKING**: official desktop runtime no longer treats baked `aidcpClientAuthUrl`, persisted `clientAuthUrl`, `AIDCP_CLIENT_AUTH_URL`, or an independent `AIDCP_CLOUD_URL` as authorities that can split the two official transports. Custom endpoints remain available only through an explicitly enabled developer-only paired target and are never shown in the customer login selector.
- Remove absolute customer-auth URL injection and verification from desktop build/release paths. A package MAY still carry a non-secret default deployment target used only to preselect the login environment.
- Display the selected/authenticated target and the automation connection target separately until an engine has confirmed its connection; waiting-slot activity names the confirmed automation target only.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `edge-cloud-env-selection`: Make the login-time deployment target the single authority for official data and automation endpoints, and replace in-session partial transport switching with a target transition.
- `edge-client-login-gate`: Select and persist the target before authentication, scope credentials and sessions to it, and fail closed on legacy or mismatched target state.
- `edge-desktop-packaging`: Stop baking or verifying absolute customer-auth URLs while retaining an optional default target as a non-authoritative login preselection.

## Impact

- `aidcp-edge`: Electron main/preload/login renderer, target resolution, session and local durable-state migration, automation lifecycle coordination, focused tests, package scripts, CI workflow, and release documentation.
- `aidcp`: OpenSpec deltas and delivery evidence.
- No Cloud protocol, Cloud runtime, database, Console runtime, ECS deployment, OL access, or real-account action is required.
- The change reaches installed clients only after a separately authorized Edge package/release and installation.
