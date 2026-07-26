## ADDED Requirements

### Requirement: worker 重启必须回收上一进程遗留的执行 claim

Cloud 委托 worker 每次启动时 MUST 在接受新任务前回收数据库中属于已退出进程的 `planning` / `executing` claim，MUST NOT 让它们停留到任务 deadline 才释放 ownership。恢复 MUST 写入可审计事件，并保留原状态与旧 claim 事实。

#### Scenario: executing 在 Cloud 重启后进入对账

- **WHEN** Cloud 在一个委托任务处于 `executing` 时重启
- **THEN** 新 worker 在领取普通队列任务前 SHALL 清除旧 claim 并把该任务送入 attempt 对账
- **AND** 该任务 MUST NOT 继续以旧 `executing` 身份占用 ownership

#### Scenario: 当前进程的慢任务不被租约扫描误杀

- **WHEN** 一个真实在跑的生成超过 claim 租约但 Cloud 进程没有重启
- **THEN** worker MUST NOT 仅因租约时刻已过就在周期 poll 中回收该任务

### Requirement: 中断 attempt 必须按派发证据分流

重启恢复 SHALL 使用持久化 attempt 状态区分是否已经派发。`prepared` 证明零派发时 SHALL 撤销临时账本并归还尝试预算；`dispatched` 且缺少可核验终局时 MUST 走结果未知对账并停止盲重试，MUST NOT 编造干净失败或成功。

#### Scenario: prepared attempt 安全返回队列

- **WHEN** 重启遗留任务只有一个 `prepared` attempt，且没有 `dispatched_at`
- **THEN** worker SHALL 丢弃该临时 attempt、归还 attemptCount 并允许任务重新排队
- **AND** MUST NOT 将其描述为已派发或结果未知

#### Scenario: dispatched attempt 无证据时诚实终结

- **WHEN** 重启遗留任务有一个未收敛的 `dispatched` attempt，且执行器无法证明其成功、失败或未动作
- **THEN** worker SHALL 以 `submitted_result_unknown` 诚实终结该 attempt 与任务
- **AND** MUST NOT 自动再派发一次相同动作
