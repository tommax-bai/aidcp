## RENAMED Requirements

- FROM: `### Requirement: 客户只能为当前环境上正在运行的账号开关慢启动`
- TO: `### Requirement: 客户只能为自己环境上已绑定的账号开关慢启动，且不依赖边缘在线`

## MODIFIED Requirements

### Requirement: 客户只能为自己环境上已绑定的账号开关慢启动，且不依赖边缘在线

customer-auth SHALL 提供 env-scoped `PUT /environments/:envKey/slow-start`。请求体 MUST 只接受 `enabled`，夹带任何其它键 MUST 整块拒绝且不写入。

**accountId MUST 由云端解析、MUST NOT 由客户端提交**。解析 SHALL 经**持久的环境↔账号绑定**（change `curated-envkey-account-binding` 所建、`env_key` 为 PK ⇒ 一个环境至多一个账号），MUST NOT 接受请求体或查询参数中的账号选择器，**MUST NOT 依赖边缘活会话**。

该路由 MUST NOT 要求该环境的边缘在线：`slow_start_since` 的执行体位于云端配额计算内、经运行时现读生效，边缘对这次写入**没有任何参与**。以边缘在线与否为前置 SHALL 被视为缺陷。

授权 SHALL 在同一 enabled-user 与 env ownership 权威范围内进行：客户 MUST 拥有该 `envKey`，否则 fail-closed。绑定读 SHALL 与 `accounts` 关联校验，悬空绑定 MUST fail-closed，MUST NOT 当作有效目标。

该路由 MUST NOT 修改风控档位、风控终态、账号写总闸或任何其它账号配置——`slow_start_since` 是唯一可被本路由写入的字段。

成功回包 SHALL 返回写后真态与生效后的当日上限。因慢启动的执行体位于云端配额计算内、且开关经运行时现读生效，云端写入成功即为已生效，回包 MUST NOT 引入「已保存 / 待下发边缘」二态——照抄一个不存在的状态同样是不诚实。

#### Scenario: 边缘离线时环境所有者仍能开启慢启动

- **WHEN** 某 `envKey` 的所有者在该环境**边缘未连接**（含从未启动）但存在有效账号绑定时提交 `{ enabled: true }`
- **THEN** 云端经持久绑定解析出 accountId，写入对齐运营自然日起点的 `slow_start_since`，回包带写后真态与生效后的当日上限
- **AND** customer-auth MUST NOT 因边缘不在线而拒绝

#### Scenario: 环境未绑定账号时诚实冲突

- **WHEN** 某 `envKey` 没有账号绑定行，或绑定指向的账号在 `accounts` 中不存在
- **THEN** customer-auth 返回 `409 binding_unknown`，MUST NOT 写入，MUST NOT 猜测任何账号

#### Scenario: 绑定查询失败 MUST NOT 伪装成未绑定

- **WHEN** 绑定读因数据库不可达或表缺失而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 把「没查成」表述为「该环境没有绑定账号」

#### Scenario: 请求体夹带账号选择器被拒绝

- **WHEN** 请求体额外携带 `accountId`、`since`、`quotaLevel` 或任何其它键
- **THEN** customer-auth 返回校验失败且不写入任何字段

#### Scenario: 非所有者请求 fail-closed

- **WHEN** 某已登录客户对不属于自己的 `envKey` 提交请求
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 写入，MUST NOT 泄露该环境的账号身份

#### Scenario: 关闭慢启动只清起点不动其它

- **WHEN** 环境所有者提交 `{ enabled: false }`
- **THEN** 云端只清空该账号 `slow_start_since`，其风控档位、风控终态与其它账号配置逐位保持原值

## ADDED Requirements

### Requirement: 慢启动状态 SHALL 提供不依赖边缘的 env-scoped 读

customer-auth SHALL 提供 env-scoped `GET /environments/:envKey/slow-start`，在该环境边缘不在线（含从未启动）时也返回该环境的慢启动真态与生效后的当日上限。

该读 SHALL 经与写路由**同一份持久绑定**解析 accountId，SHALL 复用与 `ui.snapshot` 慢启动投影**同一个 controller 产出**（同一 anchor 解析、同一次 clock），MUST NOT 另行推算天数、绑定性或上限。

授权 SHALL 与写路由同口径：客户 MUST 拥有该 `envKey`，否则 fail-closed。回包 MUST NOT 包含 accountId 或任何其它账号身份标识。

环境未绑定账号时，该读 SHALL 返回 `eligible=false` 且 `ineligibleReason=binding_unknown` 的诚实投影；此时 MUST NOT 编造 `state`、`day`、`since` 或 `totalDays`——没有账号即不知平台，任何默认值都是伪造。绑定读失败 MUST 返回 `503`，MUST NOT 降级为 `binding_unknown`，MUST NOT 返回一个看起来正常的空投影。

#### Scenario: 从未启动的环境也能读到慢启动真态

- **WHEN** 某 `envKey` 的所有者读取一个边缘从未连接、但存在有效账号绑定的环境
- **THEN** customer-auth 返回该账号的慢启动真态与生效后的当日上限
- **AND** 回包 MUST NOT 包含 accountId

#### Scenario: 未绑定环境返回诚实的不可用投影

- **WHEN** 客户读取一个自己拥有但没有账号绑定的环境
- **THEN** customer-auth 返回 `eligible=false` 与 `ineligibleReason=binding_unknown`
- **AND** 回包 MUST NOT 包含 `state`、`day`、`since` 或 `totalDays`

#### Scenario: 读路由不得泄露他人环境

- **WHEN** 某已登录客户读取不属于自己的 `envKey`
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 泄露该环境的账号身份或慢启动状态

#### Scenario: 读路由的查询失败同样不得伪装

- **WHEN** 绑定读或 controller 取用因数据库不可达而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 返回空投影

### Requirement: 命令定向下发 SHALL 继续以边缘活会话为准

「把命令发给哪台边缘」的解析 SHALL 继续基于活会话（OPEN 且非 stale 的连接），无在线节点时 SHALL 诚实失败、MUST NOT 广播。该在线判据 MUST NOT 因慢启动改用持久绑定而被一并摘除。

判据 SHALL 为：一道在线前置是**本质的**，当且仅当没有活边缘这件事本身就让该操作**无法被兑现**。命令下发没有收件人即无法兑现，故其在线判据是本质的；`slow_start_since` 的执行体在云端、幂等且可逆，故其在线判据是附带的、SHALL 被摘除。

反方向的「某边缘此刻在跑哪个账号」解析器在其最后一个生产调用点消失后 SHALL 被删除，MUST NOT 作为可复用工具留存——留存即为「按自报的活会话猜账号」保留一个现成入口。

#### Scenario: 账号无在线边缘时命令下发仍诚实失败

- **WHEN** 需要向某账号定向下发命令，但该账号没有 OPEN 且非 stale 的边缘连接
- **THEN** 云端诚实失败，MUST NOT 广播给其它边缘，MUST NOT 回落到持久绑定去猜一台机器

#### Scenario: 不可逆操作保留在线前置

- **WHEN** 某操作只有活浏览器才能真正兑现（如发布、建发布类委托任务）
- **THEN** 其边缘在线前置 MUST 保留，MUST NOT 援引慢启动的改动摘除它

#### Scenario: 一个环境至多解析出一个账号

- **WHEN** 云端为某 `envKey` 解析写入目标账号
- **THEN** 绑定的主键约束 SHALL 保证结果只能是恰好一个账号或没有绑定
- **AND** MUST NOT 存在「多个候选里任取其一」的路径
