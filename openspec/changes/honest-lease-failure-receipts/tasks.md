## 1. aidcp-cloud — 租约失败判定去枚举化

- [x] 1.1 `src/comment-agent/comment-scheduler.ts:1509` 的 `isEdgeTaskAcquireFailure` 由**白名单**改为**补集**：`err instanceof EdgeTaskLeaseError && err.code !== 'release_timeout'`。注释写清判据是「**任务体是否已经执行过**」而非逐码枚举，并说明为什么 `release_timeout` 必须排除（它发生在 work 之后，评论可能已真实发出；误判会归还小时格 → 诱发重复评论）。<!-- aidcp-cloud 860ff96 -->
- [x] 1.2 `comment-scheduler.ts:1367` 的原因分档扩成三档（见 design D2）：`edge_unhealthy` = 「边端在线，但浏览器控制面不可用（需检查/重启该环境客户端）」；`browser_wake_failed` = 「浏览器处于待机、未能在唤醒死线内起来（可恢复，稍后自动重试）」；其余 = 原始 message（离线/失联）。MUST NOT 把前两者混说成「边端离线」。<!-- aidcp-cloud 860ff96 抽成 leaseFailureDetail()，排期链与定向链共用 -->

## 2. aidcp-cloud — 定向评论链补齐诚实终态

- [x] 2.1 `src/comment-agent/comment-task-runner.ts:186` 的 `TargetedCommentOutcome` 增补 `'not_started'` 成员。<!-- aidcp-cloud 860ff96 -->
- [x] 2.2 `comment-scheduler.ts:1459` 的 `targetedOutcomeToReceipt` 补 `not_started` 分支（穷举 switch 无 default，不补即 typecheck 失败）。文案：「浏览器未能接管，本次未搜索、未定位目标笔记、未发布评论（原因）」；**MUST NOT 带出具体目标笔记标识**。<!-- aidcp-cloud 860ff96 -->
- [x] 2.3 `comment-scheduler.ts:1190-1193` 的定向 catch 接上 1.1 的判定 → `{ outcome: 'not_started', … }`，并复用 1.2 的原因分档。非租约异常保持原 `post_failed` 路径不变。<!-- aidcp-cloud 860ff96 -->

## 3. aidcp-cloud — 受理超时接线修正（补 browser-slot-scheduling task 3.3 的缺口）

- [x] 3.1 `src/server.ts:1470`：`acquireTimeoutMs` 注入点删掉硬编码回落值 `?? 45_000`，改为「有 env 用 env、无 env 不传（走类默认 200s）」。使生效值只有一处事实源。
      背景：`browser-slot-scheduling` 的 task 3.3 标 `[x]`（`aidcp-cloud 87f53b9`），但该提交只改了 `edge-task-lease-client.ts` 的类默认常量、**从未碰 `server.ts`**，注入点的 45s 永远覆盖默认值 → 该修复至今零生效，dev `.env` 亦未设该 env。**本 change 不动 `browser-slot-scheduling/tasks.md`（有并发 session 在其上作业）**，缺口在此登记。<!-- aidcp-cloud 860ff96 新增 readEnvNumberOrUndefined()：有 env 用 env、无 env 交给被注入方的类默认，杜绝注入点复制默认值 -->
- [x] 3.2 dev `.env` 无需新增 env（接线修正后默认即 200s）；部署后确认日志中 acquire 不再在 45s 处提前超时。<!-- 2026-07-14 deployed -->

## 4. aidcp-cloud — 回归断言（typecheck 抓不到，必须用测试钉死）

- [x] 4.1 `test/comment-agent/comment-scheduler.test.ts`：排期链撞 `EdgeTaskLeaseError('edge_unhealthy')` → outcome `not_started`；回执文案含「未搜索」「未选中」「未发布」，且**不含**「已选中」「发布未确认」；`onScheduledTaskNotStarted` 被调用（小时格回流）。<!-- aidcp-cloud 860ff96 -->
- [x] 4.2 同上：撞 `release_timeout` → **不**归为 `not_started`（守住 D1 的排除项，防重复评论）。<!-- aidcp-cloud 860ff96 -->
- [x] 4.3 `test/comment-agent/comment-scheduler-targeted.test.ts`：定向链撞 `edge_unhealthy` → outcome `not_started`；回执**不含**任何目标笔记标识，且不含「已选中/发布未确认」措辞。<!-- aidcp-cloud 860ff96 -->
- [x] 4.4 原因分档断言：`edge_unhealthy` 的回执**不得**出现「离线」字样；`browser_wake_failed` 的回执标明可恢复。<!-- aidcp-cloud 860ff96 -->
- [x] 4.5 受理超时断言：未设 env 时 `EdgeTaskLeaseClient` 的生效 `acquireTimeoutMs` ≥ 边缘唤醒死线（200s），防止注入点回落值再次漂移。<!-- aidcp-cloud 860ff96 断言随 acquire 下发的 acquireTimeoutMs > 180s -->

## 5. 验证与集成

- [x] 5.1 `cd ../aidcp-cloud && npm run test:acceptance`（安全红线 `AC-PROTO-*` / `AC-PUB-*` / `AC-RISK-*` 必须全过）<!-- 50/50 pass -->
- [x] 5.2 `npm test` 全量 + `npm run typecheck` <!-- 1999/1999 pass；typecheck clean -->
- [x] 5.3 `openspec validate honest-lease-failure-receipts --strict`
- [x] 5.4 集成回 `master`（rebase，遇 non-ff 绝不 force），提交、推送 <!-- aidcp-cloud 860ff96 经 scripts/land-change ff 推 master -->
- [x] 5.5 按 CLAUDE.md §5 安全序列部署 dev（`scripts/deploy-target dev --check` → 备份 → rsync → restart → healthcheck）；红线：绝不碰同机 isales <!-- 2026-07-14 deployed -->
- [x] 5.6 真机验收项登记 `docs/real-machine-acceptance-backlog.md`：待机账号的排期评论能在 200s 受理窗内完成唤醒并真实发出；控制面故障时回执为「未开始」且小时格被归还

## 6. 附带修复（不属本 change 范围，随手补上）

- [x] 6.1 `aidcp-edge/.gitignore` 只有带斜杠的 `node_modules/`，**只匹配目录**——并行开发 worktree 软链过来的 `node_modules` 是符号链接文件、匹配不上，一次 `git add -A` 就会把软链提交进仓，ff 合回 master 时顶掉主 checkout 真正的 `node_modules` 目录。补一条不带斜杠的 `node_modules`。<!-- aidcp-edge 9324f52 -->
- [x] 6.2 `scripts/new-change` 开流时自动软链 `node_modules`（省掉每条流一次 `npm ci`），且**建之前先 `git check-ignore` 校验**——`.gitignore` 挡不住软链就不建，宁可让那条流自己 `npm ci`，也绝不留一颗会污染主干的雷。提示语补「只显式列文件、绝不 `git add -A`」。<!-- aidcp -->
