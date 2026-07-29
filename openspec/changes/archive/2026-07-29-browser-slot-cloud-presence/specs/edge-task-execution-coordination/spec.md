## ADDED Requirements

### Requirement: Browser-absent edge 的任务 SHALL 触发唤醒并得到终局回执

Cloud 在 Edge 控制面在线但浏览器缺席时 SHALL 允许需要浏览器的任务进入 acquire/wake 流程。Edge MUST 在唤醒完成且身份复核成功后才授予浏览器执行租约；唤醒失败或死线到达 SHALL 返回明确终局并保持后续可重试。

#### Scenario: 控制面在线任务唤醒浏览器
- **WHEN** Cloud 向 browser-absent edge 派发一个需要浏览器的任务且其在死线内取得槽位
- **THEN** Edge 完成浏览器启动、身份复核与租约 acquired 后才接收首条业务命令

#### Scenario: 排队超出唤醒死线
- **WHEN** 任务等待浏览器槽位超过调用方死线
- **THEN** Cloud 收到 `browser_wake_failed` 类可恢复终局并可按策略重试
- **AND** MUST NOT 把它记录为 edge offline、成功或无回执

#### Scenario: 浏览器缺席时业务命令不得静默丢弃
- **WHEN** 浏览器缺席期间仍收到一条需要页面的业务命令
- **THEN** Edge 返回明确的 browser-unavailable/wake-required 失败
- **AND** MUST NOT 只写本地日志而让 Cloud 看门狗超时
