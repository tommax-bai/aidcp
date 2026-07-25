## MODIFIED Requirements

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

- **WHEN** 某账号当日已在 `dev` 上完成 N 次点赞，随后该账号改由 `ol` 的连接驱动、归属随握手切到 `ol`
- **THEN** `ol` 上该账号当日点赞计数 MUST 包含这 N 次
- **AND** MUST NOT 出现「换 target 后当日额度从零开始」或「两个 target 各得一份完整额度」
