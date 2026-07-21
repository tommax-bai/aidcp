## ADDED Requirements

### Requirement: Customer publish queue routes SHALL recheck exact environment ownership

客户鉴权服务 SHALL 提供当前客户已授权环境的发布队列读取和单任务取消路由。每个请求 MUST 在客户 JWT、撤销和启用态校验后，从数据库重新解析路径 `envKey` 的当前归属；取消写还 MUST 读取目标任务并验证其账号与该精确环境解析的账号一致、属于发布动作族且处于允许取消的状态。接口 MUST NOT 接受 `accountId` 作为客户选择器。

#### Scenario: 已归属小红书环境读取队列

- **WHEN** 客户持有效令牌请求自己当前归属的小红书 `envKey` 发布队列
- **THEN** 服务端只返回该环境绑定账号的客户队列投影和响应时间

#### Scenario: 同一客户其它环境的任务 id 不能被当前环境取消

- **WHEN** 客户在环境 A 的取消路径提交一个属于其环境 B 的真实任务 id
- **THEN** Cloud 拒绝取消且任务不变，不因两个环境属于同一客户而放宽精确目标校验

#### Scenario: 非小红书或未归属环境被拒绝

- **WHEN** 客户请求非小红书、未归属、已移除或绑定未确认的环境队列
- **THEN** 服务端拒绝请求且不返回队列数量、任务存在性或账号字段

### Requirement: Customer publish queue DTO SHALL be minimum disclosure

客户发布队列响应 SHALL 只包含首页摘要、客户状态、四阶段状态、可证实进度、客户可见标题/来源、任务取消所需 id/version/cancelRequested 与时间字段。响应 MUST NOT 包含 `accountId`、原始 lifecycle snapshot、stage facts、claim token、模型诊断、内部错误或跨账号数据。

#### Scenario: 客户队列不泄漏内部生命周期

- **WHEN** 内部 journey snapshot 或 delegated task 含账号、角色事实、claim 与诊断字段
- **THEN** 客户 DTO 只返回显式白名单字段，序列化响应中不存在这些内部字段

### Requirement: Customer queue cancellation SHALL use CAS and truthful receipts

客户队列取消 SHALL 要求请求体只含有效整数 `version`，并复用领域取消方法完成状态转换。版本不一致 MUST 返回冲突且不重试写；立即终态 SHALL 返回 `cancelled` 或 `partially_completed`，安全收口 SHALL 返回 `cancelRequested=true` 的非终态。服务端 MUST NOT 把取消请求已记录描述为工作已停止。

#### Scenario: 排队任务立即取消

- **WHEN** 当前版本的 queued 或 deferred 任务被取消且尚无已完成部分
- **THEN** Cloud 返回该任务的最小客户终态 `cancelled`，且只改变目标任务

#### Scenario: 规划任务进入安全取消

- **WHEN** 当前版本的 planning 任务接受取消
- **THEN** Cloud 返回同任务的新版本与 `cancelRequested=true`，状态仍非终态并等待工作器收口

#### Scenario: 陈旧版本不执行取消

- **WHEN** 请求 version 与当前任务版本不一致
- **THEN** Cloud 返回 409 且任务保持当前状态，不自动按新版本执行取消
