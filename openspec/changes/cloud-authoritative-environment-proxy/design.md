## Context

`add-system-upstream-proxy-chain` made the user-entered environment proxy an Edge-local encrypted authority because AdsPower must be rewritten between the original proxy and a random GOST loopback. That model survives an ordinary Edge process crash only while the same `userData` remains available. It does not survive a new `AIDCP_USER_DATA_DIR`, another machine, or loss of the local record. In those cases, the existing bootstrap path can read a mutable AdsPower loopback and save it as the original proxy.

AIDCP Cloud already owns the environment registry, customer assignment, provisioning intent, and exact environment-scoped client authorization. The accepted product decision is that proxy type, host, port, username, and password may be stored as plaintext PostgreSQL columns. This decision intentionally permits database operators, backups, and read replicas to access directly usable proxy credentials; it does not permit those credentials to enter broad API projections or logs.

## Goals / Non-Goals

**Goals:**

- Make Cloud the only durable authority for every configured proxy and the complete original proxy configuration. Persist explicit `no_proxy` on AIDCP writes, while allowing a legacy AdsPower profile that is itself explicitly `no_proxy` to bypass the proxy subsystem without a Cloud row.
- Keep environment creation, proxy editing, preflight, AdsPower synchronization, and close restoration consistent with one explicit Cloud revision.
- Support machine/userData switching without importing an ephemeral AdsPower loopback as the original proxy.
- Give legacy valid Edge-local authorities a bounded one-time Cloud migration path.
- Keep exact credentials limited to an owned-environment read/write path and the existing private Edge → core pipe.
- Preserve truthful partial outcomes when Cloud and AdsPower cannot both be updated.

**Non-Goals:**

- Encrypt proxy authority columns at rest; plaintext storage is an explicit accepted decision.
- Add proxy authority to `/my-environments`, general environment lists, fleet snapshots, logs, errors, or Console list pages.
- Treat AdsPower's current configured profile value as original-proxy authority. The only permitted runtime classification is the credential-free fact that AdsPower explicitly reports `no_proxy`.
- Add automatic proxy-provider discovery, credential rotation, cross-customer sharing, or a new retry worker.
- Permit two installations to edit one authority without revision conflict detection.

## Decisions

1. **Store one explicit authority row per Cloud environment.**

   Add `client_environment_proxy_authorities` keyed by `env_key` with:

   - `state = configured | no_proxy`
   - nullable `proxy_type`, `proxy_host`, `proxy_port`, `proxy_user`, and `proxy_password`
   - monotonic `revision`
   - `source = provisioning | edge_edit | local_migration | admin`
   - `updated_by`, `updated_at`

   Checks require all route fields for `configured` and require them to be null for `no_proxy`. Missing row means `uninitialized` for a profile that AdsPower reports as proxy-configured; it does not force a legacy AdsPower `no_proxy` profile into the proxy subsystem. A separate table keeps broad `client_environments` queries credential-free and makes accidental `SELECT *` disclosure less likely.

2. **Keep plaintext at rest but narrow every projection.**

   PostgreSQL stores all proxy fields, including password, as plaintext per the accepted decision. The exact `GET/PUT /environments/:envKey/proxy-authority` routes recheck the logged-in client's ownership and never join into `/my-environments`. Responses, errors, audit text, logs, and tests must not echo credential values. The Cloud store returns exact credentials only to the authorized Electron main process.

   Reusing `provider_credentials` was rejected: its provider/field key space and runtime-only semantics do not model per-environment revisions, explicit no-proxy, or ownership. Encrypting only password was also rejected by the accepted plaintext decision.

3. **Use revision/CAS for all edits and migrations.**

   A new row is created with `expectedRevision = null`; updates require the exact current revision. Successful writes increment the revision and return the canonical authority. A mismatch returns `409 proxy_authority_conflict` with only the current revision, not credentials. This prevents silent last-writer-wins when two installations edit the same profile. Concurrent browser execution remains governed by existing AdsPower active-profile and Edge lifecycle gates; a durable runtime lease is excluded until a real cross-machine concurrent-start failure is observed.

4. **Persist creation authority atomically with Cloud environment provisioning.**

   `/environment-provisioning/complete` accepts a required normalized `proxyAuthority` object. `completeProvisioningIntent` writes environment registration, customer scope, slow-start state, and proxy authority in the same PostgreSQL transaction. An idempotent retry must match the previously committed authority; changing proxy payload while reusing an intent returns conflict.

   AdsPower creation still uses the user's original input first because `envKey` does not exist before `user/create`. If Cloud completion fails, Edge reports “created locally, Cloud authority not committed,” does not add the environment to the runnable roster, and does not claim full success.

5. **Cloud-first proxy editing with truthful partial state.**

   Editing is allowed only for an inactive, owned environment. Authority read failure never removes that repair entry: Electron opens a blank configured-proxy form with a warning and never projects malformed route or credential fields. When a malformed response still binds the exact environment and carries a valid positive revision, a repaired value may replace it using that revision; an unavailable authority or unusable revision keeps the editor open but makes save fail honestly. For a valid current authority, Electron submits the normalized new value with its revision. Only after Cloud success does it update AdsPower. If AdsPower fails, Cloud remains authoritative and the receipt says Cloud saved / AdsPower pending; the next start will apply Cloud. Rolling Cloud back was rejected because a failed compensating write could lose the user's newest intent.

