## ADDED Requirements

### Requirement: 内部 Panel 提供环境资产投影与账号环境摘要

内部 Panel API SHALL 提供受内部 JWT 保护的环境资产列表，聚合环境生命周期、环境名来源、挂载账号统一显示名、账号风控/档位、分组、端用户归属、installation 观测与删除请求；客户令牌 MUST NOT 访问该跨客户投影。账号列表 SHALL additive 返回有效/删除中/在线环境计数，且所有账号环境摘要与环境列表使用同一生命周期过滤规则。

#### Scenario: 内部管理员读取环境资产
- **WHEN** 持内部 Panel JWT 请求环境列表
- **THEN** 返回环境与账号/风险/分组/归属/生命周期投影，并不暴露密钥、凭据、代理密码或客户 key/hash

#### Scenario: 客户令牌无法读取跨客户环境资产
- **WHEN** 持客户令牌请求内部环境资产端点
- **THEN** 请求被拒且不返回任何跨客户挂载或归属信息

#### Scenario: 账号摘要与环境生命周期一致
- **WHEN** 某账号有一个 active、一个 deleting 和一个 deleted 环境
- **THEN** 账号摘要返回 activeCount=1、deletingCount=1，deleted 环境不计入当前数量

### Requirement: 内部删除 API 只创建异步期望状态

内部 Panel SHALL 提供逐环境删除申请 API，要求完整 envKey 确认并支持幂等请求。成功响应 MUST 返回写后生命周期与 requestId，状态为请求已创建/已存在；该 API MUST NOT 直接声称 AdsPower 已删除。重复未终态请求 MUST 返回同一 active request，已删除环境 MUST 返回同一终态而非重建任务。

#### Scenario: 创建删除申请返回 202 真态
- **WHEN** 管理员对 active 环境提交匹配 envKey 的确认和新的幂等键
- **THEN** Cloud 原子创建删除申请、冻结调度并以 202 返回 `waiting_edge` 及 requestId，不返回“已删除”

#### Scenario: 重复提交不产生多条删除责任
- **WHEN** 同一环境已有未终态删除申请且管理员重试请求
- **THEN** API 返回现有 requestId/状态，不产生第二个 active 删除申请或第二次 AdsPower 执行责任
