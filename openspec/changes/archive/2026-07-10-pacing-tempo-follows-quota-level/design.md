# Design — pacing-tempo-follows-quota-level

## 现状（坐实）

- `tempoForStatus(status)`（`pacing.ts`）：`normal=1.0 / warned=1.3 / restricted|frozen=1.6`。**唯一** tempo 来源。
- `computeDwellMs`/`computeThinkMs`/`computeFeedFloorMs`/`buildPacingSnapshot` 全用 `tempoForStatus(status)`——只吃 `status`。
- `state.quotaLevel`（`conservative`/`normal`/`aggressive`，默认 `normal`）：经 `RiskController.setQuotaLevel` 单写、`panel-server.ts:1048` 后台可配。只驱动 `effectiveQuotas()`（限频），**不碰 tempo**。
- 注：`effectiveQuotas()` 里 `warned`/`restricted`/`frozen` 基准固定 `conservative`、`normal` 用 `state.quotaLevel`——即 quotaLevel 仅在 status=normal 时对配额生效。tempo 侧同理用 max 合并后，quotaLevel 的放慢在 status=normal 时透出、status 更差时被更大的 status-tempo 盖过。

## 决策

`effectiveTempo(status, quotaLevel) = max(tempoForStatus(status), tempoForQuotaLevel(quotaLevel))`

`tempoForQuotaLevel`：`conservative=1.3` / `normal=1.0` / `aggressive=1.0`。

- **取 max 而非相乘**：两者都是「越谨慎越慢」的 ≥1 因子；max = 谁更谨慎听谁，避免相乘把保守+被警告叠成 1.69 这类过慢。与 `effectiveQuotas` 的「status 差就固定 conservative 基准」同精神（不叠加、取更严）。
- **激进不提速（=1.0 而非 <1.0）**：tempo <1.0 会把动作停顿压到人类基线以下、更像机器、抗检测头寸更薄。「激进」的语义是「用满更多配额（多做）」，不是「每个动作更快」。故激进只放行更多配额、pacing 保持人类量级。用户 07-10 定案。
- **纯云端**：tempo 由云端算、随 welcome 快照 / 决策指令 / `pacing.update` 下发；边缘只乘算。故只改云端算 tempo 处，边缘与协议零改。

## 接入点（全云端）

| 处 | 改法 |
|---|---|
| `computeDwellMs`/`computeThinkMs`/`computeFeedFloorMs` | 入参加 `quotaLevel?: RiskQuotaLevel`（可选、默认 `normal` 保测试向后兼容）；内部 `tempoForStatus(status)` → `effectiveTempo(status, quotaLevel ?? 'normal')` |
| `buildPacingSnapshot(status, provider)` | → `buildPacingSnapshot(status, quotaLevel, provider)`，快照 tempo 用 `effectiveTempo` |
| `handler.ts buildWelcomePacing` | 读 `getState().quotaLevel` 一并传入 |
| `role-dispatcher` `thinkNow`/`dwellForCurrentNote`/feed 中心值 | 传 `this.getQuotaLevel()` |
| `role-dispatcher` `maybePushTempo` + 构造期基线 | `tempoForStatus(getRiskStatus())` → `effectiveTempo(getRiskStatus(), getQuotaLevel())` |
| `server.ts` dispatcher 装配 | 加 `getQuotaLevel: () => ctx.controller.getState().quotaLevel` |

## 中途生效（复用既有通道）

后台 `setQuotaLevel` 改档 → 该账号 controller 状态更新 → dispatcher 下次 `sendCommand` 顶端 `maybePushTempo` 读到新 `quotaLevel` → `effectiveTempo` 变 → 去抖推 `pacing.update` → 边缘 `applyTempoUpdate` 当场调速。**无需断连重连**。这正是让 `pacing-fallback-hardening` 的 `pacing.update` 通道从 latent 转为日常可触发的关键。

## 安全 / 回归

- `effectiveTempo` 取 max、`tempoForQuotaLevel` 恒 ≥1.0 → 只会更慢、绝不更快（保守放慢、激进不提速），风控安全方向；无零延迟风险。
- 默认账号 `quotaLevel=normal` → `tempoForQuotaLevel=1.0` → `effectiveTempo=tempoForStatus`，行为**零回归**（未配保守的号完全不变）。
- 无协议 / 边缘改动 → 无 `AC-PROTO` 漂移、无边缘回归。
- 不做 env 开关：纯保守方向、零回归，无需 kill-switch。
