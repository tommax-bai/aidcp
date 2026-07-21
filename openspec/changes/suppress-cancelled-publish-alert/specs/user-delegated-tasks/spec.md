## ADDED Requirements

### Requirement: Explicit publish rejection is a non-alerting delegated cancellation

当委托发帖进入 `waiting_approval` 后，用户通过受支持的审批入口明确取消或驳回对应候选稿时，系统 SHALL 持久化该决定，并在异步对账中把委托任务收敛为用户取消语义。系统 MUST 保留真实进度和未下发证据，MUST NOT 将该操作报告为发布失败或发送委托层失败/部分完成报警。仅有 `needs_review` 状态而没有明确用户决定证据时，系统 MUST 继续按真实异常失败闭合，不得猜测为用户取消。

#### Scenario: User rejects the only pending publish candidate

- **WHEN** 零成功的委托发帖正在等待候选稿审批，且用户明确取消或驳回该候选稿
- **THEN** 候选稿不向平台下发，委托任务进入 `cancelled`，终态保留用户取消证据，且委托层不发送“发帖任务未成”报警

#### Scenario: User rejects the remaining candidate after earlier success

- **WHEN** 委托任务已有真实发布成功但尚未达到目标，且用户明确取消或驳回当前待审候选稿
- **THEN** 任务保留真实成功数并按既有诚实终态规则收敛，且委托层不发送失败或部分完成报警

#### Scenario: Needs review without user rejection evidence

- **WHEN** 委托对账读取到候选稿为 `needs_review`，但没有持久化的明确用户取消或驳回证据
- **THEN** 系统继续按非重试失败处理并保留既有失败报警，不得把异常静默为用户取消
