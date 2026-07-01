## Why

「撞到自己的速率配额」现在被当成风控信号在用：`RiskController.record()` 一旦某动作被 `canDo` 拒（配额到顶），就 `applySignal({kind:'quota_exceeded'})`，把账号威胁状态机推 `normal→warned→restricted`。这混淆了两件正交的事——**我方自我节流（背压，正常且健康）** 与 **平台风险（威胁，需要收敛）**。后果是账号会**自锁**：实测账号 Tmax（`66cd1d4f…0314ee`）持续浏览撞受限态下 conservative 的 view 每小时上限（20/h），每一次超额 view 都吐一个 `quota_exceeded`、刷新 `last_signal_at` 把 72h 恢复窗口无限重置，`signal_count` 累到 31，卡在 `restricted` 不动——全程零验证码、零平台风控浮层，纯系统自判。

## What Changes

- **cloud（核心修复）**：`RiskController.record()` 被拒不再发 `quota_exceeded` 信号，只 `return false`（背压——`canDo` 本就已拦住动作）。把 `quota_exceeded` 从威胁状态机的升级逻辑与 `RiskSignalKind` 中移除。威胁态今后**只由平台可观测信号驱动**：验证码 → 强信号、未知阻断浮层 → 软信号、运营手动信号。这是对「不自残 / 被禁 `record` 返 false」红线的**强化**（`record` 被拒仍返 false 不变，只去掉「撞自己配额还自升状态」的自残副作用）。
- **cloud（改道·运维告警）**：当 `record` 因**速率窗口**到顶被拒（`explain` 的 reason 为 `quota:hour` / `quota:minute`，即过载节奏）时，用现成告警存储发一条**低优先级运维告警**（`type: pacing_saturation`，按「账号+动作」冷却），进现有 `/api/alerts` + 看板告警区。这是被摘掉的信号的正确新归宿：「该有人去调这个账号的浏览节奏」。
- **cloud + console（改道·用量可见）**：看板总览接口的按账号今日计数补上「当前 day 窗口生效配额上限」（+ 可选已饱和窗口标记）；后台把按账号今日活动表每格从「数字」升级成「用了 / 上限」、到顶标红。视觉上与风控状态徽标**明显区分**（节奏 ≠ 平台风险）。
- **console（恢复出口·小）**：确认风控控制器已暴露「运营强制恢复」（`operator_override_recover`）。**不加自动恢复**——真风险态保持人工显式清除；让运营能从 UI 恢复账号（如 Tmax）。
- **不做**：不改每日配额数字；不加自动恢复；不动 WebSocket 协议（风控留云端内部）；账号列表单独加「配额」徽标列为可选 stretch，v1 不做。

## Capabilities

### New Capabilities
<!-- 无新增 capability；变更并入既有两个 spec 的 delta -->

### Modified Capabilities
- `interaction-risk-gating`: 新增/修订要求——**速率配额超限是「节奏背压」，不是「风控状态输入」**；账号威胁态只由平台可观测信号（验证码 / 阻断浮层 / 运营手动）升级；`record` 被拒返 false 的红线保留、但不再附带状态升级副作用。
- `console-panel-api`: 新增要求——按账号的**配额用量 / 上限**对外可见（看板按账号活动带生效上限 + 饱和标记）；**节奏饱和以低优先级运维告警**呈现，与风控告警同渠道、不同语义。

## Impact

- **cloud（aidcp-cloud）**
  - `src/risk/risk-controller.ts`：`record()` denial 路径移除 `applySignal({kind:'quota_exceeded'})`；新增只读判定供接线层识别「速率饱和」。
  - `src/risk/risk-state-machine.ts`：`quota_exceeded` 从 `isRiskSignal` 与软信号 transition 中移除。
  - `src/risk/types.ts`：`RiskSignalKind` 去掉 `quota_exceeded`。
  - `src/server.ts`：`interaction.occurred` 接线处经 `explain()` 识别速率饱和 → 注入的运维告警器发低优先级告警（冷却 map）。
  - `src/panel/panel-store.ts` / `src/panel/panel-server.ts` / `src/panel/types.ts`：看板 `totalsByAccount` 每账号 APPEND 生效上限（+ 饱和标记），来自各账号 controller 的 `effectiveQuotas()` / `counts()`。
  - 测试：`test/risk-state-machine.test.ts` / `test/risk-controller.test.ts` / `test/acceptance/risk-guard.test.ts` 更新到新行为（配额拒不升级）；新增运维告警 + 面板用量字段的断言。
- **console（aidcp-console）**
  - `src/components/AccountTotalsTable.tsx`：每格「用了 / 上限」+ 到顶标红。
  - `src/types/api.ts` / `src/api/queries.ts`：镜像新字段（只调既有 `useDashboardSummary` 块，不新增 hook）。
  - `src/components/RiskControls.tsx`：确认「强制恢复」已暴露（缺则补）。
- **协调**
  - `session-limits-to-quota-layer`（在飞）明确不动风控状态单写路径，且它治理「单场会话预算」，与本 change 展示的「滑窗速率配额」是不同预算——设计里点明区分，无冲突。
  - `dashboard-refresh-clarity`（在飞，前提已过时）也改看板总览接口（加 `asOf`）+ 看板页 + `queries.ts`；字段可加、协调不踩同一 summary 块。
- **红线**：`record` 被禁返 false 不变（AC-RISK 强化非削弱）；不动协议两份 `protocol.ts`；面板只读组合、绝不经 `RiskController` 写。
