# client-facebook-rule-mode-toggle Specification

## Purpose
TBD - created by archiving change client-facebook-rule-mode-toggle. Update Purpose after archive.
## Requirements
### Requirement: Facebook 客户环境在慢启动附近显示规则模式开关

桌面客户端 SHALL 在当前客户环境明确为 Facebook 时，于每日用量区的慢启动开关附近呈现紧凑的规则模式开关和固定说明；非 Facebook、平台未知或不属于当前客户的环境 MUST NOT 呈现可操作的规则模式开关。开关 SHALL 表达 Cloud 持久配置是否启用，MUST NOT 把启用配置表述为当前正在运行。

#### Scenario: Facebook 环境显示相邻开关

- **WHEN** 客户选择一个明确归属且平台为 Facebook 的环境
- **THEN** 客户端在慢启动开关附近显示规则模式开关
- **AND** 说明明确慢启动开启时由慢启动优先、规则模式暂停

#### Scenario: 其它平台不显示规则模式

- **WHEN** 客户选择小红书、视频号、未知平台或非归属环境
- **THEN** 客户端不显示可操作的 Facebook 规则模式开关

### Requirement: 客户端规则模式读写保持 Cloud 环境作用域权威

客户规则模式接口 SHALL 只接受当前客户 `envKey`，由 Cloud 复核环境归属、解析唯一持久账号绑定并校验 Facebook 平台后，读取或写入既有账号级规则模式配置。写请求 MUST 只接受布尔 `enabled`，客户端 MUST NOT 提交或选择 `accountId`、规则定义、运行进度、HTTP 目标或授权模式。环境内核停止 MUST NOT 单独阻止该纯 Cloud 配置读写。

#### Scenario: 已绑定 Facebook 环境读取配置

- **WHEN** 已登录客户读取自己一个已唯一绑定账号的 Facebook 环境规则模式
- **THEN** Cloud 返回同一 `envKey` 与该账号现有规则模式配置的最小客户投影
- **AND** 响应不泄露 `accountId` 或内部更新者

#### Scenario: 已绑定 Facebook 环境写入配置

- **WHEN** 已登录客户为自己一个已唯一绑定账号的 Facebook 环境提交唯一字段 `{ enabled: boolean }`
- **THEN** Cloud 使用现有账号级规则模式存储写入配置并返回写后权威投影
- **AND** Edge 不创建任何本地规则配置或运行授权

#### Scenario: 停止的环境仍可更改 Cloud 配置

- **WHEN** 客户拥有的 Facebook 环境内核已停止但持久账号绑定仍唯一有效
- **THEN** 规则模式读写仍可通过 customer-auth 完成
- **AND** 系统不要求启动浏览器或 Edge 会话来证明这次 Cloud 配置写入

#### Scenario: 非法范围和平台失败关闭

- **WHEN** 环境不归属当前客户、绑定未知、绑定冲突、绑定服务不可用、账号平台不是 Facebook或请求包含 `enabled` 之外的字段
- **THEN** Cloud 返回可区分的拒绝或不可用结果
- **AND** 不修改任何账号规则配置

### Requirement: 客户端使用非乐观权威回读呈现

客户端 SHALL 按 `envKey` 隔离规则模式读取和写入状态。未读取、读取中、接口不可用或响应不完整时 MUST 呈现未知且禁用，MUST NOT 默认为关闭。写入中 SHALL 禁用控件并标记等待 Cloud 确认；只有包含同一环境完整权威配置的成功回执才能收敛为新值。失败或晚到的其它环境回执 MUST NOT 改写当前环境显示。

#### Scenario: 未知不冒充关闭

- **WHEN** customer-auth 未返回完整规则模式配置或读取失败
- **THEN** 客户端将开关显示为未知且不可操作
- **AND** 不把 checkbox 未选中解释为 Cloud 已关闭规则模式

#### Scenario: 写入等待权威确认

- **WHEN** 运营员切换规则模式且 Cloud 写请求尚未完成
- **THEN** 客户端显示正在开启或关闭并禁用重复提交
- **AND** 不提前宣称配置已生效

#### Scenario: 写失败恢复原真态

- **WHEN** Cloud 拒绝或未完整确认规则模式写入
- **THEN** 客户端恢复最近一次同环境 Cloud 真态并显示失败原因
- **AND** 不保留乐观 checked 状态

#### Scenario: 环境切换隔离晚到回执

- **WHEN** 环境 A 的规则模式请求尚未完成时客户切换到环境 B
- **THEN** 环境 A 的回执只更新 A 的缓存
- **AND** 不改变环境 B 的开关和反馈

### Requirement: 客户端开关不得改变规则模式仲裁

客户端规则模式开关 SHALL 只修改既有 Cloud 配置的 `enabled` 字段。Cloud 仍 MUST 在会话装配时应用既有平台、绑定人设、活跃时段、慢启动、风险和单飞仲裁；慢启动为 active 时规则模式 MUST 保持暂停且不累计进度。Edge MUST NOT 根据本地 checkbox 自行选择模式、累计任何级别的规则节奏计数，或触发点赞、加群和评论。两级节奏的阈值与周期一律由 Cloud 的权威规则定义决定，Edge MUST NOT 内置或推断任何节奏数字。

#### Scenario: 慢启动继续优先

- **WHEN** 规则模式配置已开启且同一环境慢启动为 active
- **THEN** Cloud 继续选择慢启动而不是规则模式
- **AND** 客户端开关不绕过或覆盖该仲裁

#### Scenario: 客户端不内置节奏数字

- **WHEN** Cloud 的权威规则定义发生节奏变更
- **THEN** 客户端无需发版即可继续正确工作
- **AND** 客户端 MUST NOT 依据本地写死的浏览条数或点赞轮次自行触发任何动作

