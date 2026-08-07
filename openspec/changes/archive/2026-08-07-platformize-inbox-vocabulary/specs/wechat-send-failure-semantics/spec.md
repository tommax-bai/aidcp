## MODIFIED Requirements

### Requirement: 失败语义修正不得扩展协议或写授权

本变更 SHALL 复用现有 `wechat_channels.inbox.reply.result` 的 `confirmed | failed | ambiguous`、durable outbox 与 exact Cloud ack，MUST NOT 新增 message type 或 payload 字段。尚未获得真实捕获证据的写端点与账号写开关 MUST 继续关闭，测试结果 MUST NOT 被表述为真实账号发送成功。

#### Scenario: 新旧 peer 契约保持不变

- **WHEN** 修正后的 Edge 向现有 Cloud 回传确定未派发的 `failed` 或派发后不确定的 `ambiguous`
- **THEN** Cloud 按既有 schema 和 attempt/job 状态机持久化并 exact ack，无需能力协商或数据库迁移

#### Scenario: 本地回归不冒充真实写验收

- **WHEN** 单元、协议、acceptance 或 mock 测试全部通过但没有批准的真实写目标与平台证据
- **THEN** 变更记录 MUST 明确真实评论/私信写入未执行，MUST NOT 启用未捕获写端点或宣称真机发送成功
