## ADDED Requirements

### Requirement: 账号风险状态的写入者在任一时刻全局唯一

The system SHALL 保证：对任一 `accountId`、任一时刻，`risk_state` 的写入者唯一。「唯一」的判据 MUST 是**跨进程**的，MUST NOT 只在单进程内成立。

该不变量由三条机制共同保证，三条都是 MUST：

1. **每 target 单实例**：承载风控写路径的自动化进程对每个 `executionTarget` MUST 单实例，并 MUST 在启动时以数据库层的互斥手段（会话级 advisory lock，键含 `executionTarget`）取得「自动化写者锁」。取不到锁 MUST 在有界等待后拒绝启用风控写路径并告警，MUST NOT 降级为无锁继续写。持锁连接断开即视为写权丢失，MUST 停止下发新的互动命令并告警，MUST NOT 静默继续写 `risk_state`。
2. **账号归属唯一**：每个账号在任一时刻 MUST 只归属一个 `executionTarget`（见 `same-account-parallel-safety`）。
3. **条件写 + 诚实拒绝**：`risk_state` 的每一次写 MUST 带属主谓词（写方的 `executionTarget` 必须等于该账号的归属 target），影响行数为 0 时 MUST 作为显式失败上报，MUST NOT 返回成功、MUST NOT 重试覆盖、MUST NOT 通过放宽谓词绕过。

写失败为「非属主」时，该进程 MUST 驱逐本地缓存的该账号控制器并告警；下次解析该账号 MUST 从库重新加载状态与计数。

`risk_counters` 属于 append-only 的既成事实账本，MUST NOT 加属主谓词、MUST NOT 按 `executionTarget` 分裂成多份。同一账号的当日额度 MUST 只有一份：归属变更前后飞在半路的回执 MUST 记进同一本账，MUST NOT 因换了写入进程而各算一份。

#### Scenario: 同一 target 的第二个实例拒绝启动

- **WHEN** 某 `executionTarget` 已有一个自动化进程持有写者锁，运维以滚动或蓝绿方式启动第二个同 target 实例
- **THEN** 第二个实例在有界等待后取不到写者锁，MUST 拒绝启用风控写路径并以非零码退出，MUST 产生指明「另一实例正持锁」的告警
- **AND** 它 MUST NOT 以无锁方式启动风控写路径或 outbox apply

#### Scenario: 非属主进程的状态写被数据库拒绝

- **WHEN** 某账号归属 `ol`，而 `dev` 的进程（例如经面板首页汇总物化的陈旧控制器）尝试写该账号的 `risk_state`
- **THEN** 该写的影响行数为 0，MUST 作为 `risk_state_not_owned` 显式失败上报，附带真实归属 target
- **AND** 该账号刚被 `ol` 写下的 `restricted` MUST 保持不变，MUST NOT 被陈旧的 `normal` 覆盖

#### Scenario: 拒绝后驱逐缓存而不是重试

- **WHEN** 一次状态写因非属主被拒
- **THEN** 该进程 MUST 从控制器缓存中移除该账号并告警
- **AND** MUST NOT 重试同一次写，MUST NOT 在移除后立刻用同一份陈旧内存状态重建控制器

#### Scenario: 归属变更不清零也不翻倍当日额度

- **WHEN** 某账号当日已在 `dev` 上完成 N 次点赞，随后归属被显式改为 `ol`
- **THEN** `ol` 上该账号当日点赞计数 MUST 包含这 N 次
- **AND** MUST NOT 出现「换 target 后当日额度从零开始」或「两个 target 各得一份完整额度」

### Requirement: 配额判定依据的计数必须与库内事实一致

配额准入判定所依据的计数 SHALL 与 `risk_counters` 的库内事实一致。系统 MUST 具备检出二者偏差的机制，MUST NOT 让「内存计数只在控制器创建时回放一次、此后只累加本进程自己写的那些」这一事实成为不可观测的默认状态。

具体要求：

