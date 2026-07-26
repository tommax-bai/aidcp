## 1. Admission and isolated worktrees

- [x] 1.1 Create `codex/split-cloud-api-composition-root-3a` worktrees for every owning repo that changes; keep canonical control on `main` and sibling canonicals on `master`, preserve unrelated worktrees, and install physical dependencies where required.
  <!-- aidcp/aidcp-cloud/aidcp-transport/aidcp-automation/aidcp-api/aidcp-kernel isolated worktrees created from current origin defaults. aidcp-cloud npm ci passed; the other four hit observed npm.zhaopin.com ECONNRESET and received physical copies of their canonical node_modules, verified as non-symlink directories. -->
- [x] 1.2 Record the read-only baseline: `sync-split-repos` differs only at hand-written composition roots, `AC-BOUND` / `AC-OWN` counts are zero, acceptance is green, and current kernel/transport pins are aligned.
  <!-- aidcp-cloud@031e58e: acceptance 123 pass / 0 fail; AC-BOUND crossBoundaryEdges=0 and AC-OWN crossLayerWrites=0/crossLayerReads=0. sync-split-repos confirmed source, migrations, kernel 32868ff and transport 9d62678 pins aligned; only expected hand-written composition roots differ. -->

## 2. Canonical owner contracts in aidcp-cloud

- [x] 2.1 Make the four kernel `Panel*Config` read methods explicitly asynchronous and make the local facades plus four panel request handlers await-safe; preserve facade behavior and add focused compatibility tests.
  <!-- aidcp-cloud worktree: four kernel getters now return Promise, four owner facades return async truth, and four panel GET handlers await. Focused config/mirror/panel tests 65 pass / 0 fail; npm run typecheck exit 0. -->
- [x] 2.2 Implement `panel-automation-http.ts` with all six `PanelAutomationReader` methods, route/client parity, filters, and failure-not-empty tests.
  <!-- aidcp-cloud worktree: six routes + typed client; optional filters and missing projection rows preserved. Focused tests 5 pass / 0 fail; owner error codes propagate instead of zero/empty success; typecheck exit 0. -->
- [x] 2.3 Implement `panel-config-http.ts` for quota/pacing/session/resume read and write methods; prove validation rejects stay structured, writes return owner truth, and remote failures never return defaults/stale views.
  <!-- aidcp-cloud worktree: eight routes + four typed clients. Round-trip/failure tests 2 pass / 0 fail; validation reason, updatedBy, optional fields and owner truth preserved; typecheck exit 0. -->
- [x] 2.4 Implement `facebook-group-ops-http.ts` for list/facets/enable/progress/assignments/reclaim plus single/batch scope counts and recent scheduled results; explicitly encode Maps as stable JSON arrays. Exclude `importTargets` / `replaceTargetScopes` until the 4a account-roster port is paired, with tests proving the partial port is not injected as a complete panel dependency.
  <!-- aidcp-cloud worktree: ten-method partial port + HTTP adapter; import/replace excluded, optional args preserved, two batch Maps encoded as entries and rebuilt client-side. Focused tests 5 pass / 0 fail; typecheck exit 0. -->
- [x] 2.5 Implement `group-route-http.ts` with `getRoute(groupLabel)` / `listRoutes` / `setRoute`; preserve null-as-unconfigured separately from transport/owner failure.
  <!-- aidcp-cloud worktree: three-method route/client; legitimate null, explicit clear, business rejection, malformed write and owner/transport failure remain distinct. Focused tests 5 pass / 0 fail. -->
- [x] 2.6 Implement `alert-resolution-http.ts` over `AlertResolutionPort.resolveById`; preserve true `0 | 1` results and prove the adapter has no risk-state or Edge-resume path.
  <!-- aidcp-cloud worktree: single-method route/client preserves at=0 and real updated-row count; malformed input and owner/transport failures remain errors. Focused tests 4 pass / 0 fail. -->
- [x] 2.7 Register the five route groups on the existing automation internal HTTP server using only automation-owned stores/facades; do not add api/content pools, retries, fallbacks, public routes, or schema changes.
  <!-- aidcp-cloud worktree: existing automation listener now registers panel automation/config, narrowed Facebook ops, optional group route and optional alert resolution. Missing risk registry no longer prevents unrelated owner routes from starting; source guard test passes. -->
- [x] 2.8 Add direct HTTP contract tests for success, business rejection, malformed/optional payloads, non-2xx propagation, bounded timeout, and serialization fidelity across all five members.
  <!-- aidcp-cloud worktree: five transport suites total 21 pass / 0 fail; universal InternalHttpClient bounded timeout remains the shared mechanism, with no member-specific retry/fallback. npm run typecheck exit 0. -->

## 3. Server-first validation and dev delivery

- [x] 3.1 In `aidcp-cloud`, run focused transport/panel/config/Facebook/group/alert tests, `npm run test:acceptance`, full `npm test`, and `npm run typecheck`; confirm `AC-BOUND-*` / `AC-OWN-*` remain zero.
  <!-- aidcp-cloud worktree: focused server/transport 27 pass; acceptance 123 pass; full suite 3401 pass / 0 fail / 11 skipped; typecheck and diff-check pass. AC-BOUND crossBoundaryEdges=0; AC-OWN crossLayerWrites=0/crossLayerReads=0. -->
