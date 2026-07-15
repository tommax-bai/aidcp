## ADDED Requirements

### Requirement: 账号人设支持严格校验的结构化强制互动规则

账号 soul MAY 包含可选 `mandatory_interactions` 列表；每条规则 MUST 具有账号内唯一、格式稳定的 `id`，非空语义条件 `when`，只含 `like` / `comment` 的非空动作集合，以及在含 `comment` 时必填的 `comment_guidance` 与显式 `comment_approval`（`review` / `auto_approve`）。为适配既有评论事件链，含 `comment` 的规则 MUST 同时含 `like`。loader MUST 限制规则数量与文本长度，拒绝重复 id、未知动作、未知审批模式和非法字段组合；任一规则非法 MUST 使整份人设以 `persona_invalid` 被拒，库与内存镜像均不变。

该字段 SHALL 与 identity / interests 一样经账号 persona 取值口热加载；保存成功后后续选卡、详情匹配、点赞与评论角色 MUST 使用新规则，无需重启。未配置该字段的账号 MUST 保持既有普通互动行为，MUST NOT 被推导出隐式强制规则。

#### Scenario: 合法强制规则保存并热加载
- **WHEN** 操作员给已绑定账号保存一条唯一 id、`actions=[like,comment]`、评论指引和 `comment_approval=auto_approve` 的合法规则
- **THEN** persona API 返回写后真态，后续浏览角色立即读到该规则，无需重启 cloud

#### Scenario: 非法规则整份拒绝
- **WHEN** 规则 id 重复、动作未知、含 comment 但无 like / 无评论指引、或审批模式非法
- **THEN** persona API 返回 `persona_invalid`，数据库与内存镜像保持保存前真态，MUST NOT 部分接受

#### Scenario: 未配置规则零回归
- **WHEN** 某账号人设不含 `mandatory_interactions`
- **THEN** 其选卡、点赞、评论门槛、冷却与审批行为与变更前逐位一致，系统 MUST NOT 从自由文本猜出强制授权
