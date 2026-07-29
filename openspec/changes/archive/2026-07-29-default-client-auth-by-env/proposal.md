## Why

Edge desktop can still start without the customer login gate in local dev and in
dev-targeted desktop builds unless the launcher or workflow explicitly provides
`AIDCP_CLIENT_AUTH_URL`. That makes the client look like an old internal build:
startup does not ask for a customer login and the settings panel has no logout
entry.

The desired default is that official dev and ol environments both require the
customer login gate without per-machine manual environment variables.

## What Changes

- Add environment-scoped default customer-auth base URLs to edge:
  - dev: `http://121.89.85.150:8088/capi`
  - ol: `https://aidcp.tommax.cc/capi`
- Resolve the customer-auth base URL from explicit config first, then baked
  package metadata, then the resolved cloud environment's default auth URL.
- Keep explicit `AIDCP_CLIENT_AUTH_URL` and persisted `clientAuthUrl` overrides.
- Update desktop build workflow/docs/tests so dev and ol builds bake a login
  address by default instead of only ol doing so.

## Impact

- `aidcp-edge`: Electron main auth resolution, package scripts, GitHub desktop
  build workflow, release docs, and focused Electron tests.
- No WebSocket protocol change.
- No cloud or console runtime change.
