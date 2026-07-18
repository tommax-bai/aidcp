## 1. Schema capability detection

- [x] 1.1 Add explicit full and legacy-read-only schema modes to `InteractionStore` initialization
  <!-- aidcp-cloud 5f11bd0: exact pre/post-0046 shapes classify as legacy_read_only/full. -->
- [x] 1.2 Reject missing base schema and partially applied migration `0046` shapes with distinct startup errors
  <!-- aidcp-cloud 5f11bd0: missing 0042 base and inconsistent 0046 shapes fail with distinct errors; no DDL. -->
- [x] 1.3 Add focused store initialization tests for full, legacy, missing-base, and inconsistent schema states
  <!-- aidcp-cloud 5f11bd0: schema-capability.test.ts covers all four states. -->

## 2. Runtime capability wiring

- [x] 2.1 Wire the detected schema mode into Cloud interaction runtime initialization and startup logging
  <!-- aidcp-cloud 5f11bd0: server startup retains the mode and reports the exact capability boundary. -->
- [x] 2.2 Force global outbound writes off in legacy-read-only mode while preserving configured read controls
  <!-- aidcp-cloud 5f11bd0: one effective write capability feeds both control projection and the final send gate. -->
- [x] 2.3 Add focused tests proving compatibility mode keeps reads available and blocks outbound work before attempt creation
  <!-- aidcp-cloud 5f11bd0: focused interaction tests passed 17/17. -->

## 3. Verification and delivery

- [x] 3.1 Run focused Cloud tests, Cloud typecheck, and strict OpenSpec validation
  <!-- Focused 17/17; acceptance 56/56; all 276 Cloud test files passed in Windows-safe batches; typecheck and openspec strict validation passed. -->
- [x] 3.2 Run repository change-risk and diff checks, then commit and push the control and Cloud changes through the default-branch workflow
  <!-- aidcp-cloud 5f11bd0 -> origin/master; aidcp d0910b9 -> origin/main; both ff-only after fetch/rebase, diff checks clean. -->
- [x] 3.3 Deploy dev Cloud without database DDL and verify interaction list/read-control APIs recover while outbound controls remain closed
  <!-- 2026-07-18 dev deployed aidcp-cloud 5f11bd0 from clean master. Windows ACL on isales-4.pem was tightened to TOM\tianx read/write only; Git Bash still reported synthetic 644, so the equivalent ACL facts were verified manually per deployment-environments.md. Backup: /opt/aidcp/backups/aidcp-cloud-20260718-165634.tgz + .env. Clean git archive SHA-256 matched before extraction; no package change, npm install, migration, or DDL. Restart 16:57:44 CST: active, NRestarts=0, 8787/8090/8091 listening, panel/console 200, PG select 1, Feishu ready, 4 isales services still running, no error entries. Startup reported legacy read-only mode with outbound writes forced closed. Authenticated GET for env k1eoujd8 returned 200, wechat_channels, active/applied, 2 items, commentsReadEnabled=true, dmReadEnabled=true. -->
