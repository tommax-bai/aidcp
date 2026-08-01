## 1. Cloud customer schedule projection

- [x] 1.1 Add a pure customer schedule projector that converts effective active/content masks into clamped daily ranges, enabled customer action summaries, current/next windows and an explicit server timezone without exposing internal masks or account identity.
- [x] 1.2 Add focused projector tests for full-day active fallback, content fail-closed, cross-midnight/day ranges, content-within-active clamping, action labels and current/next boundaries.
- [x] 1.3 Add env-scoped `GET /environments/:envKey/schedule` to customer-auth with ownership/binding/platform gates and a minimal DTO; wire it to the production `ContentScheduleStore` and account platform source.
- [x] 1.4 Add customer-auth route tests for offline success, unsupported platform, binding failures, unavailable dependency, read-only behavior and response allowlisting.

## 2. Edge fixed customer data path

- [x] 2.1 Add a named `environment-schedule:get` IPC and preload method that accept only local envId, resolve profileId in main, and call the fixed customer-auth schedule path without requiring browser/core state.
- [x] 2.2 Add IPC and preload/security tests proving the fixed path, session handling, selected-environment validation and absence of renderer-controlled URL/token/accountId.

## 3. Xiaohongshu environment schedule UI

- [x] 3.1 Add the compact XHS-only “本周安排” entry to the environment homepage after runtime guidance and before 今日进展, covering loading, active/upcoming, empty, stopped and error summaries within the 64–72px height budget.
- [x] 3.2 Add an environment-scoped schedule workspace with back navigation, seven-day selection, activity/content ranges, enabled action summary, current/next status, today confirmed usage, retry and lifecycle-control delegation.
- [x] 3.3 Isolate state by envId/platform/request epoch, discard late responses, refresh at the minute boundary, exit on non-XHS switches and restore the environment-home scroll position on return.
- [x] 3.4 Add responsive/reduced-motion styling and focused renderer tests for placement, strict XHS gating, honest “可工作/工作中/已结束” semantics, switching, stale responses, empty/error states and no content-workspace coupling.

## 4. Validation, integration and delivery

- [x] 4.1 Run Cloud focused tests, full tests and typecheck; run Edge focused tests, full tests and typecheck.
  <!-- Cloud: focused customer schedule/auth tests 67/67; module-boundary tests 17/17; full suite 3,092 passed, 8 skipped, 0 failed; typecheck passed. Edge: focused schedule/security tests 22/22 after rebase; full suite 2,262/2,262; typecheck passed. Responsive browser QA passed at 1180px, 760px and 620px, with 620px document/shell/workspace width fixed at 620px and no horizontal overflow. -->
- [x] 4.2 Record Cloud/Edge commit SHAs and validation evidence in this task file, then run `openspec validate client-xhs-environment-schedule --strict`.
  <!-- Cloud commit 6c9ab00 (client-xhs-environment-schedule: expose customer schedule view). Edge rebased commit ac79920 (client-xhs-environment-schedule: add environment schedule workspace). Strict validation passed before integration. -->
- [ ] 4.3 Rebase/integrate clean feature branches into the latest default branches, rerun required validation, push Cloud/Edge/control defaults and deploy eligible Cloud runtime changes to DEV with backup and post-deploy checks.
  <!-- 2026-08-01 23:xx：**部署这一半今晚试过，主干在 dev 上起不来**，dev 已回滚到 `534af19` 保服务。
       根因在同步读自举链路（新流 DB 侧没备好），见 `docs/handoff-2026-08-02-round9.md` §1。本条不勾。 -->
  <!-- Integration complete: Cloud master 6c9ab00, Edge master ac79920, control main 40cc848. DEV deployment was attempted from clean Cloud master after backup at /opt/aidcp/backups/cloud-20260723-154625. The required read-only migration gate reported no schema_migrations ledger and 72 pending migrations; verify found 16 missing objects (the ledger plus publish_execution_state) and 0 extra objects. No restart occurred. Synced source was restored from backup, the service remained active, and 8787/8090 remained listening. Deployment stays incomplete until the separate migration baseline/missing-object review is completed. -->
- [ ] 4.4 Verify the DEV customer-auth schedule endpoint and served/runtime source boundaries, and record that installed Edge clients remain unchanged until a separately authorized package/release.
  <!-- Not yet served on DEV because 4.3 stopped at the migration gate. Edge source is merged only; no installer was built or installed, so installed clients remain unchanged. -->
