## MODIFIED Requirements

### Requirement: Facebook 客户环境在慢启动附近显示规则模式开关

桌面客户端 SHALL 在当前客户环境明确为 Facebook 时，于每日用量区的慢启动开关附近呈现紧凑的规则模式开关和 Cloud 驱动的规则说明；非 Facebook、平台未知或不属于当前客户的环境 MUST NOT 呈现可操作的规则模式开关。开关 SHALL 只表达 Cloud 持久环境配置是否启用，MUST NOT 把启用配置表述为当前正在运行。说明 SHALL 区分 API owner current revision、当前 execution target applied current revision 与当前账号 adopted revision，并按 Cloud 回包展示对应 `viewThreshold`、`joinEveryNRounds`、传播等待及安全边界采用状态；客户端 MUST NOT 内置、推断或用旧常量补齐这些数字。

#### Scenario: Facebook 环境显示相邻开关

- **WHEN** 客户选择一个明确归属且平台为 Facebook 的环境
- **THEN** 客户端在慢启动开关附近显示规则模式开关及 Cloud 返回的数字策略摘要
- **AND** 说明明确慢启动开启时由慢启动优先、规则模式暂停

#### Scenario: 待采用版本与当前版本分开显示

- **WHEN** owner 或 target-applied current revision 已更新而绑定账号仍在旧 adopted revision 的非零收集进度或活动轮次中
- **THEN** 客户端分别显示 owner current、target applied current 与 adopted revision，并区分传播等待和下一安全收集边界采用
- **AND** 不用 current 数字重算当前进度或声称当前轮次已换版

#### Scenario: 其它平台不显示规则模式

- **WHEN** 客户选择小红书、视频号、未知平台或非归属环境
- **THEN** 客户端不显示可操作的 Facebook 规则模式开关

### Requirement: 客户端规则模式读写保持 Cloud 环境作用域权威

客户规则模式接口 SHALL 只接受当前客户 `envKey`，由 Cloud 复核环境归属并校验该环境的权威平台后，直接读取或写入**该环境**的规则模式启用配置。`accountId` MUST NOT 由客户端提交，也 MUST NOT 作为写入目标选择器。PUT 写请求 MUST 严格只接受 `{ enabled: boolean }`，客户端 MUST NOT 提交或选择 `accountId`、current/applied/adopted policy revision、`viewThreshold`、`joinEveryNRounds`、规则定义、运行进度、HTTP 目标或授权模式。该路由 MUST NOT 依赖环境↔账号绑定、账号是否存在、边缘活会话或环境内核是否停止。

成功回包 SHALL 返回写后环境启用真态，以及 owner current、target applied current 和 adopted policy 的独立完整 envelope；每份 envelope MUST 包含同一策略的 `envKey`、`kind`、`revision`、`schemaVersion`、`complete=true`、`asOf`、`freshUntil`、完整 typed numeric payload 与可选 digest，MUST NOT 跨 revision 拼接字段。有唯一有效当前账号绑定时，回包 SHALL 另外返回账号 adopted 快照、运行状态、是否等待 target 传播及是否等待安全边界采用。没有有效绑定时，回包 SHALL 明确标注没有执行对象且 MUST NOT 编造 adopted revision、进度或生效态。云端环境写入成功即为配置已保存，回包 MUST NOT 引入「已保存 / 待下发边缘」二态。任何引用的 revision 缺失、陈旧、未发布、结构无效或不兼容时，接口 SHALL 返回具名不可用状态，MUST NOT 用编译期旧数字补齐。

支持动态策略投影的新 Edge SHALL 在已认证环境 GET/PUT 与创建完成请求上发送 `X-AIDCP-Client-Capabilities: facebook_mode_policy_projection_v1`。Cloud SHALL 只为已授权 `envKey` 或有效 create-intent completion 记录服务端 observation：含 marker 为 positive，相关请求缺 marker/非法为 negative；positive 仅在 30 天内为 fresh。non-legacy current 下从关闭到开启规则模式、以及账号在零进度边界采用新的 non-legacy revision，均 MUST 要求该环境 fresh positive capability；missing、negative 或过期 positive 时分别返回 `facebook_mode_policy_projection_capability_missing`、`facebook_mode_policy_projection_capability_unsupported`、`facebook_mode_policy_projection_capability_stale`，不得采用。automation adoption MUST 使用同一 `client_environment_automation` cursor 原子应用的本地 observation，不得热读 API。`{enabled:false}` 只减少平台工作，即使 policy detail 或 capability 不可用也 SHALL 在 ownership/platform 可证时允许并返回写后开关真态。

