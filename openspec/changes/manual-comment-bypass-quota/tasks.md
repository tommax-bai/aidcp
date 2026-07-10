# Tasks

## 1. aidcp-cloud — thread manual override through the manual `/comment` path

- [x] 1.1 Add `manualOverride` to `triggerManual` options; set it only at the Feishu `/comment` handler (server.ts). <!-- aidcp-cloud cb0889a -->
- [x] 1.2 Group-join stage: add `{ manual }` opt to `triggerScheduled`; skip `canJoin` + `canUseSessionJoin` when manual; still record session-join on verified join. <!-- aidcp-cloud cb0889a -->
- [x] 1.3 Comment stage: skip `facebookCanComment` + comment daily cap when `manualOverride` (both plain `/comment` and post-`--join` in-group comment). <!-- aidcp-cloud cb0889a -->
- [x] 1.4 Ensure automatic paths (auto-comment loop, hot-lead auto-comment, background join loop) never carry the flag → quotas preserved. <!-- aidcp-cloud cb0889a -->

## 2. aidcp-cloud — tests

- [x] 2.1 Join scheduler: manual bypasses both join gates and still records session budget; auto path (no flag) still `quota_denied`. <!-- aidcp-cloud cb0889a -->
- [x] 2.2 Comment scheduler: manual override bypasses comment `canDo` + daily cap → `commented`; `--join` threads `manual:true` and in-group comment also bypasses; auto path (no flag) still `quota_denied`. <!-- aidcp-cloud cb0889a -->
- [x] 2.3 `npm run typecheck` + `npm run test:acceptance` + `npm test` green. <!-- aidcp-cloud cb0889a -->

## 3. Deploy + real-machine acceptance

- [x] 3.1 Deploy dev. <!-- 2026-07-10 deployed -->
- [ ] 3.2 Real-machine: `/comment FBProbe --join` on a real FB account whose session join budget is exhausted → actually joins + comments (no `session_budget` refusal). (real-machine backlog)
