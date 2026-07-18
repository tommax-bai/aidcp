## MODIFIED Requirements

### Requirement: Customer curated content routes recheck environment ownership

客户鉴权服务 SHALL 提供当前客户已授权环境的精选内容分页、单条详情和参考创作接口。每个请求 MUST 在客户 JWT、撤销和启用态校验后，从数据库重新读取该客户的环境归属，并只以已归属的 `envKey` 作为账号范围；接口 MUST NOT 接受可绕过归属检查的 `accountId`，MUST NOT 暴露内部面板跨账号能力。精选列表新筛选 MUST 接受 `uncreated`、`created` 或 `all`，并 MUST 在账号约束内通过既有 `delegated_tasks.source_constraints` 真态判断是否曾持久化洗稿触发任务，任务当前或终态不得改变该归类。滚动发布期 SHALL 继续接受旧 `creatable`，且 MUST 精确返回 `uncreated ∪ created` 的原可创作集合；新客户端 MUST NOT 再产生该值。其它未知值 SHALL 以具名无效筛选错误拒绝，不得静默回落。

#### Scenario: 已归属环境可读取三种精选筛选

- **WHEN** 客户持有有效客户令牌，以当前仍归属于自己的 `envKey` 请求 `uncreated`、`created` 或 `all` 列表
- **THEN** 服务端只返回该 `envKey` 绑定账号的客户展示字段和与该筛选一致的分页总数

#### Scenario: 触发记录关联保持账号隔离

- **WHEN** 另一账号存在相同来源 id 或精选 id 的洗稿触发任务
- **THEN** 该记录不得改变当前账号灵感在“未创作”或“已创作”中的归类

#### Scenario: 旧客户端筛选保持原语义

- **WHEN** 尚未更新的客户端请求 `mode=creatable`
- **THEN** 服务端返回正文非空的全部图文灵感，不按是否触发洗稿拆分，也不包含视频、评论或空正文

#### Scenario: 未知筛选被明确拒绝

- **WHEN** 客户请求其它未定义筛选值
- **THEN** 服务端返回无效筛选错误，且不触达精选列表查询

#### Scenario: 非归属环境被拒绝且不泄漏内容

- **WHEN** 客户以未归属或刚被移除的 `envKey` 请求列表、详情或参考创作
- **THEN** 服务端拒绝请求，不返回该环境是否存在、精选数量或任意内容字段

#### Scenario: 跨账号单条 id 统一未找到

- **WHEN** 客户提交一个真实存在但属于其它账号的精选内容 id
- **THEN** 单条接口返回与不存在 id 相同的 404 形状，不泄漏该行存在性
