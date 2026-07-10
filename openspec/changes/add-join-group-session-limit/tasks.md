## 1. Cloud Session Budget Contract

- [x] 1.1 Add `join_groups` to `SessionInteractionBudget`, defaults, config store schema, migration/self-heal DDL, panel API patch parsing, and related tests. <!-- aidcp-cloud 918f62fe35a71eb41c07fbdf8520103600807d9b -->
- [x] 1.2 Add runtime session-budget adapter support for `join_group` so the scheduler can check and consume the active account session budget. <!-- aidcp-cloud 918f62fe35a71eb41c07fbdf8520103600807d9b -->

## 2. Cloud Facebook Join Scheduler

- [x] 2.1 Gate real Facebook group-join dispatch on remaining single-session `join_groups` budget and record an honest non-success result when exhausted. <!-- aidcp-cloud 918f62fe35a71eb41c07fbdf8520103600807d9b -->
- [x] 2.2 Consume `join_groups` only after judgment-confirmed successful join, and cover skip/failure paths with scheduler tests. <!-- aidcp-cloud 918f62fe35a71eb41c07fbdf8520103600807d9b -->

## 3. Console Admin

- [x] 3.1 Add "加群" to the "单场会话上限" table, save payload, API types, validation copy, and quota page tests. <!-- aidcp-console 901dc228981c5d7326272ee12f7e3fa17e367b99 -->

## 4. Validation, Release, Deployment

- [x] 4.1 Run OpenSpec validation plus targeted/full cloud and console validation. <!-- validations passed: openspec validate add-join-group-session-limit --strict; aidcp-cloud npm run test:acceptance, npm test, npm run typecheck; aidcp-console npm run typecheck, npm test, npm run build -->
- [x] 4.2 Commit and push the control/cloud/console changes to their default branches. <!-- pushed: aidcp-cloud master 918f62fe35a71eb41c07fbdf8520103600807d9b; aidcp-console master 901dc228981c5d7326272ee12f7e3fa17e367b99; aidcp main 5e929a2a79bcecc6e1e68671d37488b7c13581db -->
- [x] 4.3 Deploy cloud and console to dev, then verify health and static asset behavior. <!-- 2026-07-10 dev: backups cloud.bak.20260710-110302.tar.gz, cloud/.env.bak.20260710-110302, console.bak.20260710-110302.tar.gz; rsynced cloud master to /opt/aidcp/cloud and console dist to /opt/aidcp/console; restarted aidcp-cloud.service; checks passed: service active, /api/health ok, 8787 returns 426, 8090/8787/8088 listening, session_config_global.budget_join_groups default 1, public console 200, assets/index-CytJQenX.js contains join_groups and 加群, PG ready, Feishu WSClient onReady, recent logs no errors -->