- [x] 3.2 Commit the server-first `aidcp-cloud` slice with explicit pathspecs, push its feature branch, rebase/validate, fast-forward `master`, and push `origin/master`.
  <!-- aidcp-cloud@5b35d0a pushed on feature branch, typechecked after rebase, then fast-forwarded and pushed to origin/master. -->
- [x] 3.3 Read `docs/deployment-environments.md`, run `scripts/deploy-target dev --check`, back up and deploy the clean eligible default checkout, then verify monolith service/listeners/health/schema gates/Feishu/PostgreSQL/logs and confirm automation port 8093 remains closed; use the direct loopback HTTP contract suites as the five route-group evidence, because monolith intentionally does not start the automation internal listener.
  <!-- dev 121.89.85.150: backed up /opt/aidcp/cloud.bak.20260726-142613.tar.gz, deployed clean aidcp-cloud@5b35d0a (server.ts SHA-256 matches local), migration status content 20/20 automation 43/43 api 53/53 with 0 pending, restarted only aidcp-cloud.service. Service active; :8787 and :8090 listen; GET /api/health={"ok":true}; :8093 remains closed; enforce schema gates, automation writer lock, RiskControllerRegistry, panel and Feishu WS all report healthy. Five route groups are proven by 21 direct loopback HTTP contract tests, not by a nonexistent monolith listener. -->

## 4. Shared transport publication and derived repos

- [x] 4.1 Add exactly the five files to `TRANSPORT_MEMBERS`; update package exports/build coverage without admitting private outbox/account-projection transport files.
  <!-- control worktree adds exactly panel-automation, panel-config, facebook-group-ops, group-route and alert-resolution to TRANSPORT_MEMBERS. aidcp-transport@b754bc8 builds all five under wildcard exports; runtime import probe resolves 5/5. -->
- [x] 4.2 Sync the canonical source and relevant tests into isolated `aidcp-transport` / `aidcp-automation` worktrees; keep automation on its local `src/transport` copy and update exact transport pins only in real consumers.
  <!-- Isolated worktrees carry canonical owner source/tests with kernel imports rewritten to aidcp-kernel. automation keeps local transport source and only updates kernel; api/content pin aidcp-transport@b754bc8 and all three pin aidcp-kernel@f7bceaf. -->
- [x] 4.3 Run `aidcp-transport` build/typecheck/tests plus focused client tests and typecheck in each changed consuming repo; prove exports resolve to built files and pin/source drift is rejected.
  <!-- aidcp-transport build/typecheck and 5/5 export probe pass. api focused 24/24 + strict slice tsc pass; automation focused 62/62 + strict slice tsc pass; content full 438/438 + full typecheck pass. Honest existing extraction gates remain: api full test 404/409 (5 missing src/soul/soul.yaml asset failures) and full typecheck cannot resolve the unrewritten monolith root; automation full test 1597/1626 (26 stale migration/boundary-fixture failures including risk_command_outcome) and full typecheck likewise fails on the unrewritten root. These are not widened or labeled green; api/automation main() remain this change's explicit non-goal. -->
- [x] 4.4 Commit and push each derived repo feature branch, serialize rebase/fast-forward integration into the latest default branches, rerun validation, and push defaults without force or non-fast-forward history.
  <!-- aidcp-kernel@f7bceaf, aidcp-transport@b754bc8, aidcp-api@72858c9, aidcp-automation@7c7848f and aidcp-content@c023f70 were rebased, scoped gates rerun, then fast-forwarded and pushed to origin/master in dependency order. No force/non-FF history. api/automation whole-repo pre-existing red gates remain recorded under 4.3 and are not claimed green. -->

## 5. Documentation and closeout

- [x] 5.1 Update `docs/cloud-composition-root-trisection.md` §10 with the resolved config-facade decision, exact 3a method surface, delivered repo SHAs, dev evidence, and the honest boundary that api `main()` / three-process communication remain unverified.
  <!-- §10.4/10.6/10.7 corrected and §10.8 added: 5 contract groups / 28 methods, Facebook import/scope writes deferred to 4a, six delivered repo SHAs, validation and DEV monolith evidence recorded. :8093 closed and api main/three-process communication remain explicitly unverified. -->
- [x] 5.2 Run `scripts/sync-split-repos` in its default read-only check mode, reconcile any non-composition drift, and record the final seven-repo source/pin/migration result without treating expected hand-written roots as syncable.
  <!-- AIDCP_CODES_ROOT=/Users/baitianxing/codes sync-split-repos --ref aidcp-cloud@5b35d0a: api 105/105, automation 203/203, content 83/83, kernel 90/90 and transport 33/33 with zero non-composition source drift; pins align to kernel f7bceaf / transport b754bc8 and migrations align 53/43/20. Exit 1 is solely the expected api/automation/content hand-written server/index roots, reported but never auto-synced. -->
- [x] 5.3 Run `openspec validate split-cloud-api-composition-root-3a --strict`, update every completed task with concise `<!-- repo sha validation/deployment/deviation -->` evidence, commit/push the control worktree, fast-forward `main`, and push `origin/main`.
  <!-- aidcp@281c429: rebased onto current origin/main, strict OpenSpec validation and diff-check passed, feature branch pushed, then canonical main fast-forwarded and origin/main pushed without force. This closeout evidence is committed and pushed immediately after the recorded integration. -->
