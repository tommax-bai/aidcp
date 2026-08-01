## 1. Deployment script repair

- [x] 1.1 Brace every deployment-script variable that is immediately followed by non-ASCII text.
- [x] 1.2 Add a focused source contract test for hazardous unbraced localized expansions.

<!-- Evidence: aidcp-cloud b4694df fixes all six matching expansions and adds the lexical regression test. No topology or fallback behavior changed. -->

## 2. Validation and delivery

- [x] 2.1 Run the focused test, Bash syntax check, Cloud typecheck, and strict OpenSpec validation.
- [x] 2.2 Commit, rebase, fast-forward integrate, and push Cloud and control changes.
- [ ] 2.3 Deploy the integrated Cloud default branch to DEV with the three-process script and verify content, automation, API, ports, schema, PostgreSQL, Feishu, and unrelated-service isolation.
  <!-- 2026-08-01 23:xx **主动不做，卡点已坐实（不再是「没人试过」）。** -->
  - **前置未满足**：`split-cloud-automation-production-runtime` 的 tasks.md 明写
    「`aidcp-api` 的手写入口**还没构造** Facebook 运营策略存储，故它今天供的是一个当场抛具名错误的实现。
    **三进程真跑之前必须补上**，否则 automation 拉这条流会拿到 502」。
    今天切三进程 = 把这条流打成 502，**那不是「脚本能不能跑」的问题，是上游能力缺口**。
  - 脚本本身**探测过是好用的**：`deploy-multi.sh dev check`（纯探测、不改状态）通过，
    报「SSH 可达、目录与 .env 就位、选择器已识别 automation / api」。
  - **另一个必须先解的**：主干目前在 dev 上**单体形态都起不来**（同步读自举，见
    `docs/handoff-2026-08-02-round9.md` §1），切拓扑之前先让单体能起。
  - dev 当前 = 单体拓扑跑 `534af19`（回滚保服务），多服务单元文件已备但未启用。

<!-- Validation: focused deployment contract 1/1, bash syntax and lexical scans, Cloud typecheck, and strict OpenSpec validation passed. Cloud b4694df and control 1fdb1fd were rebased, fast-forward integrated, and pushed without force. DEV deployment remains pending. -->

<!-- DEV attempt 2026-07-26: the repaired script completed backup, source sync, dependency install, capability probe, unit install, content health, and automation :8787 health. API then started :8091/:8094 but refused panel :8090 with `composition_dependency_unavailable: server` because the panel still requires automation-owned composition state. The script failed closed and automatically restored the monolith; aidcp-cloud.service is active/enabled with NRestarts=0 and :8787/:8090/:8091, schema gates, PostgreSQL, writer lock, outbox worker, reconciler, and Feishu healthy. Task 2.3 remains open: source segmentation does not yet prove a deployable three-process runtime. -->
