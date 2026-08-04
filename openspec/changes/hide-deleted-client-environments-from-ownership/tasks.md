## 1. Cloud behavior

- [x] 1.1 Filter `deleted` lifecycle rows from `GET /api/client-environments` while leaving `GET /api/environments` unchanged (`aidcp-cloud` `f287e52`, `src/panel/panel-server.ts`).
- [x] 1.2 Add a panel API regression test proving ownership candidates exclude deleted rows and environment assets retain them (`aidcp-cloud` `f287e52`, `test/panel-server.test.ts`).

## 2. Validation

- [x] 2.1 Run the focused panel server test for the changed endpoint behavior (`aidcp-cloud`: 1/1 passed).
- [x] 2.2 Run Cloud acceptance/full tests and typecheck with successful final exit status (`test:acceptance`: 186/186; `npm test`: 4151 passed, 11 skipped; `typecheck`: exit 0).

## 3. Delivery evidence

- [x] 3.1 Reconcile implementation and validation evidence in this checklist and pass `openspec validate hide-deleted-client-environments-from-ownership --strict` (exit 0).
- [ ] 3.2 Commit and push the Cloud and control changes, deploy the integrated Cloud default branch to `dev`, and verify the documented service/listener/health checks.
