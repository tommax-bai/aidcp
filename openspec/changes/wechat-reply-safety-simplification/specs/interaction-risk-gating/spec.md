## ADDED Requirements

### Requirement: 视频号入站回复的风险状态与数量准入必须解耦

视频号平台已确认的评论/私信回复 SHALL 继续作为真实动作事实记录，最终风险状态仍 SHALL 仅由 Cloud `RiskController` 单写。发送前对 `RiskController` 的读取 SHALL 保留风险状态和未知拒因的 fail-closed 语义，但 MUST NOT 使用通用 `comment`/`dm_reply` 的 `quota:*` 结果重复限制 interaction 域已经独立计数的回复数量。记录动作返回的通用 quota 内/外结果 MUST NOT 被呈现为视频号专用策略结论。

#### Scenario: 平台确认后记账但不恢复重复数量闸
- **WHEN** 视频号回复获得平台确认
- **THEN** Cloud 恰好一次记录该真实动作事实
- **AND** 后续视频号数量准入仍只读取 interaction 专用限速

