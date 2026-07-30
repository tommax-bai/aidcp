## MODIFIED Requirements

### Requirement: 程序化 Facebook 环境归属与默认慢启动原子完成

customer-auth 的程序化环境归属完成接口 SHALL 接受可选布尔字段 `slowStartEnabled`，并保持省略该字段的旧客户端请求兼容。`slowStartEnabled=true` MUST 仅在同一请求的规范平台为 `facebook` 时接受；小红书、视频号、未知平台或非布尔值 MUST fail-closed，且不得部分注册环境或写入归属。

该接口 SHALL 另外接受两个可选的 Facebook 专属创建意图：环境规则模式开启意图与环境评论审批覆盖模式（`source_rules|auto_approve_all`）。两者 MUST 仅在规范平台为 `facebook` 时接受，非 Facebook 平台、非法枚举或非布尔值 MUST 在注册环境前拒绝整个请求。请求体 MUST 继续走严格白名单：夹带白名单之外的任何键 MUST 整块拒绝且不写入。`slowStartEnabled=true` 与规则模式开启意图 MUST NOT 在同一请求中同时为真，同时提交 MUST fail-closed 拒绝，MUST NOT 静默取其一。

首次成功完成 Facebook 创建 intent 时，Cloud SHALL 在同一数据库事务中插入环境、写入唯一客户归属、完成 intent，并按本次提交的意图写入该环境的慢启动起点、规则模式配置与评论审批策略。慢启动起点为服务端当前时刻所属上海自然日的 00:00，同时显式标记初始化完成；未提交开启意图时慢启动字段保持 NULL。慢启动起点 MUST NOT 取 Edge 时钟、账号入库时间、Cookie 时间或 `accounts.slow_start_since`。

已完成 intent 的幂等重试 MUST 只返回既成归属，不得再次写入或重置慢启动起点、规则模式配置或审批策略；若运营在首次完成后手动更改过其中任何一项，陈旧重试 MUST NOT 复原。接口不得修改风控档位、风险状态、账号旧慢启动列或其它环境配置。

#### Scenario: Facebook 创建原子写入 D1 起点

- **WHEN** 有效客户使用待完成 intent 注册一个全新 Facebook 环境并提交 `slowStartEnabled=true`
- **THEN** 环境、归属、intent 完成态与上海当日 00:00 慢启动起点在同一事务中提交

#### Scenario: Facebook 创建原子写入规则模式与免审

- **WHEN** 有效客户在完成请求中提交规则模式开启意图与 `auto_approve_all`
- **THEN** 环境、归属、intent 完成态、该环境规则模式配置与评论审批策略在同一事务中提交
- **AND** 未提交慢启动开启意图时该环境慢启动字段保持 NULL

#### Scenario: 旧客户端省略字段保持兼容

- **WHEN** 有效旧客户端完成环境归属但未提交 `slowStartEnabled`
- **THEN** 请求继续按既有规则成功，环境慢启动字段保持 NULL

#### Scenario: 非 Facebook 开启意图原子拒绝

- **WHEN** 请求以小红书、视频号或未知平台提交 `slowStartEnabled=true`、规则模式开启意图或审批模式字段
- **THEN** Cloud 在注册环境前拒绝整个请求，环境、归属和 intent 均不发生部分写入

#### Scenario: 慢启动与规则模式互斥意图被拒绝

- **WHEN** 同一 Facebook 完成请求同时提交 `slowStartEnabled=true` 与规则模式开启意图
- **THEN** Cloud 在注册环境前拒绝整个请求，MUST NOT 只取其中一项写入

#### Scenario: 完成重试不重置或复活慢启动

- **WHEN** Facebook intent 已成功完成，随后同一 intent/环境被再次提交
- **THEN** Cloud 返回幂等成功但不更新 `slow_start_since`、规则模式配置或审批策略
- **AND** 即使该环境已被运营手动更改，也不得复原为创建时的值

## ADDED Requirements

### Requirement: 客户只能为自己的环境设置评论审批覆盖，且不依赖账号绑定或边缘在线

customer-auth SHALL 提供 env-scoped 的评论审批覆盖读写路由。写请求体 MUST 只接受模式枚举 `source_rules|auto_approve_all`，夹带 `accountId`、`updatedBy` 或任何其它键 MUST 整块拒绝且不写入。

策略 SHALL 直接持久化在 `envKey` 对应的环境记录；`accountId` MUST NOT 由客户端提交，也 MUST NOT 作为写入目标选择器。该路由 MUST NOT 依赖环境↔账号绑定、账号是否存在、边缘活会话、浏览器是否运行或环境是否已启动。

授权 SHALL 在同一 enabled-user 与 env ownership 权威范围内进行：客户 MUST 拥有该 `envKey`，否则 fail-closed 且不泄露该环境的账号身份或现有策略。写入 SHALL 只修改该环境的审批策略字段，MUST NOT 修改当前或历史账号的审批策略、风控档位、风控终态、账号写总闸或任何其它账号配置。客户来源的审计署名 MUST 与后台管理员可区分。

成功回包 SHALL 返回写后环境策略真态。没有唯一有效当前账号绑定时，回包 SHALL 明确标注当前没有执行对象，MUST NOT 编造绑定或生效评论行为。云端环境写入成功即为配置已保存，回包 MUST NOT 引入「已保存 / 待下发边缘」二态。

#### Scenario: 边缘离线且未绑定账号时仍能设置免审

- **WHEN** 某 `envKey` 的所有者在该环境边缘未连接且没有账号绑定时提交 `auto_approve_all`
- **THEN** 云端写入该环境策略并返回已保存的环境配置态
- **AND** 回包标注当前没有执行对象，MUST NOT 返回伪造的绑定或生效评论态

#### Scenario: 请求体夹带账号选择器被拒绝

- **WHEN** 请求体额外携带 `accountId`、`updatedBy` 或任何其它键
- **THEN** customer-auth 返回校验失败且不写入任何环境或账号字段

#### Scenario: 非所有者请求 fail-closed

- **WHEN** 某已登录客户对不属于自己的 `envKey` 提交请求
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 写入，MUST NOT 泄露该环境的账号身份或现有策略

#### Scenario: 环境注册表查询失败 MUST NOT 伪装成未配置

- **WHEN** ownership 或环境策略写入因数据库不可达或表缺失而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回「按来源规则」，MUST NOT 把「没写成」表述为配置已保存

#### Scenario: 关闭免审只改该环境策略

- **WHEN** 环境所有者提交 `source_rules`
- **THEN** 云端只更新该环境的审批策略
- **AND** 当前及历史账号的策略旧列、风控档位、风控终态与其它账号配置逐位保持原值
