## ADDED Requirements

### Requirement: 账号全局评论免审覆盖人设规则局部审批模式

结构化 `mandatory_interactions[].comment_approval` SHALL 继续表达 `source_rules` 账号的局部站立授权；当账号显式配置全局评论 `auto_approve_all` 时，Cloud MUST 将该账号所有 mandatory 评论的有效模式解析为 `auto_approve`，即使命中规则写为 `review`。该覆盖 MUST NOT 改写 persona 原文或放宽 mandatory 匹配、详情确认、动作集合与通知先行要求。

#### Scenario: 全局免审覆盖 mandatory review
- **WHEN** `auto_approve_all` 账号命中一条详情确认且 `comment_approval=review` 的 mandatory 评论规则
- **THEN** 该评论发送免审通知成功后获得授权，MUST NOT 等待按钮审批

#### Scenario: 来源规则账号保持 persona 局部模式
- **WHEN** 账号为 `source_rules`
- **THEN** mandatory 规则的 `review|auto_approve` 继续逐条决定该来源审批方式，MUST NOT 被改写

#### Scenario: 覆盖不改变规则匹配
- **WHEN** `auto_approve_all` 账号的帖子未命中任何 mandatory 规则
- **THEN** 免审只作用于实际由普通评论链产生的候选，MUST NOT 伪造 mandatory 命中或强制生成评论
