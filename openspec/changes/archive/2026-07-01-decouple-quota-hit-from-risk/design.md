## Context

账号风控状态机（`normal→warned→restricted→frozen`）本意是「平台威胁态」：平台注意到我们、可能要制裁，就收敛。但现状把「我方自我节流」也接进了这根状态机——`RiskController.record()` 一旦某动作被 `canDo` 拒（滑窗配额到顶），就 `applySignal({kind:'quota_exceeded'})`，把威胁态往上推（`risk-controller.ts:88-90`、`risk-state-machine.ts:21,54`、`types.ts:42`）。

这两件事是正交的：

- **速率配额（节流 / 背压）**：我方给自己设的活动预算。跑满 = 节流器正常工作、把我拦在安全速率内。这是**健康、预期**的结果。数据来源是**我方的计数器**。
- **威胁态（风控）**：平台对我的反应。证据 = 验证码、阻断浮层、强制登出、内容被删、互动被平台拒。数据来源是**平台**。

把前者接进后者导致**自锁**：受限态下互动配额被清零、浏览配额压到 conservative（view 20/h），持续浏览（每开一篇笔记记一次 `view`，`handler.ts:224-238`）不断撞顶、每次超额都吐 `quota_exceeded` 刷新 `last_signal_at`、把 72h 恢复窗口无限重置。实测 Tmax 就此卡在 `restricted`、`signal_count=31`、全程零平台信号。且威胁态无自动恢复发射方（`recovered` 信号只有消费方），只进不出。

## Goals / Non-Goals

**Goals:**
- 速率配额饱和只做背压（拒绝 + 可选运维提示），**不再升风控态**。威胁态只由平台可观测信号驱动。
- 把「配额饱和」改道成运营看得见的信息：按账号**用量 / 上限**可见 + **过载节奏**低优先级运维告警。
- 保住并强化红线：`record` 被拒仍返 false（AC-RISK「不自残」），只是去掉状态升级副作用。
- 让运营能从后台**显式强制恢复**账号（真风险态保持人工清除）。

**Non-Goals:**
- 不加自动恢复 / 定时降级扫描（真风险态该人工确认）。
- 不改每日 / 突发配额数字本身（那是 `safety-quota-config` 的治理面）。
- 不动 WebSocket 协议、两份 `protocol.ts`、`command-bridge`（风控留云端内部）。
- 不治理「单场会话预算」（那是在飞的 `session-limits-to-quota-layer`，属**另一种预算**，见 Decisions D6）。
- 账号列表单独加「配额」徽标列 = 可选 stretch，v1 不做。

## Decisions

### D1：彻底移除 `quota_exceeded` 作为风控信号（而非「保留但忽略」）
`record()` denial 路径去掉 `applySignal({kind:'quota_exceeded'})`，被拒只 `return false`；同时从 `risk-state-machine.ts` 的 `isRiskSignal`（:21）与软信号 transition（:54）、`types.ts` 的 `RiskSignalKind`（:42）删除该 kind。
- **为何彻底删而非留着不触发**：留着会给后人「配额还能升风控」的错觉，且引用面极小（全仓仅 4 处 + 1 单测），删干净成本低、语义清。
- **软信号路径不受损**：`light`（未知阻断浮层）仍在，`normal→warned→restricted` 的软升级对**真实**软信号照常工作，只是不再由「我方配额」触发。

### D2：告警在接线层发，`RiskController` 保持纯净
运维告警不在 `RiskController` 内部发（它不该持有告警存储 / 做 I/O）。改在 `interaction.occurred` 接线处（`server.ts:612`）：`record()` 返 false 时调 `explain()` 拿 reason，若为 `quota:hour` / `quota:minute`（过载节奏），经**注入的运维告警器**发一条低优先级告警。
- **备选**：给 `RiskController` 注入告警回调——否决，会让风控层背上 I/O 依赖、破坏「纯状态 / 配额计算器」定位。
- **备选**：`record()` 返回富结构（含 reason）——可选优化，但 `explain()` 已能拿到 reason，v1 复用即可，不改签名。

### D3：只对**突发窗口**（小时 / 分钟）饱和发告警，每日饱和静默
过载节奏的信号是**突发窗口**撞顶（短时间刷太猛）。每日上限撞顶是「今天预算用完了」——预期、正常，发告警只会刷屏。故告警仅在 `quota:hour` / `quota:minute` 触发；`quota:day` 只背压、不告警。

