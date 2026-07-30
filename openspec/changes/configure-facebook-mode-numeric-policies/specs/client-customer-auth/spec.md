## MODIFIED Requirements

### Requirement: 程序化 Facebook 环境归属与默认慢启动原子完成

customer-auth 的程序化环境归属完成接口 SHALL 接受可选布尔字段 `slowStartEnabled`，并保持省略该字段的旧客户端请求兼容。`slowStartEnabled=true` MUST 仅在同一请求的规范平台为 `facebook` 时接受；小红书、视频号、未知平台或非布尔值 MUST fail-closed，且不得部分注册环境或写入归属。

该接口 SHALL 另外接受两个可选的 Facebook 专属创建意图：环境规则模式开启意图与环境评论审批覆盖模式（`source_rules|auto_approve_all`）。两者 MUST 仅在规范平台为 `facebook` 时接受，非 Facebook 平台、非法枚举或非布尔值 MUST 在注册环境前拒绝整个请求。请求体 MUST 继续走严格白名单：夹带白名单之外的任何键 MUST 整块拒绝且不写入。`slowStartEnabled=true` 与规则模式开启意图 MUST NOT 在同一请求中同时为真，同时提交 MUST fail-closed 拒绝，MUST NOT 静默取其一。

首次成功完成 Facebook 创建 intent 时，Cloud SHALL 在同一数据库事务中插入环境、写入唯一客户归属、完成 intent，并按本次提交的意图写入该环境的慢启动生命周期、规则模式配置与评论审批策略。`slowStartEnabled=true` 时，慢启动生命周期 MUST 同时写入服务端当前时刻所属上海自然日 00:00 的 `slow_start_since` 与当时全局 current、published、完整、fresh 且 schema 兼容的 slow-start policy revision pin，并显式标记初始化完成；未提交开启意图时起点与 pin 均保持 NULL。起点 MUST NOT 取 Edge 时钟、账号入库时间、Cookie 时间或 `accounts.slow_start_since`。

`slowStartEnabled=true` 所需的全局 current revision、完整 definition、freshness 或 schema compatibility 任一缺失、陈旧、无效或不兼容时，整个环境插入、唯一归属、intent 完成和全部创建意图写入 MUST 在同一事务中失败；MUST NOT 留下未 pin 的起点、已归属但未完成的环境、已完成 intent 或其它部分状态，也 MUST NOT 回落到 legacy 编译期数字。

已完成 intent 的幂等重试 MUST 只返回既成归属，不得再次校验后改写、重置或换版慢启动起点与 pin、规则模式配置或审批策略；若运营在首次完成后手动更改过其中任何一项，陈旧重试 MUST NOT 复原。接口不得修改风控档位、风险状态、账号旧慢启动列或其它环境配置。

#### Scenario: Facebook 创建原子写入 D1 起点与 policy pin

- **WHEN** 有效客户使用待完成 intent 注册一个全新 Facebook 环境并提交 `slowStartEnabled=true`
- **THEN** 环境、归属、intent 完成态、上海当日 00:00 起点与当时 compatible global current revision pin 在同一事务中提交
- **AND** 起点与 pin 均不得先于或晚于环境归属单独可见

#### Scenario: 创建所需策略不可用时整单失败

- **WHEN** `slowStartEnabled=true`，但全局 current slow-start revision 或其完整 definition 缺失、陈旧、无效或 schema 不兼容
- **THEN** Cloud 在同一事务中拒绝环境、归属、intent 完成及所有创建意图写入
- **AND** MUST NOT 写入起点后留空 pin、回落编译期七日表或把 intent 标成已完成

#### Scenario: Facebook 创建原子写入规则模式与免审

- **WHEN** 有效客户在完成请求中提交规则模式开启意图与 `auto_approve_all`
- **THEN** 环境、归属、intent 完成态、该环境规则模式配置与评论审批策略在同一事务中提交
- **AND** 未提交慢启动开启意图时该环境慢启动起点与 active pin 均保持 NULL

#### Scenario: 旧客户端省略字段保持兼容

- **WHEN** 有效旧客户端完成环境归属但未提交 `slowStartEnabled`
- **THEN** 请求继续按既有规则成功，环境慢启动起点与 active pin 均保持 NULL

#### Scenario: 非 Facebook 开启意图原子拒绝

- **WHEN** 请求以小红书、视频号或未知平台提交 `slowStartEnabled=true`、规则模式开启意图或审批模式字段
- **THEN** Cloud 在注册环境前拒绝整个请求，环境、归属和 intent 均不发生部分写入

#### Scenario: 慢启动与规则模式互斥意图被拒绝