6. **Read and freeze one Cloud snapshot for preflight and launch.**

   Before offline preflight or actual start, Electron obtains `{authority, revision}` from Cloud. Preflight cache entries include that revision. At start Electron rechecks Cloud; it may reuse a fresh preflight only when the revision matches, otherwise it invalidates and reruns. The same frozen authority feeds:

   - direct preflight and original-profile target when the switch is off;
   - GOST second hop, loopback preflight, and loopback profile target when the switch is on;
   - the private anonymous pipe delivered to the Edge core;
   - best-effort close restoration for that browser generation.

   AdsPower is read after an AIDCP write to verify the complete route. Before proxy-authority resolution it may also be read only to recognize explicit `no_proxy`; configured host, port, username, and password are never imported as the original.

7. **Fail closed on missing or unavailable Cloud authority.**

   AdsPower explicit `no_proxy` skips Cloud authority resolution, preflight, GOST, profile update, active-profile proxy restriction, and restore. For profiles AdsPower reports as proxy-configured, Cloud 404, authentication failure, timeout, malformed response, or ownership denial blocks preflight/start with a stable safe reason. There is no configured-route fallback to AdsPower current state. Explicit Cloud `no_proxy` also skips the proxy subsystem, including the partial-edit case where AdsPower has not yet adopted it.

8. **Use Edge local records only for bounded migration/cache.**

   When a proxy-configured profile's Cloud authority is uninitialized, Edge may upload an existing decryptable local `safeStorage` authority using create-only CAS. Loopback/localhost targets are never migratable. Missing, corrupt, or loopback local authority requires the user to re-save the original proxy. AdsPower explicit `no_proxy` needs no local migration. After Cloud acknowledges a configured revision, Edge may refresh its encrypted cache, but configured startup still requires an exact Cloud read and never treats the cache as a runtime fallback.

9. **Keep UI truth tied to Cloud authority and browser evidence.**

   Environment proxy summaries for configured profiles come from Cloud-safe type/host/port fields. AdsPower explicit `no_proxy` stays a local credential-free summary and exact editor result, so it cannot be replaced by an “authority uninitialized” error. Exact valid configured editor reads may include username/password for the selected owned environment. Missing, unavailable, or malformed configured reads open a blank repair form rather than blocking the editor; malformed fields are never reflected. Runtime status separately reports Cloud authority revision, chain preparation, preflight, and browser egress. A successful preflight does not become browser verification.

## Risks / Trade-offs

- [Plaintext proxy credentials are exposed by database access or backups] → Record the accepted boundary, isolate the table from list queries, restrict exact routes, redact logs/errors, and include credential-leak regression tests.
- [AdsPower creation succeeds but Cloud transaction fails] → Return a named partial result, keep the profile out of the runnable roster, and allow explicit retry/edit; never claim rollback or delete automatically.
- [Cloud edit succeeds but AdsPower update fails] → Keep Cloud authoritative, report partial application, and invalidate preflight. A configured proxy is reconciled from Cloud at the next start; explicit `no_proxy` still obeys the product rule that no-proxy startup does not mutate AdsPower, so the user must retry the failed edit sync before relying on that profile.
- [Two machines edit concurrently] → Require revision CAS and return a safe conflict; refresh before retry.
- [Cloud temporarily unavailable] → Block configured-proxy starts rather than use a stale local value; this trades availability for cross-machine authority correctness.
- [Cloud authority cannot be read for editing] → Preserve the owned inactive environment's editor as a blank repair surface. Save only when Cloud can accept a create or revision-bound replacement; never turn an unavailable or malformed value into an unversioned overwrite.
- [Legacy local record contains a stale GOST loopback] → Reject all loopback migration and require explicit re-entry.
- [Credentials leak through broad projections] → Separate table, exact DTOs, structural tests, and log/error redaction.

## Migration Plan

1. Add and migrate the Cloud authority table and exact owned-environment APIs in DEV; do not enable Edge Cloud-only reads before the migration and health checks pass.
2. Extend provisioning completion and Edge create/edit flows, initially retaining the local encrypted record as a migration/cache copy.
3. For each existing environment on first selected preflight/start:
   - AdsPower explicitly reports `no_proxy`: bypass proxy-authority resolution.
   - AdsPower reports a configured proxy and a Cloud row exists: use it.
   - Proxy-configured profile has no Cloud row and local authority is valid/non-loopback: upload with create-only CAS.
   - local authority missing/corrupt/loopback: block and require explicit proxy save.
4. Switch preflight/start/restore to frozen Cloud revisions and remove the AdsPower-current bootstrap path.
5. Validate creation, edit partial failure, machine/userData switching, revision conflict, no-proxy, GOST double-hop, browser egress, and close restoration against DEV.
6. Rollback Edge first to stop requiring the new API. Retain Cloud rows/table because deleting plaintext authority is irreversible operational data loss; a later authorized cleanup can remove them after export.

## Open Questions

- None. Cloud plaintext-at-rest authority, Cloud-first edit ordering, CAS conflict behavior, explicit missing/no-proxy distinction, and no AdsPower-current bootstrap are confirmed.
