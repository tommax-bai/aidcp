## MODIFIED Requirements

### Requirement: cloud 必须等待 edge acquired/quiesced 再发首条业务命令

protocol v2 SHALL 提供 `task.acquire`、`task.acquired`、`task.release`、`task.released`。cloud 发出 acquire 后 MUST 等 edge 回 `acquired`；该回执同时表示当前浏览原子动作已到安全边界、未开始的普通浏览命令已取消且租约已经生效。未收到 acquired 时 MUST NOT 下发该任务第一条业务命令。每个 acquire MUST 携可选的本地等待时长；edge MUST 从收到申请起在该时长内完成 quiesce 并授予租约，逾期仍未授予时 MUST 取消该排队申请，MUST NOT 在 cloud 已超时后再授予无主租约。

#### Scenario: 在途 {platform}.navigation.back 先收尾
- **WHEN** `{platform}.navigation.back` 已在 edge 执行中，cloud 申请发布租约
- **THEN** edge 等该原子动作收敛到安全边界后才回 `task.acquired`，cloud 随后才发 `navigate_entry`

#### Scenario: acquire 超时不越权发布
- **WHEN** 目标 edge 离线、协议过旧或在超时内未回 acquired
- **THEN** 发布/评论任务诚实失败或保持可重试状态，且零条业务写命令被下发，MUST NOT 回退到无租约执行

#### Scenario: edge 等待期届满不授予陈旧任务
- **WHEN** 普通浏览原子动作持续到 acquire 的本地等待上限之后
- **THEN** edge 移除该未获授任务、回到可继续协调的状态，MUST NOT 在上限之后发送 `acquired` 或持有该任务租约

### Requirement: 抢占浏览取消陈旧待执行命令而非排空队列

普通浏览 SHALL 是低优先级、可抢占执行流。独占任务申请到达时，edge MUST 允许已经开始的原子动作完成或**在其安全取消点中止**；所有尚未开始且不属于当前租约的普通浏览命令 MUST 被取消，MUST NOT 为了“FIFO”先排空旧浏览队列。任务释放后 MUST 依据当前真实页面重新上报并由 cloud 重决策，MUST NOT 重放被取消的旧命令。

**「安全取消点」SHALL 定义为**：一条命令从进入执行到它**第一次真正改写页面**之前的整段，具体包含且不限于——阻断浮层等待（等验证码 / 登录 / 风控浮层消失）、动作之间的最短间隔、动作前的犹豫停顿、离页前的停留。**这一整段 MUST NOT 计入页面写原子区**：它只消耗时间，平台侧零副作用。

**交接（quiesce）MUST 只等待正在改写页面的动作，MUST NOT 等待任何纯等待。** 停在安全取消点上的命令，MUST 在接管信号到达时当场作废、当场让路。

（该定义是本 change 的核心。前一版 spec 已经写下「或在其定义的安全取消点中止」，但从未定义这个术语——实现遂把「等验证码」也算成了不可中断的原子动作，造成硬死锁：交接无超时地等一条正在等验证码的命令，而那个验证码只有这次交接要授予的协助任务才能点掉。）

#### Scenario: 停在浮层闸上的命令当场让路
- **WHEN** 一条普通浏览命令停在阻断浮层等待里（尚未发生任何页面写），此时验证码人工协助申请租约
- **THEN** 交接 MUST 立即收敛（不等该命令的浮层等待自然结束）；该命令 MUST 零页面副作用地作废并回一条诚实失败回执；接管信号之后 MUST 记录到零次页面改写调用

#### Scenario: 停在离页停留上的命令当场让路
- **WHEN** 一条关闭 / 返回命令正停在离页停留（云端下发了较长的停留预算），此时更高档位任务申请租约
- **THEN** 交接 MUST 立即收敛，MUST NOT 等停留跑满

#### Scenario: 队列中旧滚动被取消
- **WHEN** 当前动作执行中且队列还等待 `{platform}.feed.scroll`、`{platform}.navigation.back`，此时发布申请租约
- **THEN** 当前动作到安全边界后发布获租约，两个未开始命令被取消且释放后不重放

#### Scenario: 释放后以新快照恢复
- **WHEN** 独占任务结束且没有下一独占任务等待
- **THEN** edge 回到可浏览页面、上报新 `page.cards`/页面快照，cloud 基于新状态生成后续动作

### Requirement: 任务命令必须归属于当前租约

独占任务的每条页面写命令 SHALL 携 `taskId`。edge MUST 只执行 `taskId` 等于当前租约所有者的命令；无 `taskId`、错 `taskId`、已释放或已过期租约的命令 MUST 被拒绝或丢弃并留下可观测失败，MUST NOT 改写页面。发布原子命令 MUST 返回明确失败结果；无逐命令回执的浏览协议命令由 cloud 有界等待超时收敛为失败。

#### Scenario: 迟到的发布命令不污染下一任务
- **WHEN** 发布 A 已释放，发布 B 已获租约，随后到达 A 的迟到 `{platform}.publish.command`
- **THEN** edge 返回 `task_lease_mismatch` 且不执行该命令，B 的页面状态不被污染

#### Scenario: 租约期间普通浏览命令被挡住
- **WHEN** 发布租约有效时到达一个没有 `taskId` 的 `{platform}.feed.scroll`
- **THEN** edge 不执行、不入待重放队列并记录被租约抑制，发布序列继续独占

### Requirement: Browser-control-unavailable acquisition SHALL fail immediately and explicitly

Before quiescing browse or granting a task lease, edge task coordination MUST check browser-control readiness. If control is recovering or unavailable, it MUST NOT acquire task ownership, MUST NOT dispatch a page-writing command, and MUST emit `task.released` with reason `cdp_unhealthy` for the requested task id. This negative acknowledgement SHALL be idempotent and MUST NOT leave a queued or active lease behind.

#### Scenario: Human publish arrives during CDP recovery
- **WHEN** a human-priority publish lease request arrives while browser control is recovering
- **THEN** the edge immediately returns `task.released{reason:'cdp_unhealthy'}` without calling browse quiescence and without waiting for the normal acquire timeout

#### Scenario: Duplicate release after unhealthy rejection
- **WHEN** cloud later sends a release for a task already rejected as `cdp_unhealthy`
- **THEN** the edge responds idempotently and MUST NOT resume or freeze browse because of that duplicate release
