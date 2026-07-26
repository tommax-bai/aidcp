## Context

The development workstation is Windows and invokes extensionless deployment helpers through Git Bash. NTFS ACLs are the effective local access control, while `stat -c %a` can report a synthesized `644` mode that `chmod 600` cannot reliably change. Treating that synthesized mode as authoritative makes the preflight non-portable.

## Decisions

### Target checks identity and usability, not a synthesized mode

For both `dev` and `ol`, the helper verifies the fixed target metadata and that the configured private-key path is a readable regular file. It does not inspect group/other POSIX mode bits.

The SSH client remains responsible for any platform-native private-key checks. The repository still never records or copies key contents.

### Ol selection remains strict

This change does not broaden when `ol` can be selected or deployed. An explicit user request and the existing release-branch workflow remain mandatory.

### Other deployment gates remain unchanged

Clean eligible refs, backups, scoped rsync exclusions, service-specific restart, health checks, rollback, and the prohibition on touching colocated isales remain mandatory for `dev` and `ol`.
