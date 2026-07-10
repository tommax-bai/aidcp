## Why

节奏快慢（tempo 降速旋钮）当前**只跟随风控状态**（`normal`/`warned`/`restricted`/`frozen`）。但「风控状态迁移接真实平台封号 / 限流信号」尚未实装（CLAUDE.md §2 已知缺口），状态平时恒 `normal`、tempo 恒 1.0——**降速旋钮实际空转**。

与此同时，账号另有一个**真正被运营拨动**的档位——**配额档**（`conservative`/`normal`/`aggressive`，经后台管理台 `setQuotaLevel` 按账号手动配、`panel-server` 已接线）。但它**只驱动限频配额（做多少），完全不碰节奏快慢**。结果：把一个号配成「保守」，它只是**少做**、每个动作的停顿却和「激进」号一模一样、**不会更慢**。

「保守」的直觉应是**又少又慢**。本 change 让节奏 tempo **同时**参考配额档：取「风控状态 tempo」与「配额档 tempo」中**更慢的一个**，使运营配的档位真能调速、且不再 latent。

## What Changes

- 新增 `tempoForQuotaLevel(quotaLevel)`（`conservative=1.3` / `normal=1.0` / `aggressive=1.0`——激进只多做、**不提速**，守人类节奏下限）与 `effectiveTempo(status, quotaLevel) = max(tempoForStatus(status), tempoForQuotaLevel(quotaLevel))`（两者都是 ≥1 放慢因子，谁更谨慎听谁）。
- 云端所有算 tempo 处改用 `effectiveTempo`：`computeDwellMs` / `computeThinkMs` / `computeFeedFloorMs`（决策中心值）、`buildPacingSnapshot`（welcome 兜底快照）、`role-dispatcher` 的中途档位推送 `maybePushTempo` 与其去抖基线。
- **纯云端改动，边缘零改**：边缘只是「收到多少 tempo 就乘多少」，收发 / 应用 / 中途刷新已由 change `pacing-fallback-hardening` 接好；协议 tempo 字段已存在，**无协议改动**。
- **附带红利**：后台改某账号配额档 → dispatcher 下次统一出口 `maybePushTempo` 读到新 quotaLevel → `effectiveTempo` 变 → 经既有 `pacing.update` **实时推到边缘、当场调速**（无需断连重连）。这让刚落地的 `pacing.update` 通道从 latent 变为**真被日常运营触发**。

## Capabilities

### Modified Capabilities
- `command-pacing`：
  - ADDED「节奏 tempo 由风控状态与配额档共同取更慢者」——保守账号即便风控 `normal` 也整体放慢。
  - MODIFIED「风控档位中途变化实时传播到边缘兜底」——触发源由「仅风控状态」推广为「风控状态**或**配额档」变化。

## Impact

- **aidcp-cloud**：`src/risk/pacing.ts`（`tempoForQuotaLevel` + `effectiveTempo`；`compute*` / `buildPacingSnapshot` 加 `quotaLevel` 入参并改用 `effectiveTempo`）、`src/comm/handler.ts`（`buildWelcomePacing` 读 `quotaLevel` 传入）、`src/orchestrator/role-dispatcher.ts`（`getQuotaLevel` 入口 + 中心值调用传 `quotaLevel` + `maybePushTempo`/基线用 `effectiveTempo`）、`src/server.ts`（wire `getQuotaLevel`）、相关测试。
- **aidcp-edge**：无改动（tempo 收发 / 应用不变）。
- **协议**：无改动（tempo 字段已存在；不新增消息类型）。
- **风控**：只读 `state.quotaLevel`（不写风控单写路径）；`effectiveTempo` 取 max、恒 ≥ 现役量级，**只会更慢不会更快**（保守放慢、激进不提速）——安全方向。
- **部署**：随 dev 默认部署；无 env 开关（保守放慢是纯保守方向、零回归风险）。真机验收登记 backlog。
