## Why

Operators on fresh machines can hit AdsPower `user/create` failures such as `group is deleted or archived` when the desktop app reuses a stale or invalid dedicated group id. The current UI honestly shows the failure, but the operator is stuck unless they restart AIDCP or manually repair the AdsPower group.

## What Changes

- Treat AdsPower `group is deleted or archived` during environment creation as a recoverable dedicated-group failure.
- Clear the cached group id, re-resolve or recreate the dedicated group, and retry the environment creation once.
- Keep all other creation failures honest and non-retried.

## Impact

- Affected repo: `aidcp-edge`
- Affected areas: Electron AdsPower environment creation path and focused Electron tests.
- No cloud, protocol, database, or ECS deployment impact.
