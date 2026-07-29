## Why

Facebook 发布目前复用了小红书质量评分与 LLM Gatekeeper：真实 DEV 中两轮内容生成和模型调用均成功，却连续在下发前被 `retry` 拒绝，而且评分提示仍把对象称为“小红书笔记”。Facebook 草稿本来就必须经过人工审批，这层平台错配的主观评分没有增加安全性，反而阻断候审稿并消耗媒体预约。

## What Changes

- Facebook 发布不再请求 `QualityScorer` LLM，也不产生伪造的替代分数；质量状态明确记录为“不适用”。
- Facebook 发布不再请求基于质量分的 LLM Gatekeeper；满足确定性前置条件后直接进入既有人工审批，MUST NOT 自动提交。
- 保留 Facebook 发言语言校验、素材必需、确定性合规/安全检查、审批授权和真实下发确认。
- 小红书质量评分、Gatekeeper 阈值、重试与审批行为逐字保持不变。
- 补充运行日志与回归测试，证明 Facebook 一轮中 `QualityScorer` / `ApprovalGatekeeper` 模型调用数均为零，且候审记录不携带虚构质量分。

## Capabilities

### New Capabilities

### Modified Capabilities

- `facebook-post-publish`: Facebook 候审稿不再受内容质量评分阻断，但仍必须经过确定性前置检查和人工审批。
- `publish-pipeline`: 质量评分与质量 Gatekeeper 改为平台适用策略；小红书沿用现状，Facebook 明确为不评分且不调用对应模型。

## Impact

- `aidcp-cloud`: 发布管线类型、`QualityScorer`、`ContentAssembler`、`ApprovalGatekeeper`、`PublishExecutor` 及其单元/验收测试。
- 不改协议、不改 edge、不改数据库 schema、不改小红书运行路径。
- 本 change 不清理历史 `reserved` 素材行；历史数据修复需另行审计后执行。
