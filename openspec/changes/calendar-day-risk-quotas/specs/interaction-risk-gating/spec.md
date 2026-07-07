## ADDED Requirements

### Requirement: 每日配额窗口按本地自然日计算

云端风控 SHALL 将 `day` 配额窗口定义为 Asia/Shanghai 本地自然日（00:00:00 至次日 00:00:00），而不是最近 24 小时滑动窗口。`minute` 与 `hour` 配额窗口 SHALL 继续使用滑动窗口，用于短时突发保护。所有 `RiskController.explain(action)`、`canDo(action)`、`dailyRemaining(action)`、`quotaReleaseAfterMs(action,'day')` 与 UI `dailyUsage.windows.day` 的饱和 / 恢复时间 MUST 使用同一自然日口径。

#### Scenario: 昨天的浏览不占今天每日配额

- **WHEN** 某账号昨天 17:59 已经浏览到 150 次，今天 00:00 后仅浏览 76 次
- **THEN** `RiskController.explain('view')` MUST 按今天自然日计数，允许继续浏览，MUST NOT 因最近 24 小时达到 150 而返回 `quota:day`

#### Scenario: 今日每日配额满后等下个本地午夜恢复

- **WHEN** 某账号在 Asia/Shanghai 当天自然日内 `view` 已达到 day quota
- **THEN** `RiskController.explain('view')` MUST 返回 `allowed:false` 与 `reason:'quota:day'`
- **AND** 其 `retryAfterMs` / `quotaReleaseAfterMs('view','day')` MUST 指向下一个 Asia/Shanghai 本地 00:00，而不是最早事件的 24 小时滑出时间

#### Scenario: 分钟和小时仍按滑动窗口限突发

- **WHEN** 某账号在一分钟或一小时内达到对应 burst quota
- **THEN** `RiskController.explain(action)` MUST 继续按滑动窗口返回 `quota:minute` 或 `quota:hour`，其释放时间仍为最早相关事件滑出该窗口的时间

## MODIFIED Requirements

### Requirement: 安全限额数字可在管理后台按档位配置且 canDo 每次读最新

云端的安全限额**数字**（每账号每动作的分钟 / 小时滑动突发配额，以及 Asia/Shanghai 自然日每日配额）SHALL 为可配置、可在管理后台按风控档位（conservative / normal / aggressive）编辑，且**每日上限与分钟 / 小时突发上限都 SHALL 独立可编辑**（突发上限 MUST NOT 仅由每日值派生）。云端 SHALL 把这些数字落库（新增 `quota_config` 表，迁移 `0010`，主键 `(tier, action)`，含 `daily` / `per_minute` / `per_hour` 三列）并维护内存镜像；`RiskController.canDo(action)` 经 `effectiveQuotas()` MUST **每次现读**当前生效数字（经注入的配额提供者读内存镜像），使管理后台改完即热加载生效、MUST NOT 需要重启进程。

绝不 brick（never-brick）：当配额提供者缺失、某 `(tier, action)` 缺行、或字段非有限非负整数时，`effectiveQuotas()` MUST 回落到代码写死默认（`quotas.ts` 的 `DAILY_QUOTAS` / `MINUTE_BURST_CAP` / `HOUR_BURST_CAP`），MUST NOT 抛错、MUST NOT 让风控闸失效。配额表为空（如迁移刚跑完）时行为 MUST 与现状逐位一致（零回归）。`warned` / `restricted` / `frozen` 状态对基准三档的缩放 / 清零语义 MUST 保持不变，只是基准三档数字来源改为提供者（缺值回落写死默认）。

#### Scenario: 后台改某档某动作每日上限，下一次 canDo 即按新值

- **WHEN** 管理后台把 `normal` 档 `comment_like` 的每日上限从 6 改为 4 并保存成功
- **THEN** 无需重启，该账号下一次 `canDo('comment_like')` 的自然日每日窗判定按 4 生效（命中即热加载）

#### Scenario: 分钟 / 小时突发上限独立可改、不由每日派生

- **WHEN** 管理后台单独调高某档某动作的分钟突发上限、不改其每日上限
- **THEN** `effectiveQuotas()` 的分钟窗数字按所配值生效，且每日窗数字不被该改动连带改变

#### Scenario: 缺行 / 非法值回落写死默认、绝不 brick

- **WHEN** 某 `(tier, action)` 在 `quota_config` 缺行，或其某窗口字段为非有限非负整数
- **THEN** `effectiveQuotas()` 对该动作回落 `quotas.ts` 写死默认、不抛错，风控闸照常工作

#### Scenario: 配额表为空时与现状逐位一致

- **WHEN** `quota_config` 表无任何行（如迁移刚跑完）
- **THEN** `effectiveQuotas()` 在每个状态 / 档位下产出的三窗口数字与改造前（`deriveWindowQuotas` 写死默认）逐位相同

### Requirement: 速率配额饱和是节奏背压、不是风控状态输入

账号威胁态（`normal` / `warned` / `restricted` / `frozen`）MUST 只由**平台可观测信号**驱动升级：验证码 → 强信号（`confirmed`）、未知阻断浮层 → 软信号（`light`）、运营手动信号（`manual_restrict` / `manual_freeze` / `operator_override_recover`）。

`RiskController.record(action)` 因**速率配额**耗尽而被 `canDo` 拒时 MUST 只返回 `false`（背压），MUST NOT 触发任何风控状态迁移——具体地：MUST NOT `applySignal`、MUST NOT 递增 `signal_count`、MUST NOT 刷新 `last_signal_at`、MUST NOT 把账号从 `normal` 推向 `warned` / `restricted`。`quota_exceeded` MUST NOT 作为风控信号种类存在于状态机升级逻辑与 `RiskSignalKind` 中。这里的速率配额包括分钟 / 小时滑动突发窗口与 Asia/Shanghai 自然日每日窗口。

此要求**强化**「被禁账号 `record` 返回 false（绝不自残）」既有红线：返 false 不变，只去掉「撞自己配额还自升状态」的自残副作用。

#### Scenario: 配额到顶被拒不升级风控态

- **WHEN** 某 `normal` 账号的某动作在任一配额窗口（分钟 / 小时滑动窗口或自然日每日窗口）配额耗尽，`record(action)` 被调用
- **THEN** `record` 返回 `false`，该账号风控态仍为 `normal`，`signal_count` 与 `last_signal_at` 均不变

#### Scenario: 反复撞同一配额不自锁

- **WHEN** 同一账号在短时间内连续多次撞同一配额（每次 `record` 均被拒）
- **THEN** 每次都返回 `false` 且风控态**始终**停在原状态，MUST NOT 出现 `normal→warned→restricted` 的自我升级

#### Scenario: 平台真实信号仍照常升级

- **WHEN** 边缘上报验证码 / 未知阻断浮层，云端据此对账号 `applySignal({kind:'confirmed'})` / `applySignal({kind:'light'})`
- **THEN** 威胁态照常升级（如 `normal`→`restricted` / `normal`→`warned`），证明去掉的只有「配额」这个假信号源、真信号驱动不受影响
