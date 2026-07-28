## Why

The original environment proxy is currently retained only in an Edge `userData`-scoped encrypted record while the AdsPower profile is rewritten to ephemeral GOST loopback endpoints during double-hop operation. Switching `AIDCP_USER_DATA_DIR`, moving to another machine, or starting from a profile left on a loopback can therefore lose the original route and misclassify a transient runtime value as authority.

## What Changes

- Make AIDCP Cloud the sole durable authority for every configured AdsPower proxy and persist explicit `no_proxy` for new/edited environments. A legacy profile that AdsPower itself reports as `no_proxy` bypasses proxy-authority checks because there is no original route to preserve.
- Save proxy authority when Edge completes environment creation and whenever an inactive environment's proxy is edited; reject launch when a configured environment has no usable Cloud authority.
- Fetch one exact Cloud proxy revision before preflight/start, freeze it for that browser generation, and use it to choose direct environment proxy or system-proxy → GOST → environment-proxy routing.
- Stop treating the mutable AdsPower profile as a source for the original proxy. Continue reading it to verify values Edge has just written and to recognize the credential-free `no_proxy` applicability state only.
- Route every AdsPower Local API request owned by one Electron desktop runtime through one main-process FIFO. Child proxy synchronization SHALL reserve one uninterrupted `user/update` → `user/list` batch so main-process refreshes cannot collide with the same device-level API limit.
- Treat Edge `safeStorage` records as migration/cache inputs only. Allow one-time upload of a valid non-loopback local authority, but never import a loopback from AdsPower as the original proxy.
- Add revision/CAS and environment ownership checks so multiple installations cannot silently overwrite each other's proxy authority.
- Keep proxy credentials out of environment lists, ordinary status projections, logs, errors, argv, and renderer-wide IPC despite plaintext-at-rest storage.

## Capabilities

### New Capabilities

- `cloud-environment-proxy-authority`: Cloud data model, exact environment-scoped APIs, revision semantics, migration, plaintext-at-rest boundary, and Edge consumption of the authoritative proxy.

### Modified Capabilities

- `adspower-environment-provisioning`: Environment creation and proxy editing must persist Cloud proxy authority with truthful partial-failure receipts.
- `client-customer-auth`: Owned-environment authorization must protect exact proxy authority reads and CAS writes without exposing credentials in list projections.
- `facebook-proxy-preflight`: Preflight must consume the same frozen Cloud authority revision used by the subsequent browser generation.
- `pluggable-browser-provider`: AdsPower remains an execution copy and readback gate, never an origin for reconstructing the original proxy.
- `edge-multi-instance-isolation`: Changing instance `userData` must not fork or replace the profile-scoped Cloud proxy authority.

## Impact

- **Cloud:** new PostgreSQL capability/table, client-auth API DTOs, ownership/CAS checks, provisioning transaction changes, tests, and DEV deployment.
- **Edge:** creation/edit synchronization, exact authority fetch, local migration/cache handling, preflight/start generation freeze, runtime-wide AdsPower API coordination, close restore source, renderer-safe status, and regression tests.
- **Control:** new cross-repository behavior contracts and migration/acceptance evidence.
- **Security/operations:** proxy credentials are intentionally plaintext at rest in PostgreSQL but remain excluded from list APIs and logs; database access and backups therefore gain direct access to usable proxy credentials.
