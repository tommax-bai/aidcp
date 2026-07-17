## Why

Every Edge client is expected to create AdsPower profiles in the operator-provisioned `aidcp` group. Letting each client create a fallback group turns missing visibility, wrong runtime selection, and concurrent startup into ambiguous `group name repeat` failures.

## What Changes

- Use the existing AdsPower group named exactly `aidcp` for every programmatically created environment, regardless of platform.
- Stop Edge from calling `group/create`; a missing, unreadable, deleted, or archived pre-provisioned group becomes an actionable configuration failure.
- Re-resolve the same pre-provisioned group once when a cached group id becomes deleted or archived, without creating a replacement group.
- Remove `group/create` from the Electron AdsPower write-client allowlist and focused tests.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `adspower-environment-provisioning`: require all programmatically created AdsPower environments to use the pre-provisioned `aidcp` group and prohibit clients from creating groups.

## Impact

- Affected repo: `aidcp-edge`.
- Affected areas: Electron AdsPower environment group resolution, write-client allowlist, and focused Electron tests.
- No platform-specific branch, cloud protocol, database, deployment, or installer packaging change.