#### Scenario: 已绑定 Facebook 环境读取配置

- **WHEN** 已登录客户读取自己一个已唯一绑定账号的 Facebook 环境规则模式
- **THEN** Cloud 返回同一 `envKey` 的环境启用真态、owner current、target applied current/cursor、账号 adopted revision 与各自完整只读数字 envelope
- **AND** 响应不泄露 `accountId` 或内部更新者

#### Scenario: 已绑定 Facebook 环境写入配置

- **WHEN** 已登录客户为自己一个已唯一绑定账号的 Facebook 环境提交唯一字段 `{ enabled: boolean }`
- **THEN** Cloud 只写入该环境的规则模式启用配置并返回写后权威投影
- **AND** current/adopted revision 与数字不由该 PUT 改写，Edge 不创建任何本地规则配置或运行授权

#### Scenario: 缺少客户端能力时仍可关闭规则模式

- **WHEN** 已开启环境的 policy detail 或 `facebook_mode_policy_projection_v1` 观察缺失，而所有者提交 `{ enabled: false }`
- **THEN** Cloud 在 ownership 与 Facebook 平台可证时关闭环境规则模式并返回写后开关真态
- **AND** MUST NOT 因无法展示数字而强迫环境继续产生规则工作

#### Scenario: 非 legacy 开启需要当前请求能力

- **WHEN** owner current 为 non-legacy revision，而客户端未上报 capability 或该环境观察超过 30 天后提交 `{ enabled: true }`
- **THEN** Cloud 整块拒绝开启并返回具名 capability blocker
- **AND** 不修改启用配置、不采用 revision、不创建运行进度

#### Scenario: 未绑定账号的环境仍可预设

- **WHEN** 已登录客户为自己一个尚未绑定账号的 Facebook 环境提交 `{ enabled: true }`
- **THEN** Cloud 写入该环境启用配置并返回 owner current、可证的 target applied current 与已配置真态
- **AND** 回包标注当前没有执行对象，MUST NOT 伪造账号、adopted revision、进度或生效态

#### Scenario: 停止的环境仍可更改 Cloud 配置

- **WHEN** 客户拥有的 Facebook 环境内核已停止
- **THEN** 规则模式读写仍可通过 customer-auth 完成
- **AND** 系统不要求启动浏览器、Edge 会话或存在账号绑定来证明这次 Cloud 配置写入

#### Scenario: 非法范围、平台和额外字段失败关闭

- **WHEN** 环境不归属当前客户、环境平台不是 Facebook、环境注册表不可读，或 PUT 请求包含 `enabled` 之外的字段
- **THEN** Cloud 返回可区分的拒绝或不可用结果
- **AND** 不修改任何环境启用配置或全局策略

#### Scenario: 环境换绑不需要客户重新设置

- **WHEN** 客户已为某 Facebook 环境开启规则模式，该环境随后换绑到另一个账号
- **THEN** 客户端读到的该环境启用配置逐位不变并看到 owner current 与目标 applied current
- **AND** 新账号在零进度安全边界采用其 execution target 的 fresh applied current，客户 MUST NOT 被要求为新账号重新开启一次

### Requirement: 客户端使用非乐观权威回读呈现

客户端 SHALL 按 `envKey` 隔离规则模式读取和写入状态。环境启用配置未读取、读取中、接口不可用或响应不完整时 MUST 呈现未知/不可用并禁用开关，MUST NOT 默认为关闭。若启用配置可证但 current/adopted revision 或数字摘要缺失、陈旧、未发布、结构无效或不兼容，开关 SHALL 保持其独立 Cloud 真态，数字说明显示未知；客户端 MUST NOT 显示编译期旧数字，是否允许开关写入继续由 Cloud eligibility 裁决。写入中 SHALL 禁用控件并标记等待 Cloud 确认；只有同一环境的权威成功回执才能收敛为新开关值。失败或晚到的其它环境回执 MUST NOT 改写当前环境显示。

