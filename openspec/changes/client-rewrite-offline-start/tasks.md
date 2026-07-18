## 1. Contract and admission

- [x] 1.1 Confirm the existing persistent env-to-account binding and the current `binding_unverified` gate on client curated `create-post`.
- [x] 1.2 Define the offline rewrite boundary: persistent binding authorizes cloud-side `review` task creation; final platform dispatch still requires a live edge.
- [x] 1.3 Validate the OpenSpec change strictly before implementation. <!-- `openspec validate client-rewrite-offline-start --strict` passed before code changes. -->

## 2. Cloud implementation

- [x] 2.1 Create the isolated `aidcp-cloud` worktree and branch named `client-rewrite-offline-start`.
- [x] 2.2 Remove live-binding attestation only from the curated `create-post` route while preserving binding resolution, server-owned account targeting, and fixed `review` mode.
- [x] 2.3 Update comments so generation, pending approval, and final platform dispatch boundaries are explicit and do not claim offline publishing.

## 3. Regression coverage and validation

- [x] 3.1 Change the offline client-auth regression to prove curated rewrite creates one task for the persistently bound account without a live browser.
- [x] 3.2 Preserve a focused assertion that the generic client delegated publish-task route remains `binding_unverified` and creates no additional task while offline.
- [x] 3.3 Run focused client-auth tests, acceptance tests, the full cloud test suite, and typecheck. <!-- focused 28/28; acceptance 56/56; explicit Windows full-suite invocation 2473 pass, 8 skipped, 0 fail; typecheck exit 0. The package `npm test` glob itself discovers 0 tests under Windows, so full validation used an explicit recursive test-file list. -->
- [x] 3.4 Run `openspec validate client-rewrite-offline-start --strict` after implementation and record concrete validation evidence. <!-- strict validation passed after code and test changes. -->

## 4. Integration and development deployment

- [x] 4.1 Commit the cloud worktree change, rebase onto the latest `origin/master`, rerun required validation, and fast-forward it to `aidcp-cloud/master` without force push. <!-- aidcp-cloud `5c17e3e`; pushed to `origin/master`; integration rerun: acceptance 56/56, explicit Windows full suite 2473 pass / 8 skip / 0 fail, typecheck exit 0. -->
- [x] 4.2 Commit and push the OpenSpec change with repo SHA and validation evidence recorded in this file. <!-- aidcp control commit `29e4ea4` pushed to `origin/main`; final deployment evidence follows in the archival commit. -->
- [x] 4.3 Deploy the clean integrated cloud `master` to `dev` following the named-target checklist; verify service, listener, health, Feishu, and PostgreSQL, or roll back on failure. <!-- Deployed clean `aidcp-cloud/master` batch at `a38bcfb`, which contains this change `5c17e3e`; backup `/opt/aidcp/backups/cloud-20260718-162530`; only `aidcp-cloud.service` restarted. Verified service active, listeners 8787/8090/8091, panel and client-auth health `ok:true`, PostgreSQL accepting connections, Feishu WS onReady, and deployed source marker present. `deploy-target --check` reports Unix 644 on Windows NTFS; Windows ACL was tightened to current-user read plus SYSTEM/Administrators and manually verified per deployment doc's equivalent-check allowance. -->
- [x] 4.4 Register any required real-machine check in the shared acceptance backlog; do not claim browser-offline client behavior verified without a real client request. <!-- Registered cluster 105 for offline rewrite creation, pending approval truth, final live-edge dispatch gate, and binding failures. -->
