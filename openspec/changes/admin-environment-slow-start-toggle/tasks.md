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

- [x] 4.1 Commit Cloud, Console, and control artifacts with validation evidence recorded in this task file <!-- cloud 74b5ce86c05baa02d539f5972d1c82b4e5782cea; console 708c75e9f086da4c51a4cec57d9f1e7894ead6ab; acceptance/full/typecheck/build pass; control commit records these artifacts -->
- [ ] 4.2 Rebase and fast-forward Cloud/Console default branches, push, and publish the Console build with the dev Cloud deployment
- [ ] 4.3 Verify dev service/listeners/health plus the authenticated environment read/write/readback path on an exact non-production Facebook environment
