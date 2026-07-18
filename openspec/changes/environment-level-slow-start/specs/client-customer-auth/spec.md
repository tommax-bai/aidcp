## MODIFIED Requirements

### Requirement: 客户只能为自己的环境开关慢启动，且不依赖账号绑定或边缘在线

customer-auth SHALL 提供 env-scoped `PUT /environments/:envKey/slow-start`。请求体 MUST 只接受 `enabled`，夹带任何其它键 MUST 整块拒绝且不写入。

慢启动配置 SHALL 直接持久化在 `envKey` 对应的环境记录；`accountId` MUST NOT 由客户端提交，也 MUST NOT 作为写入目标选择器。该路由 MUST NOT 依赖环境↔账号绑定、账号是否存在、边缘活会话、浏览器是否运行或环境是否已启动。

授权 SHALL 在同一 enabled-user 与 env ownership 权威范围内进行：客户 MUST 拥有该 `envKey`，否则 fail-closed。写入 SHALL 只修改该环境的 `slow_start_since`；开启时写入对齐运营自然日起点的值，关闭时清空。该路由 MUST NOT 修改当前或历史账号的慢启动字段、风控档位、风控终态、账号写总闸或任何其它账号配置。

成功回包 SHALL 返回写后环境配置真态。有唯一有效当前账号绑定时，回包还 SHALL 返回该账号 controller 依据该环境起点算出的生效状态与当日上限；没有有效绑定时，回包 SHALL 明确标注 `binding_unknown` 且不编造 `binding` 或当日上限。云端环境写入成功即为配置已生效，回包 MUST NOT 引入「已保存 / 待下发边缘」二态；没有账号时 SHALL 表述为当前没有执行对象，而非写入尚未完成。

#### Scenario: 边缘离线且未绑定账号时仍能开启环境慢启动

- **WHEN** 某 `envKey` 的所有者在该环境边缘未连接且没有账号绑定时提交 `{ enabled: true }`
- **THEN** 云端把该环境的 `slow_start_since` 写为对齐运营自然日的起点，并返回已开启的环境配置态
- **AND** 回包标注 `eligible=false` 与 `ineligibleReason=binding_unknown`，MUST NOT 返回伪造的 `binding` 或 `dayQuotas`

#### Scenario: 环境换绑后设置不随旧账号离开

- **WHEN** 已开启慢启动的环境从账号 A 换绑为账号 B
- **THEN** 环境的 `slow_start_since` 逐位保持不变
- **AND** 下一次配额计算中账号 B 使用该环境起点，账号 A 不再因该环境被 clamp，MUST NOT 要求重启

#### Scenario: 请求体夹带账号选择器被拒绝

- **WHEN** 请求体额外携带 `accountId`、`since`、`quotaLevel` 或任何其它键
- **THEN** customer-auth 返回校验失败且不写入任何环境或账号字段

#### Scenario: 非所有者请求 fail-closed

- **WHEN** 某已登录客户对不属于自己的 `envKey` 提交请求
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 写入，MUST NOT 泄露该环境的账号身份或配置

#### Scenario: 环境注册表查询失败 MUST NOT 伪装成未绑定

- **WHEN** ownership 或环境配置写入因数据库不可达或表缺失而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 把「没写成」表述为配置已保存

#### Scenario: 关闭慢启动只清环境起点

- **WHEN** 环境所有者提交 `{ enabled: false }`
- **THEN** 云端只清空该环境的 `slow_start_since`
- **AND** 当前及历史账号的慢启动旧列、风控档位、风控终态与其它账号配置逐位保持原值

### Requirement: 慢启动状态 SHALL 提供不依赖边缘或账号绑定的 env-scoped 读

customer-auth SHALL 提供 env-scoped `GET /environments/:envKey/slow-start`，在该环境边缘不在线（含从未启动）或尚未绑定账号时也返回该环境的慢启动配置真态。

该读 SHALL 先按 ownership 读取环境自己的 `slow_start_since`。有唯一有效当前账号绑定时，SHALL 复用与 `ui.snapshot` 慢启动投影同一个 controller 产出（同一环境 anchor 解析、同一次 clock），MUST NOT 另行推算绑定性或上限。回包 MUST NOT 包含 accountId 或任何其它账号身份标识。

环境未绑定账号或绑定账号不存在时，该读 SHALL 保留环境配置态：关闭返回 `state=off`；开启返回 `state=active`、`since`、`day` 与 `totalDays`，同时返回 `eligible=false`、`ineligibleReason=binding_unknown`。此时 MUST NOT 编造 `binding`、`dayQuotas` 或“配额已被压低”。ownership/配置读失败 MUST 返回 `503`，MUST NOT 降级为 `binding_unknown`，MUST NOT 返回看起来正常的空投影。

#### Scenario: 从未启动且未绑定的环境也能读到已开启配置

- **WHEN** 某 `envKey` 的所有者读取一个边缘从未连接、没有账号绑定、但环境慢启动已开启的环境
- **THEN** customer-auth 返回 `state=active`、环境起点与当前天数，并标注 `binding_unknown`
- **AND** 回包 MUST NOT 包含 accountId、`binding` 或 `dayQuotas`

#### Scenario: 有绑定时返回与实际 clamp 同源的真态

- **WHEN** 某环境存在唯一有效账号绑定且所有者读取慢启动状态
- **THEN** customer-auth 返回该账号 controller 基于该环境起点得出的慢启动真态与生效后的当日上限
- **AND** 回包 MUST NOT 包含 accountId

#### Scenario: 读路由不得泄露他人环境

- **WHEN** 某已登录客户读取不属于自己的 `envKey`
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 泄露该环境的账号身份或慢启动状态

#### Scenario: 读路由的查询失败同样不得伪装

- **WHEN** ownership、环境配置或 controller 取用因数据库不可达而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 返回空投影
