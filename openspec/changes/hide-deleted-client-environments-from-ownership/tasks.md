## 1. Cloud behavior

- [x] 1.1 Filter `deleted` lifecycle rows from `GET /api/client-environments` while leaving `GET /api/environments` unchanged (`aidcp-cloud` `f287e52`, `src/panel/panel-server.ts`).
- [x] 1.2 Add a panel API regression test proving ownership candidates exclude deleted rows and environment assets retain them (`aidcp-cloud` `f287e52`, `test/panel-server.test.ts`).

## 2. Validation

- [x] 2.1 Run the focused panel server test for the changed endpoint behavior (`aidcp-cloud`: 1/1 passed).
- [x] 2.2 Run Cloud acceptance/full tests and typecheck with successful final exit status (`test:acceptance`: 186/186; `npm test`: 4151 passed, 11 skipped; `typecheck`: exit 0).

## 3. Delivery evidence

- [x] 3.1 Reconcile implementation and validation evidence in this checklist and pass `openspec validate hide-deleted-client-environments-from-ownership --strict` (exit 0).
- [x] 3.2 Commit and push the Cloud and control changes, deploy the integrated Cloud default branch to `dev`, and verify the documented service/listener/health checks. Cloud `f287e52` was pushed to `master`; control `774a4c10` was pushed to `main`. DEV was backed up at `/opt/aidcp/backups/deploy-20260804-092409-hide-deleted-ownership`, then only `src/panel/panel-server.ts` was synchronized (local/remote SHA-256 `d8c4e9a707032605cacf14b618cbb05d11080c34ad91d0c157a4a373984df5ab`) to avoid deploying unrelated Cloud mainline Facebook changes. Accordingly, DEV `.deploy-sha` remains `622a1af` and this is not a full `f287e52` snapshot deployment. Migration status was clean with 20 content, 57 automation, and 69 API migrations applied and zero pending. After restarting only `aidcp-cloud.service`, it was active with PID `1144450`, `NRestarts=0`; ports 8787/8088/8090/8091 listened; panel/client-auth/public API/Console health checks passed; PostgreSQL probes, schema gates, and the DEV writer-lock startup check passed. A signed read-only live probe returned 98 ownership candidates with zero deleted rows versus 99 asset rows with one deleted row. Feishu WS is disabled by DEV configuration, so no bot identity check applied. All unrelated `isales` services remained active. OL, Console, and Edge were untouched.