- **WHEN** 同一 Facebook 完成请求同时提交 `slowStartEnabled=true` 与规则模式开启意图
- **THEN** Cloud 在注册环境前拒绝整个请求，MUST NOT 只取其中一项写入

#### Scenario: 完成重试不重置、换版或复活慢启动

- **WHEN** Facebook intent 已成功完成，随后同一 intent/环境被再次提交
- **THEN** Cloud 返回幂等成功但不更新 `slow_start_since`、active policy pin、规则模式配置或审批策略
- **AND** 即使全局 current 已变化或该环境已被运营手动更改，也不得改用新 revision 或复原为创建时的值

### Requirement: 客户只能为自己的环境开关慢启动，且不依赖账号绑定或边缘在线

customer-auth SHALL 提供 env-scoped `PUT /environments/:envKey/slow-start`。请求体 MUST 只接受 `enabled`，夹带任何其它键 MUST 整块拒绝且不写入；客户不能提交 policy revision、每日数字、动作、Prompt 或任何内部策略字段。

慢启动配置 SHALL 直接持久化在 `envKey` 对应的环境记录；`accountId` MUST NOT 由客户端提交，也 MUST NOT 作为写入目标选择器。该路由 MUST NOT 依赖环境↔账号绑定、账号是否存在、边缘活会话、浏览器是否运行或环境是否已启动。

授权 SHALL 在同一 enabled-user 与 env ownership 权威范围内进行：客户 MUST 拥有该 `envKey`，否则 fail-closed。首次开启时，Cloud MUST 在同一事务写入对齐运营自然日起点的 `slow_start_since` 与当时全局当前的 published、完整、fresh 且 schema 兼容的 slow-start revision pin；全局当前策略或完整 definition 缺失、陈旧、非法或不兼容时整次开启失败。重复 `{enabled:true}` MUST 幂等保留既有起点与 pin。关闭时 SHALL 在同一事务清空起点与 active pin；这是现有明确授权的生命周期状态变更，只依赖可证的 ownership 与环境写真态，不得因已不再需要解析的 policy detail 或客户端 capability 缺失、陈旧或不可读而被阻断，关闭后其它 RiskController、session、daily 与全局安全闸仍照常裁决。该路由 MUST NOT 修改当前或历史账号的慢启动字段、风控档位、风控终态、账号写总闸或任何其它账号配置。

成功回包 SHALL 返回写后环境配置真态，并按本规格的完整 policy envelope 返回可用的 active/next policy；不得返回裸 revision 或缺 metadata 的部分七日表。有唯一有效当前账号绑定时，回包还 SHALL 返回该账号 controller 依据同一环境起点和 active pin 算出的生效状态与当日上限；没有有效绑定时，回包 SHALL 明确标注 `binding_unknown` 且不编造 `binding` 或当日最终上限。云端环境写入成功即为配置已保存，回包 MUST NOT 引入「已保存 / 待下发边缘」二态；没有账号时 SHALL 表述为当前没有执行对象，而非写入尚未完成。

#### Scenario: 边缘离线且未绑定账号时仍能开启环境慢启动

- **WHEN** 某 `envKey` 的所有者在该环境边缘未连接且没有账号绑定时提交 `{ enabled: true }`
- **THEN** 云端原子写入对齐运营自然日的起点与当时全局当前 revision pin，并返回已开启配置及完整七日策略
- **AND** 回包标注 `eligible=false` 与 `ineligibleReason=binding_unknown`，MUST NOT 返回伪造的 `binding` 或当日最终 `dayQuotas`

#### Scenario: 重复开启不重置或换版

- **WHEN** 环境已按 revision 4 开启后全局当前变为 revision 5，客户再次提交 `{ enabled: true }`
- **THEN** 云端幂等返回原起点与 revision 4 active pin
- **AND** MUST NOT 重置 day 或把该生命周期改成 revision 5

#### Scenario: 环境换绑后设置不随旧账号离开

- **WHEN** 已开启慢启动的环境从账号 A 换绑为账号 B
- **THEN** 环境的 `slow_start_since` 与 active revision 逐位保持不变
- **AND** 下一次配额计算中账号 B 使用该环境起点与 pin，账号 A 不再因该环境被 clamp，MUST NOT 要求重启

#### Scenario: 请求体夹带账号或策略选择器被拒绝

- **WHEN** 请求体额外携带 `accountId`、`since`、`policyRevision`、`dailyCaps`、`quotaLevel` 或任何其它键
- **THEN** customer-auth 返回校验失败且不写入任何环境、策略或账号字段

#### Scenario: 非所有者请求 fail-closed

