## ADDED Requirements

### Requirement: Cloud SHALL be the single standby wait-threshold authority

Cloud SHALL be the sole policy authority for the browser cold-standby wait
threshold. Edge MUST use the validated `browserStandby.minWaitMs` from the
current Cloud hint when rechecking `wakeAt - now`; it MUST NOT combine that
value with an Edge default, persisted setting, or Edge environment override.
The visible local enable switch and all local execution safety gates remain
authoritative vetoes.

#### Scenario: Legacy Edge threshold does not override Cloud
- **WHEN** an upgraded client loads a legacy
  `browserColdStandbyMinWaitMs=1200000` value and receives a valid Cloud hint
  with `minWaitMs=300000`
- **THEN** Edge ignores the legacy value and evaluates the current remaining
  wait against 300000 milliseconds

#### Scenario: Delayed hint is rechecked against the Cloud threshold
- **WHEN** Edge receives or re-applies a valid eligible hint whose current
  `wakeAt - now` is shorter than that hint's `minWaitMs`
- **THEN** Edge rejects standby with `short_wait` even if the hint was eligible
  when Cloud generated it

#### Scenario: Missing Cloud threshold does not use a local fallback
- **WHEN** a standby hint is missing, malformed, or lacks a valid `minWaitMs`
- **THEN** Edge MUST revoke any cached hint and pending post-hold recheck for
  an awake browser and MUST NOT enter a new cold-standby cycle from that hint

#### Scenario: Invalid non-positive Cloud threshold is rejected
- **WHEN** a standby hint advertises `minWaitMs` below Cloud's supported
  positive threshold
- **THEN** Edge treats the hint as malformed and keeps an awake browser open

#### Scenario: Existing standby keeps its deterministic wake
- **WHEN** a browser is already in cold standby from a previously valid hint
  and a later snapshot omits or malforms `browserStandby`
- **THEN** Edge retains that cycle's existing wake timer, but the stale hint
  MUST NOT start another standby cycle after the browser wakes

#### Scenario: Legacy threshold cannot be re-persisted
- **WHEN** an upgraded client loads or is asked to save a settings object that
  contains `browserColdStandbyMinWaitMs`
- **THEN** the value has no runtime effect, is omitted from settings readback,
  and is omitted from the next successful settings write

## MODIFIED Requirements

### Requirement: Edge 仅在安全状态下关闭并按预测时间恢复

Edge SHALL treat `browserStandby` as advisory and perform local safety checks
before closing the browser. It MAY close the browser only when the hint is
valid and eligible, the visible local switch is enabled, the current remaining
wait meets the Cloud-advertised `minWaitMs`, the session is running/resting
without pending pause/close/remove/auth/blocker state, Cloud is connected, and
there is no known in-flight operation that requires the browser. Edge SHALL
keep the cloud engine connection intact where the core protocol supports it,
and SHALL restart/resume the environment at `wakeAt - warmupMs` or earlier if
manually requested.

#### Scenario: 安全长等待关闭浏览器并提前唤醒
- **WHEN** edge receives an eligible long-wait hint while the environment is
  safely idle or resting
- **THEN** edge closes the browser, records cold-standby status, and schedules
  wake before `wakeAt` by the configured warmup buffer

#### Scenario: 手工操作取消自动恢复
- **WHEN** an operator manually pauses, closes, removes, or restarts an
  environment while a cold-standby timer exists
- **THEN** edge cancels the cold-standby timer and does not perform the old
  automatic wake action

#### Scenario: 不安全状态拒绝关闭
- **WHEN** edge receives an eligible hint but the environment is closing,
  paused, occupied, auth-gated, blocked, removed, disconnected from Cloud, or
  has an unsafe in-flight operation
- **THEN** edge MUST NOT close the browser for cold standby and SHOULD expose a
  skipped reason for diagnostics

### Requirement: 云端发布浏览器冷待机提示（判据＝解除阻塞是否需要浏览器）

Cloud SHALL publish an optional `browserStandby` object on the existing
`ui.snapshot` stream whenever it can determine that automated browser work is
blocked by a wait that **does not require the browser to stay open in order to
be resolved**. The payload MUST include whether the feature is enabled, whether
the current wait is eligible, a machine-readable reason, `waitMs`, `wakeAt`,
`generatedAt`, `source`, `minWaitMs`, and `warmupMs`.

**准入判据 SHALL 是「解除这个阻塞需不需要浏览器」，MUST NOT 是「有没有确定的恢复时刻」。**
前一版判据（无确定恢复时刻即不让位）把**冻结账号**——等待最长、可能永远不再干活的那一类——
恰好排除在让位之外，使最不该占着浏览器的账号占得最牢。

