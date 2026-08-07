## MODIFIED Requirements

### Requirement: 慢启动状态 SHALL 提供不依赖边缘或账号绑定的 env-scoped 读

customer-auth SHALL 提供 env-scoped `GET /environments/:envKey/slow-start`，在该环境边缘不在线（含从未启动）或尚未绑定账号时也返回该环境的慢启动配置真态。

该读 SHALL 先按 ownership 读取环境自己的 `slow_start_since`。有唯一有效当前账号绑定时，SHALL 复用与 `ui.push_snapshot` 慢启动投影同一个 controller 产出（同一环境 anchor 解析、同一次 clock），MUST NOT 另行推算绑定性或上限。回包 MUST NOT 包含 accountId 或任何其它账号身份标识。

环境未绑定账号或绑定账号不存在时，该读 SHALL 保留环境配置态：关闭返回 `state=off`；开启返回 `state=active`、`since`、`day` 与 `totalDays`，同时返回 `eligible=false`、`ineligibleReason=binding_unknown`。此时 MUST NOT 编造 `binding`、`dayQuotas` 或“配额已被压低”。ownership/配置读失败 MUST 返回 `503`，MUST NOT 降级为 `binding_unknown`，MUST NOT 返回看起来正常的空投影。

`totalDays` SHALL 在**所有**分支取当前生效的权威总天数：Facebook 环境取后台全局策略的总天数，其它平台取该平台曲线的固有总天数；策略此刻取不到时取配额 clamp 同一时刻实际采用的回落天数。任何分支 MUST NOT 内联一个与权威值无关的常量——绑定与未绑定两条路径对同一环境报出不同总天数，与谎报状态同属不诚实。

该读 SHALL 在环境平台为 Facebook 时额外返回**当前生效的慢启动曲线**：总天数与逐日动作上限，且 MUST 与配额 clamp 取自同一份后台权威配置。曲线的每一行 SHALL 只包含该平台结构上能执行、且风控确实按日计数的动作。环境平台判据 SHALL 与该服务既有的 Facebook 环境准入同源，MUST NOT 另写一份平台比较。

同一环境慢启动配置的**写后回读**（开关写入的回执）SHALL 按与本读逐字相同的规则携带曲线与总天数。客户端按该回执整体覆盖此环境的慢启动状态，回执不带曲线即等于让客户端把已读到的曲线丢掉——「点一下开关，曲线表就消失了」。

曲线**缺席只有一种表达：整个字段不出现**。运行时策略不可用、环境平台非 Facebook、或平台未确认时，该读 MUST NOT 返回编译期默认曲线、空数组或全零曲线——默认曲线可能比运营当前所配更松，空曲线等同于宣称该账号没有任何逐日上限。缺席 MUST NOT 使该读失败：其余慢启动真态照常返回。

#### Scenario: 从未启动且未绑定的环境也能读到已开启配置

- **WHEN** 某 `envKey` 的所有者读取一个边缘从未连接、没有账号绑定、但环境慢启动已开启的环境
- **THEN** customer-auth 返回 `state=active`、环境起点与当前天数，并标注 `binding_unknown`
- **AND** 回包 MUST NOT 包含 accountId、`binding` 或 `dayQuotas`

#### Scenario: 有绑定时返回与实际 clamp 同源的真态

- **WHEN** 某环境存在唯一有效账号绑定且所有者读取慢启动状态
- **THEN** customer-auth 返回该账号 controller 基于该环境起点得出的慢启动真态与生效后的当日上限
- **AND** 回包 MUST NOT 包含 accountId

#### Scenario: Facebook 环境返回与 clamp 同源的曲线

- **WHEN** 某 Facebook 环境的所有者读取慢启动状态，且运营已在后台把总天数改为 10 天、并调整了其中若干天的上限
- **THEN** customer-auth 返回的曲线为 10 行，且每一行的数字逐格等于配额 clamp 当天会采用的上限
- **AND** `totalDays` 为 10

#### Scenario: 未绑定账号的 Facebook 环境同样按权威总天数作答

- **WHEN** 运营已把总天数改为 10 天，某未绑定账号的 Facebook 环境所有者读取慢启动状态
- **THEN** `totalDays` 为 10，MUST NOT 为内联常量 7
- **AND** 该分支仍 MUST NOT 返回 `binding` 或 `dayQuotas`

#### Scenario: 非 Facebook 环境不返回曲线字段

- **WHEN** 某小红书环境的所有者读取慢启动状态
- **THEN** 回包整个不含曲线字段
- **AND** 其余慢启动真态照常返回

#### Scenario: 写后回执与读同规则带曲线

- **WHEN** 某 Facebook 环境的所有者开启或关闭慢启动，写入成功
- **THEN** 回执按与读相同的规则携带当前生效曲线与权威总天数
- **AND** 回执 MUST NOT 因此出现任何表达「已保存 / 待下发边缘」的字段

#### Scenario: 运行时策略不可用时曲线缺席而非编造

- **WHEN** Facebook 运行时全局策略此刻取不到
- **THEN** 回包整个不含曲线字段，MUST NOT 返回编译期默认曲线、空数组或全零曲线
- **AND** 该读仍返回可用的慢启动真态，MUST NOT 因此失败

#### Scenario: 读路由不得泄露他人环境

- **WHEN** 某已登录客户读取不属于自己的 `envKey`
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 泄露该环境的账号身份或慢启动状态

#### Scenario: 读路由的查询失败同样不得伪装

- **WHEN** ownership、环境配置或 controller 取用因数据库不可达而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 返回空投影
