## ADDED Requirements

### Requirement: 发布队列快照按阶段摘要呈现并保留原始明细

管理后台内容页 SHALL 将 `GET /api/content/queue` 返回的 in-flight publish snapshot 优先呈现为运营可扫读的阶段摘要，而不是默认暴露完整原始键值表。阶段摘要 SHALL 至少覆盖来源/触发、洗稿/正文、质检/清洗、配图/元数据、人审/下发五类进度，并基于 snapshot 中已存在的字段如实标记已完成、当前进行中、未开始状态。

该呈现 MUST 保持诚实：字段未出现时不得声称阶段完成；状态为 idle 或 snapshot 为空时不得渲染虚假的进行中阶段。原始 snapshot 字段 MUST 继续通过二级展开入口可见，供排障和未知未来字段检查；本要求 MUST NOT 改变 `/api/content/queue` 的响应结构或发布编排行为。

#### Scenario: 运行中洗稿快照显示阶段摘要

- **WHEN** 管理后台内容页拉到 `status = running` 且 snapshot 中含 `trigger.generateInput.referenceNote`、`referenceAnalysis`、`faithfulDraft` 等洗稿字段
- **THEN** 页面优先显示洗稿来源、稿件标题或来源标题、账号、已完成/进行中的阶段摘要，而不是只显示原始 JSON 字段表

#### Scenario: 原始字段仍可展开排障

- **WHEN** snapshot 中存在未被阶段摘要识别的顶层字段
- **THEN** 页面仍提供原始字段展开入口并显示该字段的序列化值，运营排障不需要翻服务器日志确认字段是否存在

#### Scenario: 空闲状态不伪造进度

- **WHEN** `/api/content/queue` 返回 `status = idle` 且 `snapshot = null`
- **THEN** 页面只显示空闲状态和无进行中生成任务提示，MUST NOT 渲染任何已完成或进行中的阶段
