## 1. Change setup and contracts

- [x] 1.1 Create isolated control, Cloud, and Edge worktrees on `codex/cloud-authoritative-environment-proxy`, preserving canonical checkouts
  <!-- control=/Users/baitianxing/codes/aidcp.wt/cloud-authoritative-environment-proxy; cloud=/Users/baitianxing/codes/aidcp-cloud.wt/cloud-authoritative-environment-proxy; edge=/Users/baitianxing/codes/aidcp-edge.wt/cloud-authoritative-environment-proxy; all on codex/cloud-authoritative-environment-proxy; canonical checkouts unchanged -->
- [x] 1.2 Validate the proposal, design, and capability deltas with strict OpenSpec validation
  <!-- validation: openspec validate cloud-authoritative-environment-proxy --strict (pass, 2026-07-27) -->

## 2. Cloud proxy authority

- [x] 2.1 Add the PostgreSQL proxy-authority schema, domain types, and revisioned read/write store operations
  <!-- aidcp-cloud: migration 0088 + ClientUserStore authority model/read/write CAS; table ownership, owner split list, schema max, and database-scope inventory updated -->
- [x] 2.2 Add exact customer-authenticated GET/PUT routes with ownership rechecks, optimistic revision comparison, and minimum-disclosure errors
  <!-- aidcp-cloud: exact /environments/:envKey/proxy-authority GET/PUT; customer ownership is rechecked in the store transaction and errors expose no credentials -->
- [x] 2.3 Extend provisioning completion to require and atomically persist configured or explicit no-proxy authority
  <!-- aidcp-cloud: provisioning completion writes environment, proxy authority, ownership, and intent completion in one PostgreSQL transaction; idempotent retry compares the persisted authority -->
- [x] 2.4 Add focused Cloud tests for ownership isolation, plaintext round-trip, no-proxy, stale revisions, idempotent provisioning, and credential-free projections/logs
  <!-- validation: 126 focused Cloud tests pass; full test/**/*.test.ts pass after table-owner/schema-version gates were updated; PostgreSQL integration assertions added but require the named integration database -->

## 3. Edge Cloud authority integration

- [x] 3.1 Add the exact Cloud proxy-authority client and normalized configured/no-proxy/revision model
  <!-- aidcp-edge: exact authenticated Cloud client plus environment-proxy-authority normalization module -->
- [x] 3.2 Persist creation authority through provisioning completion and implement Cloud-first existing-environment proxy edits
  <!-- aidcp-edge: create completion sends the original user input; single/batch edits CAS Cloud before AdsPower and return truthful partial receipts -->
- [x] 3.3 Replace AdsPower-derived authority reads with Cloud reads and a bounded safeStorage migration that rejects loopback/runtime endpoints
  <!-- aidcp-edge: no live AdsPower bootstrap remains; migration is create-only after explicit Cloud uninitialized and rejects localhost, 127/8, ::1, mapped loopback, and 0.0.0.0 -->
- [x] 3.4 Make proxy summaries, detection, preflight, and startup freeze one Cloud authority revision and bypass proxy gates for explicit no-proxy
  <!-- aidcp-edge: summaries are projected only after customer scope filtering; preflight cache and child authority pipe carry the same revision; actual spawn re-reads Cloud -->
- [x] 3.5 Synchronize AdsPower from the frozen authority for direct/GOST modes, require readback before launch, and restore the frozen original on close
  <!-- aidcp-edge: browser provider updates user_proxy_config, reads it back exactly, then starts; confirmed close restores the frozen original; no_proxy intentionally bypasses mutation -->
- [x] 3.6 Add focused Edge tests for alternate user-data directories, migration rejection, direct and double-hop synchronization, no-proxy bypass, unavailable authority, and partial save failures
  <!-- validation: full test/electron/*.test.ts exits 0; focused authority/preflight/browser-provider/management tests pass; Cloud authority path is independent of app userData while local storage remains migration/cache only -->

## 4. Validation and delivery

- [x] 4.1 Run focused Cloud tests and Cloud typecheck
  <!-- pass: 126 focused tests; full test/**/*.test.ts; npm run typecheck -->
- [x] 4.2 Run focused Edge tests and Edge typecheck
  <!-- pass: full test/electron/*.test.ts; npm run typecheck -->
- [x] 4.3 Re-run strict OpenSpec validation and record implementation commits, validation, deviations, and remaining live-acceptance boundaries
  <!-- implementation: aidcp-cloud@7edafae; aidcp-edge@36a62af. openspec validate cloud-authoritative-environment-proxy --strict passes. Deviation clarified: explicit no_proxy never mutates AdsPower on start, so a partial Cloud-only no_proxy edit requires an explicit retry. Remaining boundary: PostgreSQL/live AdsPower smoke is tracked by 4.5/4.6. -->
- [x] 4.4 Commit and push each feature branch, fast-forward integrate Cloud/Edge/control default branches, and rerun required post-integration validation
  <!-- default branches pushed: aidcp main@a2ffb20, aidcp-cloud master@7edafae, aidcp-edge master@36a62af. Post-integration strict OpenSpec, focused Cloud/Edge tests, and both typechecks pass. -->
- [x] 4.5 Deploy the Cloud runtime change to `dev` from a clean eligible checkout and verify service, listener, health, and PostgreSQL schema evidence
  <!-- DEV 121.89.85.150: backup /opt/aidcp/cloud.bak.20260727-042450Z.tar.gz, .env.bak.20260727-042450Z, and API schema dump cloud.schema.api.before-0088.20260727-042450Z.sql. Deployed aidcp-cloud@7edafae; applied API expand 0088 in 9ms; all owners pending=0 and verify missing=0. Stop/start only aidcp-cloud.service. active, NRestarts=0, 8787/8090/8091 listening, local/public panel and client-auth health ok, three owner SELECT 1 pass, enforce schema gate passes through API 0088, dev writer-lock count=1, Feishu WSClient onReady, no recent severe logs. -->
- [ ] 4.6 Perform a real Edge smoke test covering create/edit, direct mode, GOST mode, close restoration, and cross-`AIDCP_USER_DATA_DIR` authority consistency
  <!-- Partial live result 2026-07-27: a legacy no-proxy profile failed startup with proxy_authority_uninitialized and its editor showed an unknown read error. This is not accepted; 4.7 carries the fix and this end-to-end task remains open for rerun. -->
- [x] 4.7 Make legacy AdsPower `no_proxy` bypass Cloud proxy-authority checks, keep configured route fields non-authoritative, preserve the proxy editor as a blank repair surface for read/malformed failures, allow revision-bound malformed replacement, and add regression coverage
  <!-- aidcp-edge@bb9f7ac + 54005cd. Validation: 58 focused authority/management/preflight/runtime tests pass; npm run typecheck and node syntax checks pass. Configured startup remains fail-closed; only the owned inactive editor degrades to a blank repair form, and malformed replacement requires the returned valid revision. -->
