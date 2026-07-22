## Why

`scripts/deploy-target dev --check` currently interprets the Git Bash/NTFS mode reported for `~/codes/dev-0722.pem` as a POSIX permission mode. On Windows this can remain `644` even when the Windows ACL only grants the current user access, so a safe and usable development key is rejected before SSH is attempted. This blocks high-frequency `dev` deployment without adding a reliable security signal.

## What Changes

- The `dev` and `ol` preflights continue to verify the named target, fixed host, key path, file existence, and readability.
- Neither target rejects the key based on the POSIX group/other mode reported by Git Bash on Windows.
- The authoritative deployment documentation and helper documentation describe the target-specific behavior.

## Impact

- Affected spec: `deployment-environments`
- Affected files: `scripts/deploy-target`, `scripts/README.md`, `docs/deployment-environments.md`
- No ECS target, service, credential value, runtime, or application authorization rule changes.