### D4：用量可见走既有看板总览接口的按账号切片，不新增端点
`GET /api/dashboard/summary` 已有 `totalsByAccount`（按账号今日各动作计数）。对每个账号 APPEND 当前 **day 窗口 `effectiveQuotas`**（+ 每动作是否已在任一窗口饱和的标记），由各账号 controller 的 `effectiveQuotas()` / `counts()` 现读。前端 `AccountTotalsTable` 每格「用了 / 上限」、到顶标红。
- **为何不新增 `/api/accounts/:id/quota-status` 端点**：YAGNI。用量天然属于「今日活动」视图，就地增强复用最多、改动最小。细粒度端点等有单账号详情页需求再说。
- **上限随风控态变**：`effectiveQuotas()` 已内建——`restricted` 账号互动上限显示为 0、`warned` 显示 0.7 缩放值，用量视图**顺带**如实反映风控态对预算的收敛。

### D5：告警分级与去重
`type: pacing_saturation`，`severity` 取低档（P2）——它是「该调节奏」的提示，不是阻断。按「账号 + 动作」冷却（~15–30min，仿 `captcha-coordinator` 的 `lastAlertAt` map），避免同一过载在冷却窗内反复落库。

### D6：与在飞变更的边界（点明「两种预算」）
- **速率配额（本 change 展示的）**：滑动窗、按分钟 / 小时 / 天、`RiskController.effectiveQuotas()`——「这账号每单位时间能做多少」。
- **单场会话预算（`session-limits-to-quota-layer` 治理的）**：一场浏览会话内能做多少（`freshBudget()` / `session_config`）。两者不同层、不同表，本 change 不碰后者；后者也明确不动风控状态单写路径。无冲突。
- `dashboard-refresh-clarity`（前提已过时）也改看板总览接口（加 `asOf`）+ 看板页 + `queries.ts`：本 change 只在 `totalsByAccount` 每账号 APPEND 上限字段、只调既有 `useDashboardSummary` 块，字段可加、协调不踩同一块。

### D7：恢复出口 = 人工显式，不加自动恢复
不接 `recovered` 发射方 / 定时扫描。真风险态由运营经后台「强制恢复」（`operator_override_recover`，`panel-server.ts:295` 已支持）清除。任务里确认 `console` 的 `RiskControls` 已把该操作暴露成按钮（缺则补）。

## Risks / Trade-offs

- **[受限态软升级此后只能靠未知阻断浮层触发]** → 这是**正确的**：`normal→warned→restricted` 的软路径本就该只反映真实平台软信号；配额从来不该在其中。硬信号（验证码）仍一步到 `restricted`，覆盖真风险。
- **[告警刷屏]** → 按「账号+动作」冷却窗去重 + 低分级；只对突发窗口发、每日饱和静默。
- **[看板总览接口按账号算 `effectiveQuotas()` 增开销]** → 账号数量级小（个位到几十），每账号一次内存态读取，非全表扫描，符合面板「只读组合、不阻塞事件循环」红线。
- **[跨流文件冲突]**（`panel-server.ts` / `panel/types.ts` / `queries.ts` / `AccountTotalsTable`）→ 只 APPEND 字段 / 只调既有块；提交只 stage 本 change 文件（cloud 工作区有其他 WIP）。
- **[删 `quota_exceeded` 破坏历史断言]** → 同步更新 `risk-state-machine.test.ts` / `risk-controller.test.ts` / `acceptance/risk-guard.test.ts`；先 `npm run test:acceptance` 再全量，确保 AC-RISK 全过。

## Migration Plan

1. cloud 改 3 处风控源文件 + 接线告警 + 面板字段，更新测试 → `npm run test:acceptance` → 全量 `npm test` → `npm run typecheck`。
2. console 改 `AccountTotalsTable` + 类型 / 取数镜像 + 确认 `RiskControls` 强制恢复按钮 → 前端构建 / typecheck。
3. 部署 cloud（走安全序列：备份 → rsync → restart → healthcheck），console 静态构建发布。
4. 运营对 Tmax 执行「强制恢复」（本 change 之后它不会再自锁）。
5. 回滚：cloud 状态机 / 接线是纯代码回退（无迁移、无 schema 改动），`git revert` + 重部署即可。
