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

## ADDED Requirements

### Requirement: 拒绝让位 MUST 留痕，且连续拒绝 MUST 与单次拒绝可分辨

每一次拒绝进入冷待机 SHALL 在该环境的待机状态上留下**具名原因**，并 SHALL 同时记录
**连续拒绝次数**与**首次连续拒绝时刻**；该原因与计数 SHALL 在开发者详情中可读。Edge
SHALL 另按环境记录一行日志，使拒绝在事后可回溯。

留痕 MUST 覆盖全部拒绝理由，MUST NOT 只覆盖其中一部分。单次拒绝是正常的（例如刚醒来
不足最短持有时长），而**连续拒绝**意味着该环境正在无限期占用一个浏览器槽位；二者若在
呈现与日志上长得一样，运营就无法把后者识别出来。

一次成功进入冷待机、或提示转为不再 eligible，SHALL 重置连续拒绝计数。

#### Scenario: 单次拒绝留下具名原因
- **WHEN** edge evaluates an eligible hint and any local safety check fails
- **THEN** edge records the named refusal reason on that environment's standby
  status and writes one per-environment log line, without closing the browser

#### Scenario: 连续拒绝可被识别
- **WHEN** edge refuses the same environment on consecutive hints
- **THEN** the recorded state carries a consecutive-refusal count and the
  timestamp of the first refusal in that streak, so an environment that has
  been holding a browser slot for many consecutive hints is distinguishable
  from one that refused once

#### Scenario: 让位成功后计数复位
- **WHEN** an environment enters cold standby, or a subsequent hint reports the
  environment as no longer eligible
- **THEN** the consecutive-refusal count and streak start time are reset

### Requirement: 进入冷待机失败 MUST NOT 把健康环境打成暂停态

核心侧拒绝或未能完成进入冷待机时，Edge SHALL 留在**浏览器仍然开启**的运行态，记录一条
具名的、**可重试**的失败，并 SHALL 在后续提示到达时重新判定。Edge MUST NOT 因此把该
环境写成暂停态。

「此刻不能待机」是非结构性的——同一步在下一次提示上重来完全可能成功。把它落成暂停态
会让一个健康环境永久占住浏览器槽位，并被排除出等槽位队列：这比不尝试待机更坏，而本次
改动正是要让待机尝试变得频繁得多。

#### Scenario: 核心拒绝进入待机
- **WHEN** the shell asks the core to enter cold standby and the core does not
  confirm
- **THEN** the environment stays in its running state with the browser open, a
  named retryable failure is recorded, and the next eligible hint is evaluated
  again

### Requirement: 冷待机期间被拒绝的浏览器命令 MUST NOT 静默丢弃

浏览器已因冷待机关闭时收到需要浏览器的命令，Edge SHALL 以具名原因如实拒绝并留痕，
MUST NOT 静默丢弃。该拒绝 SHALL 与「已执行」在本地呈现上可分辨。

#### Scenario: 待机期间收到浏览器命令
- **WHEN** the browser is closed for cold standby and a command requiring the
  browser arrives
- **THEN** edge refuses it with a named reason and records that refusal, rather
  than dropping it without a trace
