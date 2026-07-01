## ADDED Requirements

### Requirement: 速率配额饱和是节奏背压、不是风控状态输入

账号威胁态（`normal` / `warned` / `restricted` / `frozen`）MUST 只由**平台可观测信号**驱动升级：验证码 → 强信号（`confirmed`）、未知阻断浮层 → 软信号（`light`）、运营手动信号（`manual_restrict` / `manual_freeze` / `operator_override_recover`）。

`RiskController.record(action)` 因**滑动窗速率配额**耗尽而被 `canDo` 拒时 MUST 只返回 `false`（背压），MUST NOT 触发任何风控状态迁移——具体地：MUST NOT `applySignal`、MUST NOT 递增 `signal_count`、MUST NOT 刷新 `last_signal_at`、MUST NOT 把账号从 `normal` 推向 `warned` / `restricted`。`quota_exceeded` MUST NOT 作为风控信号种类存在于状态机升级逻辑与 `RiskSignalKind` 中。

此要求**强化**「被禁账号 `record` 返回 false（绝不自残）」既有红线：返 false 不变，只去掉「撞自己配额还自升状态」的自残副作用。

#### Scenario: 配额到顶被拒不升级风控态

- **WHEN** 某 `normal` 账号的某动作在任一滑动窗（分钟 / 小时 / 天）配额耗尽，`record(action)` 被调用
- **THEN** `record` 返回 `false`，该账号风控态仍为 `normal`，`signal_count` 与 `last_signal_at` 均不变

#### Scenario: 反复撞同一配额不自锁

- **WHEN** 同一账号在短时间内连续多次撞同一配额（每次 `record` 均被拒）
- **THEN** 每次都返回 `false` 且风控态**始终**停在原状态，MUST NOT 出现 `normal→warned→restricted` 的自我升级

#### Scenario: 平台真实信号仍照常升级

- **WHEN** 边缘上报验证码 / 未知阻断浮层，云端据此对账号 `applySignal({kind:'confirmed'})` / `applySignal({kind:'light'})`
- **THEN** 威胁态照常升级（如 `normal`→`restricted` / `normal`→`warned`），证明去掉的只有「配额」这个假信号源、真信号驱动不受影响

### Requirement: 速率突发窗口饱和改道为低优先级运维告警

当 `RiskController.record(action)` 因**突发窗口**（小时或分钟）速率上限被拒时（`explain(action).reason` 为 `quota:hour` / `quota:minute`），云端 SHALL 发一条**低优先级运维告警**（经既有告警存储 `AlertStore.raise`，`type: pacing_saturation`，`severity` 取低档如 P2，带账号 + 动作 + 撞顶窗口），提示「该账号浏览 / 互动节奏过载、需调单场时长或停顿」。该告警 SHALL 按「账号 + 动作」冷却去重（冷却窗内同组合不重复落库）。

发该告警 MUST NOT 触碰风控状态单写路径（MUST NOT `applySignal` / `setQuotaLevel` / 改 `risk_state`）。**每日窗**（`quota:day`）饱和是预期的预算用尽，MUST NOT 触发该告警（只背压、静默）。

#### Scenario: 突发窗饱和发一条运维告警

- **WHEN** 某账号某动作撞小时（或分钟）突发上限、`record` 被拒
- **THEN** 云端经告警存储 raise 一条 `pacing_saturation` 低优先级告警（含账号 / 动作 / 窗口），可经 `GET /api/alerts` 与看板告警区读到

#### Scenario: 冷却窗内不重复告警

- **WHEN** 冷却窗内同一账号同一动作再次撞同一突发窗
- **THEN** 不重复 raise 告警（去重压制刷屏）

#### Scenario: 每日窗饱和不发告警

- **WHEN** 某账号某动作只是撞到**每日**上限（当日预算用尽）、`record` 被拒
- **THEN** 只返回 `false` 背压，MUST NOT raise `pacing_saturation` 告警

#### Scenario: 告警绝不改风控态

- **WHEN** `pacing_saturation` 告警被 raise
- **THEN** 归属账号的 `risk_state`（status 与 quotaLevel）不被改写，`applySignal` / `setQuotaLevel` 不被调用
