## ADDED Requirements

### Requirement: Facebook 候审链路不使用内容质量评分

Facebook 发布 SHALL NOT 调用内容质量评分 LLM，也 SHALL NOT 用固定高分、零分、`NaN` 或小红书评分结果冒充 Facebook 质量结论。系统 MUST 以显式 `not_applicable` 状态表示 Facebook 未评分，并 SHALL NOT 因 `qualityScore` 触发 `retry` 或 `abort`。

满足既有素材、发言语言与确定性处理要求后，Facebook 候选 SHALL 确定性进入 `manual_review`，继续沿用既有草稿落库、审批卡、人工授权和下发确认链。取消内容质量评分 MUST NOT 被解释为自动发布，MUST NOT 绕过人工审批或真实提交确认。

#### Scenario: Facebook 不调用两个质量模型

- **WHEN** 一轮 `platform='facebook'` 发布生成进入后处理和 admission 阶段
- **THEN** `publish:QualityScorer` 与 `publish:ApprovalGatekeeper` 的 LLM 调用次数 SHALL 均为 0
- **AND** 质量状态 SHALL 为 `not_applicable`、质量分 SHALL 为 `null`

#### Scenario: Facebook 不因质量分重试

- **WHEN** Facebook 正文、素材和既有确定性前置条件均有效
- **THEN** 系统 SHALL 产生 `manual_review` admission 并落一条 `pending_approval` 草稿
- **AND** MUST NOT 返回“内容质量不达标”或启动盲目重生成

#### Scenario: 不评分仍必须人工审批

- **WHEN** Facebook 候选已进入 `pending_approval`
- **THEN** 系统 SHALL 等待现有人工授权后才允许进入 edge 下发段
- **AND** 未授权时 MUST NOT 调用 Facebook 提交动作

#### Scenario: 小红书链路不受影响

- **WHEN** 发布平台为 `xiaohongshu`
- **THEN** 系统 SHALL 继续调用既有质量评分与 Gatekeeper，沿用原分数、降级公式、阈值和动作语义

