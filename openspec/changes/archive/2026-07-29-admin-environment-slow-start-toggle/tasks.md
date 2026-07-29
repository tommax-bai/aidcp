## 1. OpenSpec contract

- [x] 1.1 Add admin environment lifecycle and internal Panel API delta requirements for the environment slow-start toggle
- [x] 1.2 Run `openspec validate admin-environment-slow-start-toggle --strict` <!-- 2026-07-28: pass -->

## 2. Cloud internal API

- [x] 2.1 Extend the environment asset DTO/query with authoritative slow-start configuration
- [x] 2.2 Add the admin-only environment slow-start conditional write, idempotent anchor preservation, mirror refresh, and stable rejection reasons
- [x] 2.3 Add the Panel `PUT /api/environments/:envKey/slow-start` route with strict body/JWT handling and global-disable projection
- [x] 2.4 Add focused store and Panel route tests for unbound enable, repeated enable, disable, unsupported targets, invalid bodies, and global-disable truth
- [x] 2.5 Run focused Cloud tests and `npm run typecheck` <!-- 2026-07-28: client-user-store + panel-server 84/84 pass; typecheck pass -->

## 3. Console environment toggle

- [x] 3.1 Extend Console API types and add the environment slow-start mutation/cache refresh
- [x] 3.2 Add the Facebook active-environment switch, pending state, global-disable truth, unsupported states, and failure feedback to the environment page
- [x] 3.3 Add focused page tests for success, pending, rollback, global disable, and unsupported rows
- [x] 3.4 Run focused Console tests and `npm run typecheck` <!-- 2026-07-28: EnvironmentsPage 6/6 pass; typecheck pass -->

## 4. Integration and dev verification

- [x] 4.1 Commit Cloud, Console, and control artifacts with validation evidence recorded in this task file <!-- cloud d937c2be639382fab3be8a0c7bddc96494f9e63f; console 708c75e9f086da4c51a4cec57d9f1e7894ead6ab. Cloud acceptance/focused 84/84/full/typecheck pass. Console focused 6/6, serial full 288 pass + 1 skipped, typecheck/build pass. OpenSpec strict validation pass. -->
- [x] 4.2 Rebase and fast-forward Cloud/Console default branches, push, and publish the Console build with the dev Cloud deployment <!-- 2026-07-28 DEV 121.89.85.150: Cloud/Console default branches were clean, fast-forwarded and pushed at the SHAs in 4.1; deploy-target check passed. Backups: /opt/aidcp/cloud.bak.20260728-130453.tar.gz, /opt/aidcp/cloud/.env.bak.20260728-130453, /opt/aidcp/console.bak.20260728-130453.tar.gz. Only the four changed Cloud runtime files and the canonical Console dist were synced; remote hashes matched local and Console served assets/index-pMGf2ak3.js. Migration status remained content 20/20, automation 51/51, api 59/59, all pending=0. Only aidcp-cloud.service was stopped and started; OL was not touched. -->
- [x] 4.3 Verify dev service/listeners/health plus the authenticated environment read/write/readback path on an exact non-production Facebook environment <!-- aidcp-cloud.service active with NRestarts=0; 8787/8090/8091 and Console 8088 listening; Panel and customer-auth health returned ok; all three PostgreSQL owners passed SELECT 1; enforce schema gates, target=dev automation writer lock and Feishu WS onReady were confirmed; isales-api/isales-scheduler remained active. Authenticated acceptance used exact active, unbound Facebook environment k1f43l0k (Facebook import 3): baseline disabled/since=null, enable response and GET readback agreed on one non-null anchor, disable response and GET readback returned disabled/since=null, and direct API-owner DB read confirmed the original null state was restored. -->
