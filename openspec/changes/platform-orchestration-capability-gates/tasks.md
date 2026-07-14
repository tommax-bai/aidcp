## 1. aidcp-cloud — Capability words + wired consumers

- [ ] 1.1 Add `follow` / `profile_visit` / `patrol` / `notification` to the `capabilities` Record in `src/platform/registry.ts` (same shape as C1a), with XHS supported and Facebook `{false,reason}`.
- [ ] 1.2 Gate `RoleDispatcher.setup()` role registration: patrol/notification capability decides whether the 12 patrol roles register; follow/profile_visit decides whether AuthorEvaluator/FollowAgent register.
- [ ] 1.3 Gate is fail-open: only an explicit `supported===false` skips registration; a missing entry or exception registers as today (never silently drop XHS patrol on a lookup failure).

## 2. Verification

- [ ] 2.1 Cloud unit tests: XHS registration snapshot asserts all 12 patrol roles + AuthorEvaluator/FollowAgent still register (do not push this XHS regression onto zero-coverage real machine); Facebook `patrol.supported===false` ⇒ patrol roles not registered; lookup miss/exception ⇒ registers as today.
- [ ] 2.2 `npm run test:acceptance` → `npm test` → `npm run typecheck`.
- [ ] 2.3 Rebase (serialize on `role-dispatcher.ts` after other FB changes settle), integrate, push cloud to `master`, deploy dev.

## 3. Change Record

- [ ] 3.1 Update this task record with commits and validation; `openspec validate platform-orchestration-capability-gates --strict`.