- 控制器建立时 MUST 从库回放当日窗口计数；账号归属被本实例占位成功、或归属变更后重新解析控制器时，MUST 强制重放，MUST NOT 复用可能陈旧的内存值。
- 系统 MUST 周期性地把内存计数与库内当日总量对账。判据 MUST 是「偏差是否为零」，MUST NOT 引入容忍阈值。
- 偏差非零 MUST 告警（含 accountId、动作、内存值、库值）并以库为准重建该账号计数，MUST NOT 静默沿用偏差计数继续做准入判定。

#### Scenario: 外部写入的计数行被对账检出

- **WHEN** 某账号的 `risk_counters` 中出现一行不是由本进程内存计数产生的当日记录
- **THEN** 下一次对账 MUST 检出偏差并告警
- **AND** 该账号的内存计数 MUST 被以库为准重建，重建后与库内当日总量逐项相等

#### Scenario: 归属占位后强制重放

- **WHEN** 某账号首次在本 target 上握手成功并被本实例占位归属
- **THEN** 该账号的计数 MUST 从库重放一次
- **AND** MUST NOT 直接使用握手前可能已存在的内存计数

#### Scenario: 对账不放宽到阈值

- **WHEN** 内存计数与库内当日总量相差 1
- **THEN** 系统 MUST 按偏差处理（告警 + 重建）
- **AND** MUST NOT 因差值小而判为一致

### Requirement: 边缘确认的真实动作必须先落持久 outbox 再推进

云端 SHALL 在收到边缘对真实平台动作的确认回执后，**先把该既成事实同步提交进一张带 `execution_target` 的持久 outbox 表，再推进浏览闭环**。该路径 MUST NOT 依赖进程内事件总线上的 fire-and-forget 异步写，MUST NOT 以「异常只记日志」的方式吞掉记账失败。

具体要求：

- outbox 行 MUST 带 `execution_target`（服务端注入），worker MUST 只认领本 target 的行；MUST 带去重键，边缘重发同一回执信封 MUST 只产生一行。
- 认领 MUST 使用认领令牌 + 租约 + 跳锁，并 MUST 在进程启动时回收租约过期的在途行——与委托任务 worker 同一范式。
- apply MUST 在单个数据库事务内同时完成「写入计数」与「标记 outbox 行已应用」，且 MUST 由数据库唯一约束保证 exactly-once，MUST NOT 用进程内集合去重。
- 内存计数 MUST 只在 apply 成功时递增，且 MUST 只有这一条递增路径（回执处理时 MUST NOT 先加一次）。
- 入队失败 MUST 视为本次记账失败：MUST 告警，并 MUST 使该账号停止继续下发自动互动命令，MUST NOT 当作无事发生继续浏览闭环。
- 重试 MUST 有界；超限 MUST 转入死信并告警，MUST NOT 静默丢弃。outbox 积压量与死信量 MUST 可被读取。

#### Scenario: 崩在回执与记账之间不丢账

- **WHEN** 边缘确认了一次真实点赞，云端提交了 outbox 行，随后进程在 apply 之前崩溃并重启
- **THEN** 重启后该行被回收并 apply，该次点赞 MUST 出现在计数里
- **AND** 该次点赞 MUST 只被计入一次

#### Scenario: 重复投递只记一次

- **WHEN** 边缘因重连重发了同一条动作确认信封
- **THEN** outbox MUST 只保留一行，计数 MUST 只增加一次

#### Scenario: 入队失败不静默继续

- **WHEN** 一次真实动作已被边缘确认，但 outbox 入队因数据库不可写而失败
- **THEN** 系统 MUST 告警并停止对该账号继续下发自动互动命令
- **AND** MUST NOT 把这次已发生的动作当作不存在而继续浏览闭环

#### Scenario: 超限进死信且可见

- **WHEN** 某条 outbox 行的 apply 连续失败达到重试上限
- **THEN** 该行 MUST 转入死信状态并产生告警
- **AND** 死信数量 MUST 可被读取，MUST NOT 被静默删除

#### Scenario: 记账不改变判定语义

- **WHEN** 一次动作的回执抵达时该账号配额已耗尽
- **THEN** 该动作 MUST 照常入队并最终计入（既成事实照记，与既有「绝不因策略事后重判而丢弃」一致）
- **AND** 节奏饱和告警所依据的判定 MUST 仍取自写入前的判定值，MUST NOT 改为读取含这一笔的新状态