- **WHEN** 某已登录客户对不属于自己的 `envKey` 提交请求
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 写入，MUST NOT 泄露该环境的账号身份或配置

#### Scenario: 环境注册表查询失败 MUST NOT 伪装成未绑定

- **WHEN** ownership 或环境配置读取因数据库不可达、表缺失或镜像不可用而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 把「没写成」表述为配置已保存

#### Scenario: 当前策略不可用只阻止开启

- **WHEN** 当前策略 detail 缺失、陈旧或不兼容，且环境所有者分别尝试 `{ enabled: true }` 与 `{ enabled: false }`
- **THEN** 开启以具名 policy blocker 失败且不写入起点或 pin
- **AND** 关闭仍原子清空环境起点与 pin，并把 policy detail 单独标为 unavailable

#### Scenario: 关闭慢启动原子清除环境生命周期

- **WHEN** 环境所有者提交 `{ enabled: false }`
- **THEN** 云端原子清空该环境的 `slow_start_since` 与 active policy pin
- **AND** 当前及历史账号的慢启动旧列、风控档位、风控终态与其它账号配置逐位保持原值
- **AND** policy detail 或 `facebook_mode_policy_projection_v1` capability 缺失、陈旧或不可读不得阻止关闭

### Requirement: 慢启动状态 SHALL 提供不依赖边缘或账号绑定的 env-scoped 读

customer-auth SHALL 提供 env-scoped `GET /environments/:envKey/slow-start`，在该环境边缘不在线（含从未启动）或尚未绑定账号时也返回该环境的慢启动配置真态和完整只读策略 envelope。

该读 SHALL 先按 ownership 读取环境自己的 `slow_start_since` 与 active pin。环境开启或毕业时 SHALL 返回 active pin 对应的完整 `activePolicy` envelope；环境关闭或毕业时 SHALL 另行返回全局 current revision 的完整 `nextEnablePolicy` envelope，并明确它只供以后开启。active 与全局 current 不同时必须分别呈现，MUST NOT 拼接两个 revision 的 metadata 或数值。有唯一有效当前账号绑定时，SHALL 复用与 `ui.snapshot` 慢启动投影同一个 controller 产出（同一环境 anchor+pin 解析、同一次 clock），MUST NOT 另行推算绑定性或上限。回包 MUST NOT 包含 accountId、草稿、历史版本、内部 actor 或影响统计。

环境未绑定账号或绑定账号不存在时，该读 SHALL 保留环境配置态：关闭返回 `state=off` 与 `nextEnablePolicy`；开启且仍在七日内返回 `state=active`、`since`、`day`、`totalDays` 与 `activePolicy`，已过七日则返回 `state=graduated`、原 active pin 的 `activePolicy` 与单独的 `nextEnablePolicy`，同时返回 `eligible=false`、`ineligibleReason=binding_unknown`。此时 MUST NOT 编造 `binding`、当日最终 `dayQuotas` 或“配额已被压低”。ownership/配置/policy 读失败 MUST 返回 `503` 或具名 unavailable，MUST NOT 降级为 `binding_unknown`，MUST NOT 返回看起来正常的空投影或编译期七日表。

#### Scenario: 从未启动且未绑定的环境也能读到已开启配置

- **WHEN** 某 `envKey` 的所有者读取一个边缘从未连接、没有账号绑定、但环境慢启动已开启的环境
- **THEN** customer-auth 返回 `state=active`、环境起点、当前天数、active revision 与完整七日策略，并标注 `binding_unknown`
- **AND** 回包 MUST NOT 包含 accountId、`binding` 或当日最终 `dayQuotas`

#### Scenario: 关闭环境显示下次开启版本

- **WHEN** 环境慢启动关闭且客户读取状态
- **THEN** 回包返回 `state=off` 与完整 `nextEnablePolicy` 并标明尚未 active
- **AND** MUST NOT 伪造 active revision、since、day 或 clamp

#### Scenario: 有绑定时返回与实际 clamp 同源的真态

- **WHEN** 某环境存在唯一有效账号绑定且所有者读取慢启动状态
- **THEN** customer-auth 返回该账号 controller 基于同一环境起点与 active revision 得出的慢启动真态、策略和生效后的当日上限
- **AND** 回包 MUST NOT 包含 accountId

#### Scenario: active 与 current 版本不得拼接

- **WHEN** 环境 active revision 为 4，而全局 current revision 已为 5
- **THEN** 回包的 `activePolicy` 完整 envelope 来自 revision 4，并把 revision 5 作为独立完整 `nextEnablePolicy` envelope 标为之后开启采用
- **AND** MUST NOT 使用 revision 5 的任一 metadata、day/action 值或 digest 覆盖 active policy

