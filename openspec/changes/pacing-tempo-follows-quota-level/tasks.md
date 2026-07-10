# Tasks — pacing-tempo-follows-quota-level

> 纯云端改动（边缘 / 协议零改）。回归纪律：`test:acceptance` → 全量 `test` → `typecheck` 全绿。
> 非热点文件（不碰 protocol.ts / command-bridge / RoleName 注册 / 风控状态机单写）；只读 `state.quotaLevel`。

<!-- cloud 870be7b landed master + 2026-07-10 deployed dev -->

## 1. aidcp-cloud — effectiveTempo 接入

- [x] 1.1 `src/risk/pacing.ts`：`tempoForQuotaLevel`（conservative=1.3 / normal=1.0 / aggressive=1.0）+ `effectiveTempo = max(tempoForStatus, tempoForQuotaLevel)` <!-- cloud 870be7b -->
- [x] 1.2 `src/risk/pacing.ts`：`DwellInput`/`ThinkInput`/`FeedFloorInput` 加 `quotaLevel?`；`compute*` 内改用 `effectiveTempo(status, quotaLevel ?? 'normal')` <!-- cloud 870be7b -->
- [x] 1.3 `src/risk/pacing.ts`：`buildPacingSnapshot(status, quotaLevel, provider)`，快照 tempo 用 `effectiveTempo` <!-- cloud 870be7b -->
- [x] 1.4 `src/comm/handler.ts`：`buildWelcomePacing` 读 `getState().quotaLevel` 传入（读态异常回落 normal） <!-- cloud 870be7b -->
- [x] 1.5 `src/orchestrator/role-dispatcher.ts`：`getQuotaLevel?` 入口 + 成员 + 默认 `() => 'normal'` <!-- cloud 870be7b -->
- [x] 1.6 `role-dispatcher.ts`：`thinkNow`/`dwellForCurrentNote`/feed 中心值传 `quotaLevel: this.getQuotaLevel()` <!-- cloud 870be7b -->
- [x] 1.7 `role-dispatcher.ts`：`maybePushTempo` + 构造期基线用 `effectiveTempo(getRiskStatus(), getQuotaLevel())`（`tempoForStatus` import 换 `effectiveTempo`） <!-- cloud 870be7b -->
- [x] 1.8 `src/server.ts`：dispatcher 装配加 `getQuotaLevel: () => ctx.controller.getState().quotaLevel` <!-- cloud 870be7b -->

## 2. 测试（克制）

- [x] 2.1 `effectiveTempo`/`tempoForQuotaLevel`：conservative=1.3、normal/aggressive=1.0；与 status 取 max <!-- cloud 870be7b test/risk-pacing -->
- [x] 2.2 `computeDwellMs`/`computeThinkMs`：status normal 下 conservative>normal、aggressive==normal；restricted 下 quotaLevel 不再改变；缺省 quotaLevel 退化零回归 <!-- cloud 870be7b -->
- [x] 2.3 cloud dispatcher：quotaLevel normal→conservative → 下一次 sendCommand 前推 `pacing_update{1.3}` <!-- cloud 870be7b test/integration/pacing-tempo-push -->
- [x] 2.4 `buildPacingSnapshot`：conservative 账号 welcome 快照 tempo=1.3（status normal）；restricted+conservative 取 1.6 <!-- cloud 870be7b test/pacing-snapshot -->
- [x] 2.5 `test:acceptance`（47 绿，AC-PROTO 计数不变 72）→ 全量 `test`（1759 绿）→ `typecheck` 全绿 <!-- cloud -->

## 3. 集成 / 部署 / 真机

- [x] 3.1 cloud land（fetch+rebase master、跑闸）→ ff push master `870be7b` <!-- land-change --yes -->
- [x] 3.2 本仓 openspec change 提交、push（additive，走 main 临时 worktree） <!-- 见 archive 提交 -->
- [x] 3.3 部署 dev（备份 cloud.bak.20260710-184537 → rsync 快照 → restart → healthcheck 全过：active/8787/8090/effectiveTempo+getQuotaLevel live/飞书长连接/无错） <!-- 2026-07-10 deployed dev -->
- [x] 3.4 真机验收项登记 backlog 簇 39（后台把测试号改「保守」→ 动作停顿/停留明显变慢 + 边缘日志当场出现，现真可人为触发） <!-- 见 backlog -->
- [x] 3.5 tasks.md 勾选回写 + validate --strict → archive <!-- 本次 -->
