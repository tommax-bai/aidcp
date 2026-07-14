# browser-cold-standby Specification

## Purpose
TBD - created by archiving change browser-cold-standby-next-action. Update Purpose after archive.
## Requirements
### Requirement: 云端发布确定性的浏览器冷待机提示

Cloud SHALL publish an optional `browserStandby` object on the existing `ui.snapshot` stream when it can determine that automated browser work is blocked by a finite, deterministic long wait. The payload MUST include whether the feature is enabled, whether the current wait is eligible, a machine-readable reason, `waitMs`, `wakeAt`, `generatedAt`, `source`, `minWaitMs`, and `warmupMs`. Cloud MUST NOT publish an eligible cold-standby hint for captcha, login, manual intervention, unknown scheduler state, occupied environments, or other hard blockers without a deterministic wake time.

#### Scenario: 长时间配额等待可进入冷待机
- **WHEN** an account is blocked from the next automated browser action by a quota/risk window that has a finite release time exceeding the cold-standby threshold
- **THEN** cloud publishes `browserStandby.eligible=true`, `reason` describing the deterministic blocker, and `wakeAt` equal to the forecasted release time

#### Scenario: 短等待不触发冷待机
- **WHEN** the next eligible browser action is delayed for less than the configured cold-standby threshold
- **THEN** cloud publishes no eligible hint, or publishes `eligible=false` with reason `short_wait`

#### Scenario: 硬阻塞不伪装成可恢复等待
- **WHEN** the account needs captcha, login, manual intervention, or another non-deterministic unblock
- **THEN** cloud MUST NOT set `browserStandby.eligible=true` and MUST preserve the existing honest warning/presence behavior

### Requirement: Edge 本地开关默认开启并可禁用

Edge SHALL include a browser cold-standby switch that defaults to enabled. The local switch MUST be able to disable cold standby even when cloud publishes an eligible hint, and disabling it MUST prevent browser close/restart automation caused by cold-standby hints.

#### Scenario: 默认开启
- **WHEN** the desktop app starts with no cold-standby override
- **THEN** the local cold-standby setting is enabled

#### Scenario: 本地禁用覆盖云端提示
- **WHEN** the local setting or environment override disables browser cold standby
- **AND** cloud publishes `browserStandby.eligible=true`
- **THEN** edge records/skips the hint but MUST NOT close the browser for cold standby

### Requirement: Edge 仅在安全状态下关闭并按预测时间恢复

Edge SHALL treat `browserStandby` as advisory and perform local safety checks before closing the browser. It MAY close the browser only when the hint is eligible, the local switch is enabled, the wait exceeds the local threshold, the session is running/resting without pending pause/close/remove/auth/blocker state, and there is no known in-flight operation that requires the browser. Edge SHALL keep the cloud engine connection intact where the core protocol supports it, and SHALL restart/resume the environment at `wakeAt - warmupMs` or earlier if manually requested.

#### Scenario: 安全长等待关闭浏览器并提前唤醒
- **WHEN** edge receives an eligible long-wait hint while the environment is safely idle or resting
- **THEN** edge closes the browser, records cold-standby status, and schedules wake before `wakeAt` by the configured warmup buffer

#### Scenario: 手工操作取消自动恢复
- **WHEN** an operator manually pauses, closes, removes, or restarts an environment while a cold-standby timer exists
- **THEN** edge cancels the cold-standby timer and does not perform the old automatic wake action

#### Scenario: 不安全状态拒绝关闭
- **WHEN** edge receives an eligible hint but the environment is closing, paused, occupied, auth-gated, blocked, removed, or has an unsafe in-flight operation
- **THEN** edge MUST NOT close the browser for cold standby and SHOULD expose a skipped reason for diagnostics

### Requirement: 协议兼容现有 ui.snapshot

The `browserStandby` payload SHALL be optional and backward compatible on `ui.snapshot`. Existing edge builds that ignore unknown fields MUST continue to process other snapshot fields, and new edge builds MUST sanitize the payload before forwarding it as structured UI events.

#### Scenario: 旧字段不受影响
- **WHEN** a `ui.snapshot` contains `browserStandby` together with existing fields such as presence and daily usage
- **THEN** daily usage, presence, and other existing UI behavior continue to work unchanged

