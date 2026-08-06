## MODIFIED Requirements

### Requirement: Edge 仅在安全状态下关闭并按预测时间恢复

Edge SHALL treat `browserStandby` as advisory and perform local safety checks
before closing the browser. It MAY close the browser only when the hint is
valid and eligible, the visible local switch is enabled, the current remaining
wait meets the Cloud-advertised `minWaitMs`, and every local safety check
passes. Edge SHALL keep the cloud engine connection intact where the core
protocol supports it, and SHALL restart/resume the environment at
`wakeAt - warmupMs` or earlier if manually requested.

The local safety checks SHALL be evaluated **only** against facts that are
verifiable at decision time — the core child process is alive, the cloud engine
link is connected, the automation intent is neither paused nor stopped, and
there is no in-flight operation that requires the browser.

Every input to the admission decision SHALL have a demonstrable live source on
**every supported platform**, and that source SHALL be pinned by a regression
assertion. Edge MUST NOT gate admission on a lifecycle label whose only writer
has been retired on the platform in question: such a label freezes at whatever
value it was last given, and a stale value there silently converts a
recoverable wait into a permanently held browser slot with no diagnostic trace.
In particular, the browse-session lifecycle label — whose only writers are
log-phrase matches emitted by the retired page-automation path — MUST NOT be an
admission condition.

Having a live writer is a **necessary but not sufficient** condition for
admission input. The browse-session lifecycle label SHALL remain excluded from
the admission decision **even after it is rewired to a live structured source**,
and re-adding it SHALL require amending this requirement rather than citing the
restored writer. The governing reason is not whose writer is alive: that label
describes the target's **posture** (whether a browse round happens to be running
right now), not the target's **identity** (which environment and account would
be acted upon). Per the stop-or-continue criterion, a posture condition MUST NOT
by itself be grounds for refusing to act; only an identity condition may be.

#### Scenario: 安全长等待关闭浏览器并提前唤醒
- **WHEN** edge receives an eligible long-wait hint while the environment is
  safely idle or resting
- **THEN** edge closes the browser, records cold-standby status, and schedules
  wake before `wakeAt` by the configured warmup buffer

#### Scenario: 推断出来的生命周期标签陈旧时仍然让位
- **WHEN** edge receives an eligible long-wait hint while the core process is
  alive, the cloud engine link is connected, and automation is neither paused
  nor stopped, but a log-derived lifecycle label still carries a stale value
  such as `idle`
- **THEN** edge closes the browser for cold standby anyway, because that label
  is not an admission condition

#### Scenario: 会话轴接上活写入方之后仍不得进入准入闸
- **WHEN** the browse-session lifecycle label is rewired to a live structured
  session source that is written on every supported platform, and that label
  reports no browse round in progress while an eligible long-wait hint arrives
- **THEN** admission SHALL be decided without consulting that label, and edge
  SHALL close the browser for cold standby exactly as it would have before the
  rewiring
- **AND** a structural assertion SHALL fail if that label reappears among the
  admission inputs

#### Scenario: 手工操作取消自动恢复
- **WHEN** an operator manually pauses, closes, removes, or restarts an
  environment while a cold-standby timer exists
- **THEN** edge cancels the cold-standby timer and does not perform the old
  automatic wake action

#### Scenario: 不安全状态拒绝关闭
- **WHEN** edge receives an eligible hint but the environment is closing,
  paused, occupied, auth-gated, blocked, removed, disconnected from Cloud, or
  has an unsafe in-flight operation
- **THEN** edge MUST NOT close the browser for cold standby and MUST expose a
  named skipped reason for diagnostics
