## Context

The shared AdsPower account now has an operator-provisioned group named exactly `aidcp`. Edge currently looks for `aidcp-创建`, creates it when absent, and retries a create after a list miss. That fallback conflates an absent group with a failed list, wrong local runtime, insufficient group visibility, and concurrent clients.

Environment provisioning is platform-neutral at this layer: Facebook, Xiaohongshu, WeChat Channels, and future platform choices all pass through the same `createEnvironmentWithGroupRecovery` service before `user/create`.

## Goals / Non-Goals

**Goals:**

- Resolve the exact pre-provisioned `aidcp` group and pass its id to every `user/create` request.
- Fail closed with an actionable error when the group cannot be listed or found.
- Re-resolve once after AdsPower rejects a cached group id as deleted or archived.
- Remove group creation from the desktop write surface.

**Non-Goals:**

- Creating, renaming, restoring, or authorizing AdsPower groups from Edge.
- Using AdsPower groups as customer-ownership records.
- Changing platform-specific environment payloads, cloud protocol, or desktop packaging.

## Decisions

### Resolve by exact name instead of hard-coding a group id

The resolver will use `group/list` and match the exact name `aidcp`. Group ids can change after operator repair, while the pre-provisioned name is the stable contract. The resolved id remains cached for the process lifetime to preserve the existing low-call behavior.

Alternative considered: package the current group id. Rejected because deletion and recreation would require a client release even though the operational name did not change.

### Treat missing or unreadable group state as configuration failure

If `group/list` fails, Edge returns that list failure. If the list succeeds without `aidcp`, Edge returns an actionable missing-group error. It MUST NOT call `group/create` in either case.

Alternative considered: generate a suffixed fallback group. Rejected because it hides wrong-runtime and permission problems and fragments environments across groups.

### Keep one bounded stale-id retry

If `user/create` reports that the cached group is deleted or archived, Edge clears the cache, excludes the failed id, re-lists `aidcp`, and retries `user/create` once only when a different current id is visible. It never creates a replacement.

### Remove `group/create` from the write-client allowlist

The environment flow no longer needs a group write. Removing the endpoint and convenience wrapper structurally enforces the new contract instead of relying on call-site discipline.

## Risks / Trade-offs

- [The `aidcp` group is missing or hidden from the runtime identity] → Stop before `user/create` and tell the operator to check the AdsPower runtime, API key, and group permission.
- [The group is deleted while a client holds its cached id] → Re-resolve once and use a replacement `aidcp` id only if the operator has already provisioned it.
- [Legacy clients still create `aidcp-创建`] → New clients ignore that legacy group; no destructive migration or automatic profile moves are performed.
- [A wrong AdsPower account also contains a group named `aidcp`] → This change narrows the symptom but does not prove runtime identity; runtime/key identity verification remains separate work.

## Migration Plan

1. Confirm the shared AdsPower account exposes the pre-provisioned `aidcp` group to the shared runtime identity.
2. Release the Edge code change after focused and full validation.
3. Existing profiles remain in their current groups; only newly created profiles use `aidcp`.
4. Rollback is the previous Edge version; no data migration or server rollback is required.

## Open Questions

None for implementation. Moving existing profiles into `aidcp` is intentionally outside this change.
