## MODIFIED Requirements

### Requirement: Edge 仅在安全状态下关闭并按预测时间恢复

Edge SHALL treat `browserStandby` as advisory and perform local safety checks before releasing the browser. It MAY enter standby only when the hint is eligible, the local switch is enabled, the wait exceeds the local threshold, the session is running/resting without pending pause/close/remove/auth/blocker state, and **no task lease is active**.

进入待机时 Edge SHALL **释放全部本地浏览器句柄**——断开浏览器控制连接、退订依赖浏览器的监测体、清除页面/目标引用、关闭浏览器——并 SHALL **保留核心进程与云端连接**。释放前 MUST 先按既有排空契约把浏览循环有界排空。释放 MUST NOT 留下任何仍被长期存活组件持有的过期浏览器句柄。

Edge SHALL 在 `wakeAt - warmupMs`、或**更早的按需唤醒触发**（见「按需唤醒」）时恢复；恢复 MUST 走原地重建，MUST NOT 通过重启核心进程实现。

#### Scenario: 安全长等待释放浏览器层并计划唤醒
- **WHEN** edge receives an eligible long-wait hint while the environment is safely idle or resting and no task lease is active
- **THEN** edge drains the browse loop, releases every local browser handle, closes the browser, keeps the core process and cloud connection alive, records cold-standby status, and schedules wake before `wakeAt` by the configured warmup buffer

#### Scenario: 在跑租约阻止释放
- **WHEN** an eligible hint arrives while a task lease is active
- **THEN** edge MUST NOT release the browser and SHALL re-evaluate standby after the lease is released

#### Scenario: 手工操作取消自动恢复
- **WHEN** an operator manually pauses, closes, removes, or restarts an environment while a cold-standby timer exists
- **THEN** edge cancels the cold-standby timer and does not perform the old automatic wake action

#### Scenario: 不安全状态拒绝关闭
- **WHEN** edge receives an eligible hint but the environment is closing, paused, occupied, auth-gated, blocked, removed, or has an unsafe in-flight operation
- **THEN** edge MUST NOT release the browser for cold standby and SHOULD expose a skipped reason for diagnostics

## ADDED Requirements

### Requirement: 唤醒 SHALL 原地重建浏览器层、绝不重启核心进程

从冷待机唤醒时 Edge SHALL 在**不重启核心进程、不断开云端连接**的前提下重建浏览器层：重新拉起浏览器 → 重新建立控制连接 → **重新确认登录态与账号身份** → 重新挂载依赖浏览器的监测体。

重建 SHALL 被视为**新的一代浏览器**：MUST NOT 假设仍处于登录态，MUST NOT 复用释放前缓存的任何浏览器侧状态。重建 SHALL 幂等——重复触发不得产生第二个浏览器或第二组监测体。

重建失败 SHALL **诚实报错**并保持待机态（可再次唤醒），MUST NOT 伪装成已就绪，MUST NOT 静默降级为进程重启。

#### Scenario: 唤醒不掀桌子
- **WHEN** a parked environment is woken
- **THEN** the core process is not terminated, the cloud WebSocket is not dropped, and the browser layer is rebuilt in place

#### Scenario: 重建后不假设仍登录
- **WHEN** the browser layer is rebuilt
- **THEN** edge re-verifies login state and account identity before reporting browser readiness, and MUST NOT report ready on the basis of pre-release cached state

#### Scenario: 重建失败诚实回退待机
- **WHEN** rebuilding the browser fails (launch failure, control connect failure, or login gate)
- **THEN** edge reports the failure honestly, remains in standby, and MUST NOT report the environment as ready

### Requirement: 按需唤醒 SHALL 由任务触发、有界、且失败诚实

除按预测时间唤醒外，Edge SHALL 支持**按需唤醒**：任何需要浏览器的入站动作（浏览命令、任务受理、发布）在浏览器缺席时 SHALL 触发唤醒并**有界等待**其就绪，等待上限默认 **180 秒**（可配），且 MUST 小于云端空转看门狗阈值。

排队等待 SHALL 计入该死线。若在触发时即可判定无法在死线内就绪（如队列过长、内存准入不通过），Edge SHALL **立即诚实失败**，MUST NOT 吊住调用方直到超时。

唤醒成功后动作照常执行；动作完成后 Edge SHALL **重新按待机规则判定**是否再次停泊，MUST NOT 无条件立刻关闭（唤醒即关是浪费），也 MUST NOT 无条件保持打开（占着槽位是浪费）。

#### Scenario: 任务唤醒已停泊的浏览器
- **WHEN** a task or publish command arrives for a parked environment
- **THEN** edge requests a wake, waits within the deadline for the browser to become ready, and then executes the action

#### Scenario: 判定进不了死线立即失败
- **WHEN** a wake is requested but the serial launch queue or memory admission makes readiness within the deadline impossible
- **THEN** edge fails the request honestly and immediately with a machine-readable reason, and MUST NOT block until the deadline expires

#### Scenario: 任务完成后重判待机
- **WHEN** a woken environment finishes the task it was woken for
- **THEN** edge re-evaluates the standby rule: it parks again if a long deterministic wait still applies, and otherwise keeps the browser open
