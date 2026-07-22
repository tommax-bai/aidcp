## ADDED Requirements

### Requirement: Facebook 群组面板 API 暴露账号分组范围读模型

Facebook 群组列表 SHALL 为每个目标返回完整 `accountGroupLabels`，接受可选账号分组过滤；facets 或等价只读端点 SHALL 返回当前 Facebook 账号实际使用的可选分组及无范围目标计数。导入 API SHALL 接受可选请求级 `accountGroupLabels`，未提供与显式空集合的语义必须可区分。所有字段为增量兼容，既有 URL-only 和元数据导入继续有效。

#### Scenario: 未带范围字段的旧导入兼容
- **WHEN** 旧客户端仍只提交 URL 或 metadata items
- **THEN** API 继续处理导入且不清空既有目标范围

#### Scenario: 列表返回完整范围
- **WHEN** 一个目标映射两个账号分组且列表按其中一个过滤
- **THEN** 返回行仍包含两个完整标签，而不是只返回命中过滤的一个

### Requirement: 账号自动化目录聚合 Facebook 加群配置和 scheduled 最近结果

`GET /api/content-schedule` SHALL 在 `platform-aware-account-automation` 的服务端权威投影中，为 Facebook 增加 `join_group` 可用动作并返回每账号自动加群开关、配置日上限、有效日上限、动作时段/来源、是否已分组/映射候选摘要，以及最新 scheduled 审计结果。非 Facebook 行 MUST NOT 获得该动作；无配置或无审计 SHALL 返回 fail-closed 默认和 null 结果，不得伪造。

#### Scenario: Facebook 行显示可配置加群动作
- **WHEN** 内容排期目录包含 Facebook 账号
- **THEN** 其 `availableActions` 含 `join_group`，动作投影携带真实配置、有效额度、范围可用性和最近 scheduled 结果

#### Scenario: 小红书行不出现加群
- **WHEN** 目录包含小红书账号
- **THEN** 其 `availableActions` 不含 `join_group`，也不返回伪造的加群配置

