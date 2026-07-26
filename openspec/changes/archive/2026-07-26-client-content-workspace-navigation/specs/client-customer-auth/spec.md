## ADDED Requirements

### Requirement: Customer curated content routes recheck environment ownership

客户鉴权服务 SHALL 提供当前客户已授权环境的精选内容分页、单条详情和参考创作接口。每个请求 MUST 在客户 JWT、撤销和启用态校验后，从数据库重新读取该客户的环境归属，并只以已归属的 `envKey` 作为账号范围；接口 MUST NOT 接受可绕过归属检查的 `accountId`，MUST NOT 暴露内部面板跨账号能力。

#### Scenario: 已归属环境可读取精选内容

- **WHEN** 客户持有效客户令牌，以当前仍归属自己的 `envKey` 请求精选列表或详情
- **THEN** 服务端只返回该 `envKey` 的客户展示字段和一致分页总数

#### Scenario: 非归属环境被拒绝且不泄漏内容

- **WHEN** 客户以未归属或刚被移除的 `envKey` 请求列表、详情或参考创作
- **THEN** 服务端拒绝请求，不返回该环境是否存在、精选数量或任意内容字段

#### Scenario: 跨账号单条 id 统一未找到

- **WHEN** 客户提交一个真实存在但属于其他账号的精选内容 id
- **THEN** 单条接口返回与不存在 id 相同的 404 形状，不泄漏该行存在性

### Requirement: Customer curated DTO is a minimum disclosure projection

客户精选内容响应 SHALL 只包含列表与详情体验所需的显式白名单字段，并保留计数缺失值为 `null`。响应 MUST NOT 包含行所属 `accountId`、内部纳入原因、跨账号统计、删除能力或仅供运营/模型内部使用的诊断字段。

#### Scenario: 客户列表不含运营字段

- **WHEN** 客户请求精选内容列表
- **THEN** 每一项可包含 id、类型、标题、正文摘要、作者、来源链接、话题、计数、参考图、机器人动作标记与时间，但不包含 `accountId` 或 `admitReason`

#### Scenario: 缺失计数不被编造为零

- **WHEN** 某条精选内容的互动计数未采集
- **THEN** 对应字段返回 `null`，客户端可以呈现“暂无数据”，不得返回 `0`

### Requirement: Customer reference creation uses server-owned source snapshots

客户参考创作接口 SHALL 只接受精选内容 id、已授权 `envKey` 和布尔值 `useReferenceImages`。服务端 MUST 以 `id + envKey` 回读精选行，验证其为正文非空的图文内容，并以服务端快照构建结构化 `publish_post` 委派任务；客户端提交的来源正文、图片 URL、作者、账号或任务状态 MUST 被禁止或忽略。

#### Scenario: 文字参照任务直接排队

- **WHEN** 客户对可创作图文提交 `useReferenceImages=false`
- **THEN** 服务端以来源 `edge` 创建结构化委派任务并返回真实排队任务，来源约束显式记录不使用参考图

#### Scenario: 图文参照只使用已存参考图

- **WHEN** 客户提交 `useReferenceImages=true`
- **THEN** 服务端只复制该精选行已经持久化的参考图与视觉分析到任务快照，不使用客户端提供的任意外部图片

#### Scenario: 不可创作内容被诚实拒绝

- **WHEN** id 对应视频、评论或正文为空的精选行
- **THEN** 服务端不创建任务并返回稳定拒绝原因，不宣称排队成功
