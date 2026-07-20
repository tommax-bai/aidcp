## ADDED Requirements

### Requirement: 人工回复必须以一次审核发送动作表达

视频号客户工作区对 `approval_required` job SHALL 提供一次“审核并发送”主动作。存在未保存文字时，该动作 SHALL 先保存，再批准，再使用批准返回的最新 version 请求发送；任一步失败 MUST 停止后续步骤并呈现真实状态。Cloud 内部 `approved`、`queued`、`sending` 与 `sent` 状态 MUST 保持分离，客户端 MUST NOT 因批准成功就显示已发送。

#### Scenario: 审核发送完整成功
- **WHEN** 客户确认一条合法草稿且保存、批准、发送入队依次成功
- **THEN** 客户只执行一次主动作
- **AND** 客户端显示已进入发送流程而非提前显示平台成功

#### Scenario: 批准成功但发送失败
- **WHEN** 批准 API 成功而发送 API 被动态门禁拒绝
- **THEN** job 保持“已批准，尚未发送”
- **AND** 客户端显示发送拒因并允许从 approved 状态重试