#### Scenario: 读路由不得泄露他人环境

- **WHEN** 某已登录客户读取不属于自己的 `envKey`
- **THEN** customer-auth fail-closed 拒绝，MUST NOT 泄露该环境的账号身份或慢启动状态

#### Scenario: 读路由的查询失败同样不得伪装

- **WHEN** ownership、环境配置、policy 或 controller 取用因数据库不可达而失败
- **THEN** customer-auth 返回 `503`，MUST NOT 返回 `binding_unknown`，MUST NOT 返回空投影

## ADDED Requirements

### Requirement: customer-auth 模式数字策略只读投影必须使用完整 envelope

customer-auth 的 env-scoped Facebook 规则模式与慢启动 GET，以及携带写后只读投影的成功 PUT/程序化归属回包，SHALL 对每个 `currentPolicy`、`appliedPolicy`、`adoptedPolicy`、`activePolicy` 或 `nextEnablePolicy` 分别返回完整、不可拆分的 envelope。每个 envelope MUST 包含与权威路由环境逐位相等的 `envKey`、固定枚举 `kind=rule-mode|slow-start`、不可变 `revision`、`schemaVersion`、服务端观测时间 `asOf`、有界 `freshUntil` 和 `complete=true`；Cloud MAY 同时返回覆盖上述 metadata 与完整 typed payload 的稳定 `digest`。规则策略 payload MUST 同时包含同 revision 的 `viewThreshold` 与 `joinEveryNRounds`；慢启动 payload MUST 同时包含 `totalDays=7` 与 `days`，其中 `days` 恰好七行，每行只含 `day=1..7` 与完整固定七动作 `dailyCaps`。顶层 `dayQuotas` 仅在有唯一绑定账号时表示同一次 controller 算出的当日最终额度，MUST NOT 放进 policy envelope 或用来表示七日矩阵。规则模式的 `appliedPolicy` SHALL 另外携带 execution target、`appliedCursor` 与 owner-current propagation lag，且 MUST NOT 用 owner current 冒充尚未应用的 target current。

同一响应中的 current/applied/adopted 或 active/next 是相互独立的 envelope。Cloud 与 Edge MUST 分别逐个验证 envKey、kind、revision、schemaVersion、freshness、complete 和完整 payload，若存在 digest 则必须一并验证；MUST NOT 从另一个 envelope、本地常量、历史缓存或裸 revision 补字段。任一 envelope 缺字段、过期、结构无效或所带 digest 不匹配时，Cloud MUST 将该 policy slot 标成具名 unavailable，MUST NOT 返回 `complete=true` 的部分对象；若环境 `enabled` 真态仍可独立证明，响应 SHALL 保留该开关真态并把 policy detail unavailable 与关闭态分开。

#### Scenario: 规则 current、applied 与 adopted 各自完整

- **WHEN** 规则模式 owner current 为 revision 9、target applied current 为 revision 8，而当前账号仍采用 revision 7
- **THEN** customer-auth 返回三个分别完整的 rule-mode envelope，每个都有自己的 envKey、revision、schemaVersion、asOf、freshUntil、complete 与两项数字，applied envelope 另含 target/cursor/lag
- **AND** MUST NOT 跨 revision 拼接阈值、周期或 metadata，也不得把 publish 误报为 target 已应用

#### Scenario: 慢启动 active 与 next 各自完整

- **WHEN** 环境 active pin 为 revision 4，而全局 current 已为 revision 5
- **THEN** `activePolicy` 与 `nextEnablePolicy` 分别返回完整 slow-start envelope 与各自完整 `days[7].dailyCaps`
- **AND** 任一 envelope 不完整时只将对应 slot 标成 unavailable，不得用另一份 revision 补齐

#### Scenario: 详情 unavailable 不覆盖开关真态

- **WHEN** Cloud 可证明环境规则模式已关闭，但无法读取 current policy detail
- **THEN** customer-auth 返回 `enabled=false` 与具名 policy unavailable，不返回伪造的完整 envelope
- **AND** Edge 不把 unavailable detail 改写为 legacy 数字或开启态

### Requirement: Edge policy projection capability 必须按环境留存并机械门禁非 legacy 采用

