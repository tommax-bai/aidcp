# Tasks — decouple-quota-hit-from-risk

> 代码落 sub-repo（cloud / console），进度回写本节。commit 只 stage 本 change 文件（cloud 工作区有其他 WIP）。格式 `<!-- <repo> <sha> 备注 -->`。

## 1. aidcp-cloud — 摘掉「配额饱和 → 风控信号」（核心修复）

- [x] 1.1 `src/risk/risk-controller.ts` `record()` denial 路径移除 `applySignal({ kind: 'quota_exceeded' })`，被拒只 `return false`（背压）。保留 `record` 返 false 语义。 <!-- aidcp-cloud 7355d0f -->
- [x] 1.2 `src/risk/risk-state-machine.ts` 从 `isRiskSignal`（:21）与软信号 transition（:54）移除 `quota_exceeded`；确认 `light` 软路径 + 硬信号 / 手动信号路径不变。 <!-- aidcp-cloud 7355d0f -->
- [x] 1.3 `src/risk/types.ts` 从 `RiskSignalKind`（:42）删除 `quota_exceeded`。 <!-- aidcp-cloud 7355d0f -->
- [x] 1.4 更新单测 `test/risk-state-machine.test.ts` + `test/risk-controller.test.ts`（record 被拒返 false 且不迁移状态 / 不动 signal_count / last_signal_at）。 <!-- aidcp-cloud 7355d0f 新增两条不变量测试 -->
- [x] 1.5 更新 `test/acceptance/risk-guard.test.ts`：新增 AC-RISK-04（配额到顶 `record` 返 false 且风控态不变）；`npm run test:acceptance` 27/27 全过。 <!-- aidcp-cloud 7355d0f -->

## 2. aidcp-cloud — 配额饱和改道为低优先级运维告警

- [x] 2.1 新增 `src/risk/pacing-saturation-alerter.ts`（`PacingSaturationAlerter`，复用 `AlertStore.raise`，`type: 'pacing_saturation'`，`severity: 'P2'`，带 accountId + action + window），按「账号+动作」冷却 map（默认 20min）。只持 AlertStore、绝不碰风控状态单写路径。 <!-- aidcp-cloud ffe9fc5 -->
- [x] 2.2 `src/server.ts` `interaction.occurred` 接线：`record()` 返 false 时经 `explain(action)` 判 reason —— `quota:hour` / `quota:minute` → 调告警器（`quota:day` 静默、只背压）。alertStore 就绪后注入（缺则降级不发、不抛）。 <!-- aidcp-cloud ffe9fc5 -->
- [x] 2.3 单测 `test/pacing-saturation-alerter.test.ts`：突发窗发一条 P2 `pacing_saturation`；冷却窗内不重复、窗外可再发；账号/动作各自独立。「每日窗不发」由调用方只传 hour/minute 保证；「不改风控态」由该类只持 AlertStore 结构性保证。 <!-- aidcp-cloud ffe9fc5 -->

## 3. aidcp-cloud — 面板按账号暴露配额用量 / 上限

- [x] 3.1 `src/panel/panel-store.ts`：`AccountTotals` APPEND 可选 `quotas`（day 上限）+ `saturated`（撞顶动作）字段。 <!-- aidcp-cloud 704bbd2 -->
- [x] 3.2 `src/panel/panel-server.ts`：`GET /api/dashboard/summary` 的 `totalsByAccount` 每账号经 `riskRegistry.getController` 现读 `effectiveQuotas().day` 补上限 + 算饱和（**只读**，拿不到诚实缺省）。`asOf` 已在、不踩同块。 <!-- aidcp-cloud 704bbd2 -->
- [x] 3.3 单测 `test/panel-server.test.ts`：summary 按账号带 day 上限、publish 撞顶标饱和；restricted 账号互动上限为 0 且组合只读不改风控态。 <!-- aidcp-cloud 704bbd2 -->

## 4. aidcp-console — 用量可见 + 恢复出口

- [x] 4.1 `src/types/api.ts`：`AccountTotals` 镜像 `quotas?` + `saturated?` 字段。`useDashboardSummary` 经 `DashboardSummary` 引用该类型、自动流通，queries.ts 无需改（不新增 hook）。 <!-- aidcp-console cd3a2f5 -->
- [x] 4.2 `src/components/AccountTotalsTable.tsx`：每格由「数字」升级为「用了 / 上限」（上限灰显），撞当日上限标红加粗；上限缺省回落只显用量。配色与 `RiskStatusBadge` 区分。 <!-- aidcp-console cd3a2f5 -->
- [x] 4.3 `src/components/RiskControls.tsx` **已暴露**「强制恢复（特权覆盖）…」（`operator_override_recover` + 审计理由 Modal）——确认无需补。 <!-- aidcp-console 现状已满足 -->
- [x] 4.4 console `npm run typecheck` 过、`npm run build` 通过（chunk 警告为既有、非本次引入）。 <!-- aidcp-console cd3a2f5 -->

## 5. 回归 / 部署 / 收尾

- [x] 5.1 cloud：`npm run test:acceptance` 27/27 → 全量 `npm test` **1001/1001** → `npm run typecheck` 干净（AC-RISK / AC-PROTO / AC-PUB 红线不破）。console typecheck + build 通过。 <!-- aidcp-cloud 全绿 2026-07-01 -->
- [x] 5.2 部署 cloud + console（用户 2026-07-01 授权「带其他修改一起上」）。**cloud**：并发操作方已把 master（含本 change 三 commit）部署上 ECS（server.ts mtime 10:55、11:13:55 重启）——探针实测 Group 1/2/3 全部 live（`quota_exceeded` 已删净、`PacingSaturationAlerter` 接线 + 启动日志「已就绪」、panel `totalsByAccountWithQuotas`+`saturated` 在）；healthcheck 全过（`active`／8787 监听／飞书 onReady／PG `select 1`／NRestarts=0／isales 未受影响）。故未重复 rsync（避免撞车）。**console**：ECS 是 06-30 旧构建，由本人补部署——备份 `console.bak.20260701-111756.tar.gz` → 纯覆盖 rsync（无 `--delete`，保 `intro.*`）→ 验证 index.html 引新 bundle `index-Y58Wj89Q.js`、8088 serve 200。 <!-- aidcp-cloud 并发方部署; aidcp-console 本人 rsync /opt/aidcp/console 2026-07-01 deployed -->
- [x] 5.3 运营对 Tmax（`66cd1d4f…0314ee`）执行「强制恢复」——用户 2026-07-01 确认已恢复。本 change 已上线，不再自锁。 <!-- 2026-07-01 用户经后台强制恢复 -->
- [x] 5.4 `openspec validate --strict` 通过 → 部署验证通过 → archive（用户 2026-07-01 确认）。 <!-- 2026-07-01 archived -->