#### Scenario: 未知不冒充关闭

- **WHEN** customer-auth 未返回完整规则模式启用配置或配置读取失败
- **THEN** 客户端将开关显示为未知/不可用且不可操作
- **AND** 不把 checkbox 未选中解释为 Cloud 已关闭规则模式

#### Scenario: 数字详情未知不改写开关真态

- **WHEN** 环境启用配置可证但 current/adopted policy 详情缺失或非法
- **THEN** 客户端保持已确认开关真态并把数字说明显示为暂不可用
- **AND** 不回退显示本地数字或把详情未知伪装成模式关闭

#### Scenario: 写入等待权威确认

- **WHEN** 运营员切换规则模式且 Cloud 写请求尚未完成
- **THEN** 客户端显示正在开启或关闭并禁用重复提交
- **AND** 不提前宣称启用配置、current revision 或 adopted revision 已生效

#### Scenario: 写失败恢复原真态

- **WHEN** Cloud 拒绝或未完整确认规则模式写入
- **THEN** 客户端恢复最近一次同环境 Cloud 真态并显示失败原因
- **AND** 不保留乐观 checked 状态

#### Scenario: 环境切换隔离晚到回执

- **WHEN** 环境 A 的规则模式请求尚未完成时客户切换到环境 B
- **THEN** 环境 A 的回执只更新 A 的缓存
- **AND** 不改变环境 B 的开关、策略摘要和反馈

### Requirement: 客户端开关不得改变规则模式仲裁

客户端规则模式开关 SHALL 只通过 PUT `{ enabled: boolean }` 修改既有 Cloud 环境配置的 `enabled` 字段。Cloud 仍 MUST 在会话装配时应用既有平台、绑定人设、活跃时段、慢启动、风险和单飞仲裁；慢启动为 active 时规则模式 MUST 保持暂停且不累计进度。Edge MUST NOT 根据本地 checkbox 自行选择模式、采用策略版本、累计任何级别的规则节奏计数，或触发点赞、加群和评论。

两级节奏的阈值与周期一律由 Cloud execution target 已原子应用的 current revision 和账号 adopted immutable revision 决定，Edge MUST NOT 内置或推断任何节奏数字。已开始的非零收集序列与活动轮次 MUST 按 adopted revision 的数字快照自然收敛，只有活动轮次终结、指针清除且下一收集序列仍为零时才可采用 target applied current revision；新的 non-legacy adoption 还须通过该环境 fresh capability gate。动作集合、动作数量、先 like 后 join-contact 的顺序、Prompt 和所有既有安全闸始终固定且不由客户开关或数字策略改变。任一所需 adoption revision 未知、陈旧、未发布、结构无效或不兼容，或在途 snapshot 不完整时，Cloud 与 Edge MUST 对新规则工作失败关闭并呈现具名 blocker，不得回退到编译期数字。

#### Scenario: 慢启动继续优先

- **WHEN** 规则模式配置已开启且同一环境慢启动为 active
- **THEN** Cloud 继续选择慢启动而不是规则模式
- **AND** 客户端开关不绕过或覆盖该仲裁

#### Scenario: 客户端不内置节奏数字

- **WHEN** Cloud 的 owner current、target applied current 或账号 adopted revision 发生变化
- **THEN** 客户端无需发版即可按 Cloud 权威投影继续正确工作
- **AND** 客户端 MUST NOT 依据本地写死的浏览条数或轮次自行触发任何动作

#### Scenario: 安全边界前不采用新版本

- **WHEN** owner 或 target-applied current revision 更新时账号存在非零收集进度或活动轮次
- **THEN** 当前工作继续按 adopted revision 结算，Edge 不重算进度、不改变本轮动作
- **AND** 仅下一零进度收集边界可由 Cloud 采用新 revision

#### Scenario: 未知 revision 失败关闭

- **WHEN** Cloud 或 Edge 无法解析本次规则工作所需的精确 immutable revision
- **THEN** 不开始或推进新的收集、like 或 join-contact 工作，并呈现具名不可用原因
- **AND** 不使用任何本地或编译期默认数字
