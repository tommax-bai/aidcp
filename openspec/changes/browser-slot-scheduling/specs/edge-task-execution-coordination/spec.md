## MODIFIED Requirements

### Requirement: Browser-control-unavailable acquisition SHALL fail immediately and explicitly

Before quiescing browse or granting a task lease, edge task coordination MUST check browser-control readiness. If control is **genuinely unavailable or recovering** — that is, the browser is present but unhealthy — it MUST NOT acquire task ownership, MUST NOT dispatch a page-writing command, and MUST emit `edge.task.released` with reason `cdp_unhealthy` for the requested task id. This negative acknowledgement SHALL be idempotent and MUST NOT leave a queued or active lease behind.

**`cdp_unhealthy` MUST NOT be used for a deliberately parked (cold-standby) environment.** 浏览器被冷待机主动收起、且可被唤醒，这是一个**可恢复的缺席态**，不是控制通道故障；把它报成 `cdp_unhealthy` 是不诚实的（见「浏览器缺席 SHALL 走唤醒路径」）。

#### Scenario: Human publish arrives during CDP recovery
- **WHEN** a human-priority publish lease request arrives while the browser is present but browser control is recovering
- **THEN** the edge immediately returns `edge.task.released{reason:'cdp_unhealthy'}` without calling browse quiescence and without waiting for the normal acquire timeout

#### Scenario: Duplicate release after unhealthy rejection
- **WHEN** cloud later sends a release for a task already rejected as `cdp_unhealthy`
- **THEN** the edge responds idempotently and MUST NOT resume or freeze browse because of that duplicate release

#### Scenario: 停泊态绝不报成控制故障
- **WHEN** a lease request arrives for an environment that is in cold standby with the browser released
- **THEN** the edge MUST NOT return `cdp_unhealthy`; it takes the wake path instead

## ADDED Requirements

### Requirement: 浏览器缺席 SHALL 走唤醒路径而非直接判失败

任务受理 SHALL 把「浏览器缺席（冷待机已释放，可唤醒）」与「浏览器在但控制不健康」区分为**两个不同的态**。

收到租约请求时若浏览器缺席，Edge SHALL：请求唤醒 → 在唤醒死线内有界等待就绪 → 就绪后正常授予租约并执行。唤醒失败或判定进不了死线的，SHALL 回一个**独立的、机器可读的缺席/唤醒失败原因**（而非 `cdp_unhealthy`），并向运维如实呈现「正在唤醒 / 唤醒失败」。

任务受理、发布、浏览三类入站动作 MUST **全部**经过这道唤醒闸；MUST NOT 有任何一条入口在浏览器缺席时静默无动作，也 MUST NOT 有任何一条入口绕开闸直接摸浏览器。

#### Scenario: 任务受理唤醒停泊环境
- **WHEN** `edge.task.acquire` arrives for a parked environment
- **THEN** edge requests a wake, waits within the deadline, and grants the lease once the browser is ready

#### Scenario: 发布唤醒停泊环境
- **WHEN** a publish command arrives for a parked environment
- **THEN** edge takes the same wake path and MUST NOT silently no-op nor report a false browser fault

#### Scenario: 唤醒失败回诚实原因
- **WHEN** the wake fails or cannot complete within the deadline
- **THEN** edge returns a distinct wake-failure reason (not `cdp_unhealthy`), leaves no lease behind, and the operator-visible state says the wake failed

### Requirement: 浏览器释放与在跑租约 MUST 互斥

Edge SHALL 保证「释放浏览器层」与「持有任务租约」两者**不可同时成立**。

- 有租约在跑时 MUST NOT 释放浏览器（不得把浏览器从正在执行的任务底下抽走）；待机请求 SHALL 推迟到租约释放之后再判定。
- 浏览器缺席且唤醒未成功时 MUST NOT 授予租约。
- 若释放与授予发生竞态，Edge SHALL 以「不释放」为安全侧，并在租约结束后重新判定待机。

#### Scenario: 在跑租约期间拒绝释放
- **WHEN** a cold-standby release is attempted while a task lease is active
- **THEN** the release is deferred, the browser stays open, and standby is re-evaluated after the lease is released

#### Scenario: 唤醒未成功不授予租约
- **WHEN** a lease is requested and the wake does not reach browser-ready
- **THEN** no lease is granted and no page-writing command is dispatched

### Requirement: Edge SHALL 向云端如实区分「引擎在线」与「浏览器就绪」

Edge SHALL 在其上报的状态中把「引擎在线（云端连接存活）」与「浏览器就绪（可立即执行页面动作）」表达为**两个独立的事实**。停泊中的环境 SHALL 呈现为**在线但浏览器缺席**，MUST NOT 与「完全就绪」压成同一个态。

Edge SHALL 在 `hello` 中上报当刻的浏览器状态快照，并 SHALL 在同一 Cloud 连接内于浏览器状态发生变化后上报最新状态。状态上报只陈述 `absent | ready` 事实，MUST NOT 把「浏览器从未创建」表达成页面唤醒请求或伪造页面活动。重复上报同一状态 MUST 是幂等的。

#### Scenario: 停泊环境的在线态如实可辨
- **WHEN** an environment is parked in cold standby with an intact cloud connection
- **THEN** cloud can distinguish it from a fully-ready environment, and the operator UI shows it as parked rather than idle-ready

#### Scenario: 排队环境握手时浏览器从未创建
- **WHEN** an environment completes Cloud hello/welcome while waiting for a browser slot and no browser has been created
- **THEN** edge reports the engine as online and the browser as `absent`, without emitting a page wake intent or claiming page readiness

#### Scenario: 同一连接内浏览器就绪
- **WHEN** the slot queue releases the environment, the browser starts, and login plus account identity are verified without replacing the Cloud connection
- **THEN** edge reports `ready` on that connection exactly as a state transition, and duplicate ready observations do not create duplicate browser sessions
