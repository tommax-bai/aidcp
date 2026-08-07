## MODIFIED Requirements

### Requirement: 只有平台确认的回复才记录成功风险事件

Cloud MUST 仅在 `wechat_channels.inbox.reply.result.status='confirmed'` 且 scope/idempotency/attempt 匹配时调用 `RiskController.record('comment'|'dm_reply')`。failed、ambiguous、duplicate command、approval、queued、sending、shadow 或 gated 结果 MUST NOT 记录成功。最终风险 status/quotaLevel 仍只由 Cloud RiskController 单写；runtime controls/reply limiter/Edge MUST NOT 改写。

#### Scenario: Ambiguous 不计成功
- **WHEN** Edge 回报 reply result ambiguous
- **THEN** Cloud 保存 attempt/job ambiguous 但不 record 风控成功，后续回查 confirmed 后才记录一次

#### Scenario: 重复 confirmed 只记一次
- **WHEN** 同一 attempt confirmed result 因重连重复到达
- **THEN** 幂等消费只记录一个 risk event，job 仍为单一 sent
