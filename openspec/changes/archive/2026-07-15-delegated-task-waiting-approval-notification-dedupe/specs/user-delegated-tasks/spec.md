## ADDED Requirements

### Requirement: 等待审批的无变化对账必须静默且不使控制卡过期

委托任务处于 `waiting_approval` 时，系统 SHALL 保留有界的审批结果对账，但当审批、真实进度、控制意图和终态结果均未变化时，MUST NOT 发送新的用户通知、写入用户可见状态事件或递增用于卡片控制的 task version。内部 claim/lease MAY 更新，但不得把无变化心跳呈现为新的业务进度。

只有审批通过、驳回、候选版本变化影响任务、真实计数变化、暂停/取消意图变化或终态收敛时，系统 SHALL 发送新的任务反馈。通知去重 MUST 忽略内部 claim、更新时间和下一轮轮询时间，同时 MUST NOT 吞掉真实业务变化。

#### Scenario: 多轮审批等待只发送一次等待卡
- **WHEN** 发布候选已持久化并进入 `waiting_approval`，连续多轮对账都返回仍未审批
- **THEN** 系统只保留首次进入等待审批时的用户通知
- **AND** 后续静默对账不递增 task version、不增加 attempt，也不发送重复飞书卡

#### Scenario: 审批结果变化仍正常通知
- **WHEN** 静默等待中的候选随后被批准、驳回或修改为影响任务收敛的新版本
- **THEN** 下一次对账 SHALL 按真实结果更新任务、attempt 和终态或下一步骤
- **AND** 系统 SHALL 发送一条反映该语义变化的新反馈

#### Scenario: 静默对账不覆盖并发取消
- **WHEN** worker 持有等待审批 claim 时用户取消尚未执行的剩余部分
- **THEN** 静默 release MUST NOT 把已经取消的任务改回 `waiting_approval`
- **AND** 取消后的真实终态与已有计数保持不变