支持动态模式数字投影的新 Edge SHALL 在相关 customer-auth 环境读写与程序化环境归属完成请求中，通过 `X-AIDCP-Client-Capabilities` 上报精确 marker `facebook_mode_policy_projection_v1`。Cloud MUST 在客户鉴权、规范 `envKey` 解析与 ownership 校验成功后，或在有效 create-intent completion 的同一事务中，按 envKey 保存服务端生成的最新 observation；客户端 MUST NOT 提交或覆盖 observedAt。header 含精确 marker 时保存 `supported=true`，相关请求未携带 marker 或值非法时保存新的 `supported=false` negative observation，从而立即撤销旧 positive 并识别客户端降级。positive freshness 固定为 `observedAt + 30 days`，只有服务端再次观察到 marker 才可续期；negative、missing 与过期 positive 均不得满足门禁。一个环境的 observation MUST NOT 转移、继承或推断给另一环境。

程序化创建请求可在同一原子事务中为新 envKey 记录 positive observation，并用该服务端 observation 满足本次创建的 capability gate；该 gate 失败时环境、归属、intent 与全部创建意图 MUST 一起回滚。对 non-legacy global current revision，首次开启慢启动、把规则模式从关闭改为开启，以及规则运行在安全边界采用该 revision 前，Cloud MUST 要求目标 envKey 存在 fresh positive `facebook_mode_policy_projection_v1` observation；missing、negative 与过期 positive SHALL 分别产生具名 `facebook_mode_policy_projection_capability_missing`、`facebook_mode_policy_projection_capability_unsupported`、`facebook_mode_policy_projection_capability_stale` blocker，不得 pin/adopt 新 revision、开始新规则进度或回落 legacy 数字。automation SHALL 只使用随 `client_environment_automation` 同 cursor 原子应用的本地 observation，不得直连 API store。legacy current 继续允许不携带 marker 的旧 Edge 使用既有开关，但升级后的 Cloud 仍 MUST 解析已迁移的 immutable legacy revision；revision/definition 不可读时不得以编译期数字补成成功。

capability gate 只限制会准入 non-legacy 数字的新开启/新采用。ownership 与环境写真态可证时，把规则模式从开启改为关闭 MUST 即使 current/applied/adopted policy detail 或 capability missing/stale 也成功只写 `enabled=false`，因为它减少规则工作；关闭慢启动属于既有显式生命周期控制，同样 MUST 原子清空 anchor 与 active pin，且之后仍由全部普通风险与安全闸裁决。已完成创建 intent 的幂等重试、重复开启一个已有 anchor+pin 的慢启动生命周期，也 MUST 返回原真态而不借 capability 重新 pin 或换版。

#### Scenario: 新 Edge observation 在三十天内满足门禁

- **WHEN** Cloud 在目标 envKey 的已认证请求中于服务端时间 T 观察到 `facebook_mode_policy_projection_v1`，并在 T 后 30 天内尝试启用非 legacy slow-start revision
- **THEN** capability gate 允许继续执行其它 policy、ownership 与原子写校验
- **AND** Cloud 使用服务端 T 而非客户端时间计算 freshness

#### Scenario: marker 缺失或陈旧阻止非 legacy 采用

- **WHEN** 目标环境从未上报 marker，或最后一次服务端 `observedAt` 已超过 30 天，且规则运行准备采用非 legacy current revision
- **THEN** Cloud 分别投影 missing 或 stale named blocker，不采用 revision、不累计新 view、不创建 round
- **AND** MUST NOT 把旧 Edge、离线状态或缺 header 推断为已兼容

#### Scenario: 客户端降级产生 negative observation

- **WHEN** 某环境曾由新 Edge 上报 positive marker，随后一次已认证 owned-environment 请求不再携带该 marker
- **THEN** Cloud 以新的 server observedAt 保存 `supported=false` 并通过同一 gate snapshot 传播
- **AND** 后续 non-legacy publish/enable/adoption 返回 `facebook_mode_policy_projection_capability_unsupported`，不得继续沿用旧 positive 的剩余 30 天

#### Scenario: 创建请求中的 marker 与环境归属原子生效

- **WHEN** 新 Edge 以有效 intent 创建 Facebook 环境、携带 marker 并请求 `slowStartEnabled=true`，且 current policy 完整兼容
- **THEN** 环境、归属、intent、server-observed capability、上海 anchor 与 current pin 在同一事务中提交
- **AND** 任一部分失败时全部回滚

#### Scenario: 关闭规则在 policy detail unavailable 时仍降风险

- **WHEN** 环境 ownership 与现有规则 `enabled=true` 可证，但 current/adopted detail 不可读或 capability missing/stale
- **THEN** 客户提交 `{enabled:false}` 仍成功把该环境规则模式关闭并返回写后开关真态
- **AND** policy detail 单独显示具名 unavailable，MUST NOT 阻止关闭或合成 legacy 默认
