## ADDED Requirements

### Requirement: 客户待审稿读取按授权环境绑定账号隔离

客户鉴权域 SHALL 提供当前授权环境绑定账号的待审稿列表与单条详情只读接口。请求 MUST 逐次从 `envKey` 解析持久账号绑定，并在 SQL 中同时约束 `account_id` 与 `status='pending_approval'`；列表 MUST 使用同一筛选条件返回一致 total、limit、offset。响应 SHALL 只披露审核所需稿件字段，不得返回来源原稿快照、内部 provider/model 诊断、审批凭据、其它账号信息或 panel 专用字段。绑定未知/冲突与跨账号 id MUST fail-closed，不得伪装成空列表或泄漏存在性。

#### Scenario: 当前账号多稿分页

- **WHEN** 已授权环境绑定账号 A 且 A 有 15 条待审稿，客户请求 limit=12 offset=0
- **THEN** 返回 A 的 12 条稿件与 total=15，不出现其它账号或非待审状态记录

#### Scenario: 单条详情按账号与状态过滤

- **WHEN** 客户请求属于其它账号、已发布或不存在的稿件 id
- **THEN** 接口返回同形 404，不泄漏该 id 是否在其它账号或其它状态存在

#### Scenario: 最小披露 DTO

- **WHEN** 列表或详情读取成功
- **THEN** 响应只包含稿件 id、类型、标题、正文/摘要、话题、配图、内容版本、更新时间、平台与发布计划，不包含 sourceReference、视觉模型诊断、审批签名或账号选择字段

#### Scenario: 环境绑定未知不伪装为空

- **WHEN** envKey 属于客户但尚未解析唯一账号或存在跨客户冲突
- **THEN** 接口返回既有稳定绑定拒因，不返回 `items=[]/total=0`
