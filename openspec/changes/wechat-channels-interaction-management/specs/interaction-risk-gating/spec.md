## ADDED Requirements

### Requirement: 视频号回复发送必须经 Cloud RiskController 与回复硬门禁

Cloud SHALL 在创建 send attempt 前再次校验 runtime/global/account/channel write switch、published policy、auth/identity/capability、job CAS、单飞、限速、ambiguous blocker 与 `RiskController.canDo`。评论回复 SHALL 使用既有 `comment` risk action；私信文本回复 SHALL 新增 `dm_reply` risk action。`dm_reply` 的 minute/hour/day 写死 fallback quota MUST 为 0，只有显式配置后才可发送。

#### Scenario: 默认私信 quota 阻止发送
- **WHEN** `dm_reply` 没有显式安全限额配置
- **THEN** 有效 quota 回落 0，send 被具名背压，MUST NOT 调 Edge 或伪造失败/成功

#### Scenario: 评论回复与其它评论共享风险预算
- **WHEN** 视频号评论回复准备发送
- **THEN** Cloud 用同一账号的 `comment` RiskController 窗口判定，MUST NOT 建立绕开现有评论预算的私有计数器

### Requirement: 只有平台确认的回复才记录成功风险事件

Cloud MUST 仅在 `interaction.reply.result.status='confirmed'` 且 scope/idempotency/attempt 匹配时调用 `RiskController.record('comment'|'dm_reply')`。failed、ambiguous、duplicate command、approval、queued、sending、shadow 或 gated 结果 MUST NOT 记录成功。最终风险 status/quotaLevel 仍只由 Cloud RiskController 单写；runtime controls/reply limiter/Edge MUST NOT 改写。

#### Scenario: Ambiguous 不计成功
- **WHEN** Edge 回报 reply result ambiguous
- **THEN** Cloud 保存 attempt/job ambiguous 但不 record 风控成功，后续回查 confirmed 后才记录一次

#### Scenario: 重复 confirmed 只记一次
- **WHEN** 同一 attempt confirmed result 因重连重复到达
- **THEN** 幂等消费只记录一个 risk event，job 仍为单一 sent

### Requirement: 配额饱和只做背压且不能自动清除 ambiguous

`dm_reply` 或 `comment` 配额饱和 SHALL 沿用既有“节奏背压，不升级风险态”不变量。配额恢复 MAY 重新评估 queued/failed 可重试 job，但 MUST NOT 自动重投 ambiguous attempt。

#### Scenario: DM 配额撞顶不自升 warned
- **WHEN** normal 账号的 dm_reply 配额耗尽
- **THEN** send 被拒/延迟，账号风险终态和 signal_count 不变

#### Scenario: 配额恢复不重发待核验消息
- **WHEN** ambiguous attempt 存在且配额窗口随后恢复
- **THEN** job 继续等待平台回查，MUST NOT 因 canDo 重新允许而创建第二 attempt
