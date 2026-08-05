# Tasks — scope-risk-reconcile-to-owned-accounts

## 1. aidcp-cloud — 对账范围按归属收敛

- [x] 1.1 给对账器加窄归属依赖 `ownerTargetFor(accountId)` 与本进程 `executionTarget`，三态分别落成「对账 / 跳过(他 target) / 跳过(未知)」；读失败不中断整轮，计入未知。 <!-- aidcp-cloud ec71ef1 -->
- [x] 1.2 `runOnce` 返回值携带四个计数（已物化 / 实际对账 / 他 target 跳过 / 未知跳过）；`已物化>0 且 实际对账=0` 时 warn 级响亮记录。 <!-- aidcp-cloud ec71ef1 返回类型由 ReconcileDrift[] 改为 ReconcileRound，调用点与用例同批更新 -->
- [x] 1.3 装配处注入归属读口（复用风控条件写在用的那一个，MUST NOT 另起读法）；归属口缺席时保持全量对账并在启动日志写明当前是哪一种形态。 <!-- aidcp-cloud ec71ef1 偏离（收紧）：判据由「读口在不在」改为与握手侧占位归属**逐字相同**的 `ownershipMode !== 'off'`——enforce 被回滚成 off 时握手不再改写归属，按陈旧归属过滤会把本进程真正驱动的账号判成别人的、静默丢掉这道保护 -->

- [x] 1.4 每轮补一行常态回执（四个计数 + 偏差数）。加上过滤之后，「一切正常」「过滤器把范围收成空」「定时器根本没跑」在运维视角下同形，而后两件是故障；这行也是这道过滤在生产上唯一的正向证据。 <!-- aidcp-cloud 3665590 / aidcp-automation 9b102b3；部署时才发现的缺口：只留「异常才说话」的那条 warn，验收就只能靠「没日志」推断 -->

## 2. aidcp-cloud — 告警来源可分辨

- [x] 2.1 在风控告警唯一收口处把本进程 `execution_target` 拼进 detail，使 dev / ol 共用告警列表可分辨来源；不动 `alerts` 表 schema。 <!-- aidcp-cloud ec71ef1（`raiseRiskAlert`）/ aidcp-automation 60b4845（`createAutomationRiskFoundation` 的 `raiseAlert`） -->

## 3. aidcp-cloud — 回归覆盖

- [x] 3.1 单测：他 target 账号有偏差也不告警不重建；本 target 账号照旧检出偏差 + 按库重建；归属未知跳过并计入未知；归属读抛错不中断其余账号。 <!-- aidcp-cloud ec71ef1 test/risk-counter-outbox.test.ts 新增 5 例 -->
- [x] 3.2 单测：全跳过时响亮记录（守住「过滤器把对账做成死代码」这条失效模式，判据是断言那条记录发生过、而不是只断言无偏差）。 <!-- aidcp-cloud ec71ef1；变异验证：把 scopeFor 改成恒 'own' 后精确红 3 例（他 target / 归属未知 / 全跳过响亮），其余 11 例仍绿——承重的是这 3 例，不是端到端那条 -->
- [x] 3.3 跑 `npm run test:acceptance` → `npm test` → `npm run typecheck`，记录结果。 <!-- aidcp-cloud: acceptance 204/204 PASS；全量 4221 pass / 0 fail / 11 skipped；typecheck PASS。aidcp-automation: acceptance 277/277 PASS；typecheck PASS；全量 2205 pass / 4 fail——该 4 例在**未改动的 HEAD 上同样红**（fill-budget / XHS-SCHEDULE ×2 / AC-PREEMPT-6），是派生仓 test/ 不随 src 同步造成的既有漂移，与本 change 无关，已在 §4.4 登记 -->

## 4. 集成与部署

- [x] 4.1 合回 `aidcp-cloud` 默认分支并推送。 <!-- aidcp-cloud master 6c165c6..ec71ef1（scripts/land-change --yes，ff-only） -->
- [x] 4.2 派生仓落地：`scripts/sync-split-repos --apply --repo aidcp-automation` 同步对账器（dry-run 显示仅此 1 个文件有差异），并手写本仓自己的组装（组装根不派生）。 <!-- aidcp-automation master 5795b1e..60b4845 -->
- [x] 4.3 部署 dev（安全序列：target 检查 → 备份 `automation.bak.20260805-124012.tar.gz` → rsync → restart → healthcheck）。 <!-- 2026-08-05 deployed；healthcheck：service active、8787 监听、写者锁 target=dev 已持有、记账 outbox 就绪；启动日志确认「风控计数对账已启动……范围=归属为 dev 的账号」 -->
- [x] 4.4 部署后确认 dev 不再对 ol 归属账号报 `risk_counter_drift`。 <!-- 2026-08-05 13:01:57 dev 对账回执：`已物化=29 实际对账=23 他target跳过=6 归属未知跳过=0 偏差=0`。那 6 个正是此前每 5 分钟刷 P1 的 ol 归属账号；归属未知=0 说明归属读口在生产上真答得出来（不是被整体降级成跳过）。自 12:56 重启起 `计数偏差` 0 条 -->
- [ ] 4.5 **ol 侧仍未修**。口径 2026-08-05 13:00 更新：ol 已由并行 session 于 12:47–12:59 切到三派生服务（控制仓 `d512e8ce`），但发布分支 `release/20260805-ol-cutover` 钉的是**本 change 之前**的快照——ol 上 `risk-counter-reconciler.ts` 无 `ownerTargetFor`、启动日志无「范围=…」后缀。故 ol 对 dev 归属账号的误报会原样持续。上 ol 需用户明确要求，并把本 change 的两个提交（automation `60b4845` + `9b102b3`）带进该发布分支（CLAUDE.md §5/§6）。

## 5. 收口

- [x] 5.1 `openspec validate scope-risk-reconcile-to-owned-accounts --strict` 通过。
- [x] 5.2 观测对账周期，确认 dev 侧 `risk_counter_drift` 归零。 <!-- 证据见 4.4 -->
- [ ] 5.3 归档前置：ol 侧落地（4.5）未完成前不归档——只在 dev 生效的修复会让告警列表继续被 ol 的同一批误报占满，而归档会把这条未了债埋进 archive 目录。
