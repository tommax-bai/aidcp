## ADDED Requirements

### Requirement: 客户只能为当前环境上正在运行的账号开关慢启动

customer-auth SHALL 提供 env-scoped `PUT /environments/:envKey/slow-start`。请求体 MUST 只接受 `enabled`，夹带任何其它键 MUST 整块拒绝且不写入。

**accountId MUST 由云端解析、MUST NOT 由客户端提交**。解析 SHALL 经边缘会话的**活映射**（当前 OPEN 且非 stale 的连接所声明的账号），MUST NOT 接受请求体或查询参数中的账号选择器，MUST NOT 依赖持久化的环境↔账号绑定表——持久绑定会陈旧（账号早已从该环境撤走而绑定行仍在），且其账号身份同样源自无凭据握手，只是把「现在自称是谁」冻成「曾经自称是谁」。

授权 SHALL 在同一 enabled-user 与 env ownership 权威范围内进行：客户 MUST 拥有该 `envKey`，否则 fail-closed。

该路由 MUST NOT 修改风控档位、风控终态、账号写总闸或任何其它账号配置——`slow_start_since` 是唯一可被本路由写入的字段。

成功回包 SHALL 返回写后真态与生效后的当日上限。因慢启动的执行体位于云端配额计算内、且开关经运行时现读生效，云端写入成功即为已生效，回包 MUST NOT 引入「已保存 / 待下发边缘」二态——照抄一个不存在的状态同样是不诚实。

#### Scenario: 环境所有者开启当前运行账号的慢启动

- **WHEN** 某 `envKey` 的所有者在该环境边缘在线时提交 `{ enabled: true }`
- **THEN** 云端解析出该边缘当前声明的 accountId，写入对齐运营自然日起点的 `slow_start_since`，回包带写后真态与生效后的当日上限

#### Scenario: 请求体夹带账号选择器被拒绝

- **WHEN** 请求体额外携带 `accountId`、`since`、`quotaLevel` 或任何其它键
- **THEN** customer-auth 返回校验失败且不写入任何字段

#### Scenario: 非所有者请求 fail-closed

- **WHEN** 某已登录客户对不属于自己的 `envKey` 提交请求
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 写入，MUST NOT 泄露该环境的账号身份

#### Scenario: 边缘未连接时诚实拒绝

- **WHEN** 某 `envKey` 当前没有 OPEN 且非 stale 的边缘连接
- **THEN** customer-auth 返回「该环境当前未连接」的冲突态，MUST NOT 写入
- **AND** MUST NOT 回落到任何持久快照或历史账号身份

#### Scenario: 同环境解析出多个账号时诚实失败

- **WHEN** 活映射对某 `envKey` 解析出多于一个候选账号
- **THEN** customer-auth 诚实失败且不写入，MUST NOT 任取其一

#### Scenario: 关闭慢启动只清起点不动其它

- **WHEN** 环境所有者提交 `{ enabled: false }`
- **THEN** 云端只清空该账号 `slow_start_since`，其风控档位、风控终态与其它账号配置逐位保持原值
