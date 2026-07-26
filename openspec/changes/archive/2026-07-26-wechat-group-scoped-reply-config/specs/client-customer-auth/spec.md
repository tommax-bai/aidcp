## MODIFIED Requirements

### Requirement: 客户互动投影必须包含回复配置就绪状态
interaction list/detail 与 read-controls 成功回包 SHALL 为当前 account/env 返回只读 `replyConfig` 有效配置投影，至少区分 `missing`、`draft_only`、`published`、`unknown`，给出 current/draft/published version，并加性给出非敏感 `source`：`group` 或 `default` 及可展示的 group label。该投影 MUST 通过与回复工作流相同的 scoped resolver 得到，MUST NOT 读取账号旧策略，MUST NOT 包含 scope opaque ID、模板正文、规则条件、完整私信或 internal permission；查询失败 MUST 显示 unknown/fail-closed，不能伪造默认 published 配置。

#### Scenario: 无发布配置时客户端得到明确阻断
- **WHEN** 当前账号目标 group/default scope 不存在、没有 config head 或只有未发布 draft
- **THEN** 客户回包分别返回 missing 或 draft_only及其目标 source，客户端可保持收件箱可读并禁用依赖 published 配置的生成/发送流程

#### Scenario: 已发布配置只暴露版本和来源状态
- **WHEN** 当前账号解析到 immutable published group/default 配置
- **THEN** 客户回包返回 published、版本号与非敏感 source，不返回 scope ID、模板、规则、profile 或审计正文

#### Scenario: 有组缺配置不伪装成默认已发布
- **WHEN** 当前账号具有非空 group label 但该组没有 published 配置，同时 default 已发布
- **THEN** replyConfig 投影仍返回该 group source 的 missing/draft_only 状态，MUST NOT 返回 default published
