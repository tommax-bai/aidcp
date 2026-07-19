## ADDED Requirements

### Requirement: 浏览器槽位等待 SHALL 保留发布授权并自动重试

当发布租约在任何发布业务命令下发前收到 `browser_wake_failed` 时，Cloud SHALL 将其视为可恢复的浏览器槽位/唤醒等待：草稿 MUST 保持 `pending_approval`，有效授权信号 MUST 保留，MUST NOT 计入发布序列失败或熔断，并 SHALL 由既有已批准草稿补偿扫描再次尝试。该行为 MUST NOT 绕过 `approved === true` 与内容版本一致闸。

#### Scenario: 槽位已满时保留授权等待
- **WHEN** 目标客户端在线、目标浏览器缺席且本机槽位暂时已满，发布 lease 在零发布命令阶段收到 `browser_wake_failed`
- **THEN** 草稿保持待审、授权保留、没有发布命令下发，操作员看到“已批准，等待浏览器槽位，稍后自动重试”

#### Scenario: 浏览器稍后启动后自动发布
- **WHEN** 上述环境仍在本地 FIFO 队列中并在其他浏览器让出槽位后启动
- **THEN** 既有补偿扫描重新取得 lease，并在再次校验授权和内容版本后只执行一次发布序列，无需重新批准

#### Scenario: Cloud 重启后恢复等待发布
- **WHEN** Cloud 在 `browser_wake_failed` 后、成功取得 lease 前重启
- **THEN** 持久待审草稿与授权信号仍能被补偿扫描发现，发布等待继续，MUST NOT 因进程内队列丢失而静默遗失

### Requirement: 槽位等待重试 MUST 保持失败分类与副作用边界

只有明确的 `browser_wake_failed` 可以保留授权自动重试。真实无在线 Edge、`cdp_unhealthy`、正常 `acquire_timeout`、控制面故障及任何发布序列已经开始后的失败 SHALL 保持既有作废授权、人工处理或未知结果语义，MUST NOT 被重新标记为槽位等待。

#### Scenario: acquire 无响应不伪装成槽位等待
- **WHEN** Cloud 已发送 acquire 但直到 Cloud 超时仍未收到 acquired 或 `browser_wake_failed`
- **THEN** dispatcher 保持既有 `acquire_timeout_requeued` 语义，作废授权并要求重批，MUST NOT 自动延后发布

#### Scenario: 发布序列开始后绝不因槽位机制重跑
- **WHEN** lease 已取得且发布序列已经开始，随后页面写入失败或提交结果未知
- **THEN** dispatcher 按既有失败/未知结果契约收敛，MUST NOT 保留授权后自动重跑整个序列

### Requirement: 浏览器槽位等待通知 SHALL 有界去重

同一发布记录在同一 Cloud 进程内连续因 `browser_wake_failed` 被补偿扫描重试时，dispatcher SHALL 只在首次进入该等待状态时通知操作员；成功取得 lease 或记录不再可下发后 SHALL 清除该去重状态。进程重启后 MAY 再通知一次恢复上下文，但 MUST NOT 在每个扫描周期重复刷屏。

#### Scenario: 周期扫描不重复通知
- **WHEN** 同一已批草稿连续三轮扫描都收到 `browser_wake_failed`
- **THEN** 操作员只收到一条等待槽位通知，三次都不作废授权且不计熔断

#### Scenario: 取得 lease 后重新武装
- **WHEN** 草稿等待后成功取得 lease，之后因新的独立发布生命周期再次进入槽位等待
- **THEN** 旧去重标记已清除，新等待可以产生一条新的诚实通知
