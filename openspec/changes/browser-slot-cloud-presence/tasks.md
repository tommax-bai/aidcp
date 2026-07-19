## 1. Cloud 可信引导与在线语义

- [x] 1.1 在 customer-auth server 增加 env-scoped control bootstrap，只返回经 `resolveBoundAccountForEnv` 验证的 envKey/accountId，并保持四类 fail-closed 错误。
- [x] 1.2 为 control bootstrap 覆盖成功、越权、未绑定、跨客户冲突、存储不可用和鉴权失效测试。
- [x] 1.3 让 Cloud 识别 Edge 的 browser-absent capability/state，并保证 UI snapshot、人设真态与 acquire/wake 信号仍可到达控制面在线会话。
- [x] 1.4 为 browser-absent 任务的唤醒、死线失败和非 offline 回执补 Cloud 测试与可诊断握手拒绝日志。

<!-- Cloud evidence: aidcp-cloud commit 19cf0eb. `src/client-auth/client-auth-server.ts` exposes the customer-auth scoped bootstrap through the existing binding resolver. `test/client-auth-server.test.ts` covers success, ownership, unknown, conflict, unavailable and anonymous requests; `test/handler.test.ts` locks browser_absent_v1 into the accepted session. Existing edge-task lease and scheduler recovery suites cover acquire/wake failure as recoverable rather than offline, and `src/comm/handler.ts` retains edge/account/reason handshake rejection diagnostics. -->

## 2. Edge 严格握手与无浏览器核心

- [x] 2.1 修正 `EdgeClient.openAndHello()`：只接受结构完整的 welcome；error/畸形响应 fail-closed 且保留可诊断原因，并补单测。
- [x] 2.2 增加 detached EdgeSession 与 lifecycle 初始 standby，使核心可在不启动 AdsPower/CDP 的情况下连接 Cloud。
- [x] 2.3 守住 browser-absent 启动边界：浏览循环、平台 watcher 与页面 supervisor 均不得提前启动，并补生命周期测试。
- [x] 2.4 在 wake 后启动 AdsPower、重附着 CDP、读取真实身份；身份变化时先以真实账号重建有效 Cloud 会话，失败时禁止页面动作并可再次唤醒。
- [x] 2.5 对浏览器缺席时误达的页面命令返回明确失败，不再静默丢弃。

<!-- Edge evidence: aidcp-edge commit 4e0671e. Strict hello tests reject error and malformed welcome; detached-session and initial-standby tests lock the no-CDP birth path. Generic XHS/FB wake reattaches the stable session object and re-handshakes on identity change before runtime resume. The WeChat interaction runtime keeps its browser sidecar closed until a slot-backed lifecycle wake. Direct page commands while absent emit `action.completed` with `browser_absent_wake_requested`; pacing-only updates remain browser-free. -->

## 3. Electron 槽位调度与诚实 UI

- [x] 3.1 Electron 主进程用客户会话请求 control bootstrap；成功时以专用 env 启动 browser-absent 核心，失败时不猜账号并保留旧排队回退。
- [x] 3.2 将无槽位环境接入现有 cold-standby ack、FIFO wake 和槽位归还链；单个 AdsPower 启动失败后继续下一队列项。
- [x] 3.3 将 Cloud 会话、浏览器运行/排队/待机和 persona 三态拆分展示；只有有效 welcome 才显示“已连接云端”。
- [x] 3.4 补多环境监督器回归：槽位少于环境时控制面仍在线、第五个被占用时后续队列继续、统计可核对、引导失败原因诚实。

<!-- Electron evidence: control-only children do not count in `occupiedSlots()`, retain bounded browser queue reservations, acknowledge through `lifecycle.standby`, and enter the existing FIFO wake path. Wake failure schedules an immediate `drainSlotWaiters()` so an occupied fifth profile cannot stall the next environment. Batch UI separates browser-queued and control-only counts, while persona remains the existing nullable authority signal. Focused Electron scheduling/lifecycle/console regressions: 79/79. -->

## 4. 验证、集成与 dev

- [x] 4.1 aidcp-edge 运行聚焦测试、acceptance、全量测试与 typecheck；记录通过数和任何真机未覆盖边界。
- [x] 4.2 aidcp-cloud 运行聚焦测试、acceptance、全量测试与 typecheck，确认协议/发布/风险安全套件全绿。
- [x] 4.3 更新 OpenSpec 任务证据并执行 `openspec validate browser-slot-cloud-presence --strict`。
- [x] 4.4 分别提交并推送 Edge、Cloud 与 control 变更，按默认分支快进集成且保持 canonical checkout 干净。
- [x] 4.5 从干净 Cloud master 部署 dev，核验 service、8787/8090 listener、health、Feishu、PostgreSQL 与 isales 未受影响。
- [x] 4.6 不生成 Edge 安装包；将“真实客户端升级后验证 16 环境/5 槽位、槽位外 persona 可见、任务可唤醒”登记为真机验收项。

<!-- Validation evidence (2026-07-19): Edge focused scheduling/lifecycle/console 79/79, acceptance 25/25, full 1855/1855, typecheck pass. Cloud focused bootstrap/capability tests pass, full 2541 pass with 8 explicit gated skips, typecheck pass. Real installed-client validation remains open because no Edge installer was built; recorded as cluster 106 in `docs/real-machine-acceptance-backlog.md`. -->

<!-- Integration/deploy evidence (2026-07-19): aidcp-edge 4e0671e and aidcp-cloud 19cf0eb were rebased on current origin/master, pushed on the feature branch, then fast-forwarded and pushed to master; control 596d7f3 was pushed to main before this evidence-only follow-up. dev preflight selected 121.89.85.150. No dependency or migration changed. Backed up `/opt/aidcp/cloud` (including target-local env, excluding node_modules/git) to `/opt/aidcp/backups/cloud.bak.20260719-165851.tar.gz`, synced only `src/client-auth/client-auth-server.ts`, and restarted only `aidcp-cloud.service`. Post-restart: service active; 8787/8090/8091 listening; panel and client-auth health both `{ok:true}`; PostgreSQL ready; Feishu WS onReady; isales api/engine/scheduler/worker remained active. -->
