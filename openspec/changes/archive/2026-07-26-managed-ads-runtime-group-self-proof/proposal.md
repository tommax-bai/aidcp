## Why

The desktop client can successfully start or adopt an AdsPower CLI daemon yet send environment-creation requests to a stale user-configured API base, or reuse a daemon whose visible group namespace does not contain the required `aidcp` group. This produces a misleading “group missing” failure even though the bundled runtime selected a valid fallback port, so managed runtime routing and group visibility need an explicit self-proof and bounded recovery contract.

## What Changes

- Make the runtime base resolved by the managed AdsPower CLI authoritative for environment-creation reads and writes; legacy renderer/settings API-base values cannot redirect a managed create request to a foreign daemon.
- Before the first managed runtime start in each desktop-app session, use the bundled CLI's own `status`/`stop` control path to stop any registered leftover CLI daemon, verify bounded completion, and then start a fresh daemon with the current managed configuration.
- Treat exact visibility of the pre-provisioned `aidcp` group on that freshly established runtime as the creation self-proof before `user/create`.
- Fail closed with a specific actionable receipt when the registered daemon cannot be stopped or the freshly started daemon still cannot see `aidcp`.
- Never scan for, signal, or terminate the independent AdsPower desktop application or arbitrary processes by name.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `adspower-environment-provisioning`: environment creation uses the managed runtime's resolved base and requires a bounded pre-provisioned-group self-proof/recovery before any AdsPower write.

## Impact

- **aidcp-edge:** `src/electron/main.cjs`, AdsPower runtime/group-resolution helpers, and focused Electron runtime/provisioning tests.
- **OpenSpec:** strengthens the existing AdsPower environment-provisioning contract and explicitly supersedes the assumption that any reachable differently-started CLI daemon is automatically safe for creation.
- **User impact:** a leftover CLI daemon cannot silently carry stale port/account state into a new AIDCP session, stale local API settings no longer cause silent routing, and failed daemon reset is reported before any environment is created.
