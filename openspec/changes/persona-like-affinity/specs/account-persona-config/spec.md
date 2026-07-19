## ADDED Requirements

### Requirement: 人设行为模板支持结构化三档点赞倾向

账号 soul 的 `behavior_guidelines` MAY 包含可选 `like_affinity`，且存在时 MUST 严格为 `normal`、`like_more`、`like_most` 之一。loader MUST 拒绝未知档位，serializer MUST 保留该字段往返；字段缺省 SHALL 等价 `normal`，历史人设无需迁移。`like_affinity` 与 `like_principle` SHALL 同时进入账号级热加载人设，但 MUST NOT 自动生成、修改或暗示 `mandatory_interactions`。

#### Scenario: 合法档位往返不丢失

- **WHEN** 一份合法 soul 含 `behavior_guidelines.like_affinity=like_more` 并经 loader → serializer → loader 往返
- **THEN** 最终人设仍为 `like_more`，其他 identity、interests 与行为原则保持不变

#### Scenario: 历史人设缺字段按正常档

- **WHEN** 一份历史 soul 有 `behavior_guidelines` 但没有 `like_affinity`
- **THEN** loader 继续接受，运行时按 `normal` 解释，MUST NOT 要求数据库迁移

#### Scenario: 未知档位整份拒绝

- **WHEN** 保存的人设含未知 `like_affinity`
- **THEN** soul 校验以 `persona_invalid` 拒绝，数据库与内存镜像不变

#### Scenario: 倾向不产生强制互动规则

- **WHEN** 任一档位经 onboarding 生成并持久化
- **THEN** 产物不因档位出现 `mandatory_interactions`，普通倾向 MUST NOT 被解释为确定性点赞授权