- **需要浏览器才能解除的阻塞 MUST NOT 产出可待机提示**：验证码、登录、运维在浏览器里手动介入、
  未知的调度器状态、环境被他处占用。这些情形 MUST 保持既有的诚实告警 / 在线状态行为。

  **这一半 MUST 有真实输入，MUST NOT 只写在规范里。** 判据是「解除阻塞需不需要浏览器」，
  若系统只接了「不需要」那一半的证据、而「需要」那一半无人提供，判据就只剩半边，所有阻塞
  都会被当成「不需要浏览器」。**「需要浏览器」的事实 SHALL 由云端权威持有**（当前来源：
  该边缘是否正处于验证码暂停态），**MUST NOT 依赖边缘自报的浮层标志**——那个标志会被
  「浏览循环结束」等无关事件清掉。该闸 SHALL 压在**所有**停工来源之前一票否决：验证码期间，
  账号同样可能排期外 / 时长满 / 配额耗尽，若只在某一个来源分支上补闸，其余来源仍会让位。
- **不需要浏览器即可解除的等待 SHALL 产出可待机提示**（等待时长 ≥ 门槛时
  `eligible=true`），覆盖**全部**使账号停工的来源，而不只是风控配额：
  1. 风控配额窗口未释放（`source='risk'`，既有行为）
  2. 周历排期关闭 / 活跃时段窗口外（`source='session'`）
  3. 每日续场场数或累计分钟已满（`source='session'`）
  4. 风控状态 `restricted` / `frozen`（`source='risk'`，无固定恢复时刻，见下条 requirement）

**待机门槛 SHALL 由 Cloud 单一持有且默认 5 分钟。** Cloud MUST 将当前门槛写入
`browserStandby.minWaitMs`，Edge 不得持有另一份策略门槛。

#### Scenario: 排期外停工 SHALL 让出槽位
- **WHEN** 某账号因周历排期关闭或活跃时段窗口外而不再自动续场，距下一个可活跃时刻超过门槛
- **THEN** 云端产出 `browserStandby.eligible=true`、`source='session'`、`wakeAt`
  等于下一个可活跃时刻，边缘据此关闭浏览器让出槽位

#### Scenario: 每日时长跑满 SHALL 让出槽位
- **WHEN** 某账号当日续场场数或累计在线分钟已达上限，距下一个本地日界超过门槛
- **THEN** 云端产出 `browserStandby.eligible=true`、`source='session'`、`wakeAt`
  等于下一个本地日界

#### Scenario: 冻结账号 SHALL 让出槽位而非攥住
- **WHEN** 某账号风控状态为 `frozen`（或 `restricted` 致其不再续场），且解除该状态不需要浏览器
- **THEN** 云端产出 `browserStandby.eligible=true`，MUST NOT 因「没有确定的恢复时刻」
  而回退成 `eligible=false, waitMs=0`

#### Scenario: 需要浏览器才能解除的阻塞 MUST NOT 让位
- **WHEN** 账号需要过验证码、需要重新登录、或需要运维在浏览器里手动介入
- **THEN** 云端 MUST NOT 置 `eligible=true`，浏览器保持打开，既有的诚实告警行为不变

#### Scenario: 验证码把账号打成受限时 MUST NOT 让位
- **WHEN** 边缘上报验证码 → 风控信号把账号迁到 `restricted` → 续场闸据此判停工
- **AND** 该边缘正处于验证码暂停态
- **THEN** 云端 MUST 置 `eligible=false`、`reason='hard_blocker'`——**绝不能关掉运维
  正要去解验证码的那个浏览器**。注：`ui.snapshot` 有意豁免验证码暂停闸（它是界面数据、
  不是页面命令），故提示**会**送达该边缘；边缘侧的浮层标志会被「浏览循环结束」清掉，
  **MUST NOT 被当作这条的防线**。

#### Scenario: 验证码期间任何停工来源都 MUST NOT 让位
- **WHEN** 边缘正处于验证码暂停态，且该账号同时满足某个让位来源（排期外 / 每日上限已满 /
  配额耗尽 / 周历关闭）
- **THEN** 云端 MUST 一律置 `eligible=false`——该闸 SHALL 压在所有来源之前，
  MUST NOT 只补在受限那一支

#### Scenario: 验证码解除后恢复正常让位
- **WHEN** 验证码已解除，边缘不再处于暂停态，而账号仍因某个来源停工
- **THEN** 云端按正常判据产出可待机提示——该闸 MUST NOT 永久禁用让位

#### Scenario: 短等待不触发待机
- **WHEN** 距下一次可执行动作的预计等待时间低于门槛（默认 5 分钟）
- **THEN** 云端不产出可待机提示，或产出 `eligible=false` 且 `reason='short_wait'`

## REMOVED Requirements

### Requirement: 待机门槛的默认值 SHALL 两端一致

**Reason**: The duplicated Edge threshold is an invisible policy veto that can
survive upgrades and silently override current Cloud policy.

**Migration**: Cloud's existing `browserStandby.minWaitMs` becomes the sole
threshold. Upgraded Edge clients ignore the legacy persisted value and remove
it on the next successful settings save.
