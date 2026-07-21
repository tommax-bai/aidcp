## ADDED Requirements

### Requirement: 客户灵感库在账号筛选后按固定热度规则分页排序

客户鉴权精选列表 SHALL 接受 `weighted`、`collects`、`likes` 和 `recent` 四种固定排序，并 SHALL 在有效客户令牌、环境归属解析、账号约束与创作状态筛选之后、`LIMIT/OFFSET` 之前由 Cloud 完成排序。省略排序参数 SHALL 使用 `weighted`；其它值 MUST 以具名无效排序错误拒绝并且不得触达精选查询。请求 MUST NOT 接受任意 SQL 字段、方向或可绕过账号隔离的参数。

`weighted` SHALL 使用 `点赞 × 1 + 收藏 × 1.43`，实现等价值 SHALL 为 `点赞 × 100 + 收藏 × 143`。点赞或收藏任一缺失的内容 MUST 排在两者均有证据的内容之后，缺失 MUST NOT 当作零。`collects` 和 `likes` SHALL 分别按对应计数降序并将该计数缺失的内容置后；`recent` SHALL 保持精选记录最近更新时间降序。所有模式 MUST 使用确定性的次级字段，使相同主排序值的分页顺序稳定。

#### Scenario: 综合热度在分页前计算

- **WHEN** 当前账号筛选后有超过一页的灵感且客户请求 `sort=weighted&limit=12&offset=0`
- **THEN** Cloud 在完整筛选结果上按 `点赞 × 100 + 收藏 × 143` 降序选择前 12 条，并返回同一筛选范围的真实 total，而不是只对任意 12 条做客户端排序

#### Scenario: 收藏与点赞排序保持账号隔离

- **WHEN** 客户分别请求 `sort=collects` 或 `sort=likes`，且其它账号存在计数更高的内容
- **THEN** 返回顺序只由当前 `envKey` 绑定账号和当前创作状态筛选中的内容决定，其它账号行不参与排序或总数

#### Scenario: 缺失热度不伪装成零

- **WHEN** 当前筛选同时包含完整赞藏计数、真实零值和缺少任一计数的内容
- **THEN** 综合排序先排列有完整计数证据的内容，真实零参与公式比较，缺失计数内容置后且响应仍保留 null

#### Scenario: 相同热度分页顺序稳定

- **WHEN** 多条灵感具有相同主排序值并跨越分页边界
- **THEN** Cloud 使用确定性的次级时间和 id 顺序，使相同数据库快照下重复请求得到相同页序

#### Scenario: 未知排序在查询前被拒绝

- **WHEN** 客户提交未定义排序、任意字段名或排序方向
- **THEN** 客户鉴权接口返回 `invalid_sort`，不静默回落且不触达精选列表查询

