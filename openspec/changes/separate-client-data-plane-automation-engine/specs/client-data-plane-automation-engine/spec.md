## ADDED Requirements

### Requirement: 桌面客户端数据面 MUST 独立于自动化引擎生命周期

客户会话有效时，Electron 应用 SHALL 作为客户端直接提供本地与 Cloud 数据管理能力；普通自动化引擎停止、暂停、启动失败、WebSocket 离线、浏览器关闭、CDP 缺席或浏览器槽位为零 MUST NOT 把客户端投影为离线，也 MUST NOT 阻塞已登记的 `local` 或 `cloud_data` 操作。

#### Scenario: 引擎停止时管理人设和草稿

- **WHEN** 客户已登录且拥有可信绑定环境，但该环境自动化引擎未启动、浏览器关闭
- **THEN** 客户端仍可读取/保存人设、编辑待审稿和提交审批决定，且不得提示连接引擎或打开浏览器

#### Scenario: 自动化 WebSocket 断线不阻塞 HTTP

- **WHEN** 自动化引擎连接处于断开或重连，而 customer-auth HTTP 可达
- **THEN** `cloud_data` 操作按 HTTP 结果正常完成，界面不得用引擎断线覆盖该请求成功

### Requirement: Cloud 自有数据操作 MUST 使用逐请求 HTTP

读取或修改 AIDCP 自有数据的客户操作 SHALL 通过 Electron main 的窄 customer-auth HTTP 适配器执行。Cloud MUST 对每次请求重新校验客户、环境归属和权威账号绑定；renderer MUST NOT 获得令牌、权威账号 ID 或通用 HTTP 能力。HTTP 请求状态 SHALL 属于具体操作，不得建立全局 `cloudState` 长连接准入。

Cloud、管理后台或编排器 MUST NOT 通过环境 automation WebSocket 向客户端推送人设、配置、稿件、审批、环境管理或其他 `cloud_data` 命令。只有由已启用自动化引擎执行的 `automation_control`、`platform_api_automation`、`browser_lifecycle` 或 `page_automation` 操作 MAY 进入该推送通道。未来若需要数据实时性，独立用户级通知通道 MAY 发送“数据已变化、请重新拉取”的失效提示，但 MUST NOT 携带非自动化业务写命令，也 MUST NOT 以自动化引擎在线作为通知或数据读取准入。

#### Scenario: 单次写失败不伪装客户端离线或保存成功

- **WHEN** 客户保存配置时 HTTP 超时
- **THEN** 客户端回滚该次未确认写并显示真实失败原因，不得显示“已保存”，也不得把自动化引擎标记为离线

#### Scenario: 越权环境逐请求拒绝

- **WHEN** 客户对不归属自己的 `envKey` 发起数据管理请求
- **THEN** Cloud fail-closed 拒绝且不泄漏绑定账号，客户端不得通过启动引擎或浏览器绕过

#### Scenario: 管理后台不能推送非自动化命令

- **WHEN** 管理后台修改某客户环境的配置、人设或稿件数据
- **THEN** Cloud 持久化权威数据，客户端在后续 HTTP 拉取或显式刷新时取得新值；Cloud MUST NOT 经 per-environment automation WebSocket 下发“应用配置/写入数据”命令

#### Scenario: 数据变更通知只触发重新拉取

- **WHEN** 未来独立用户级通知通道告知客户端某项 Cloud 数据已变化
- **THEN** 客户端按自身客户会话重新发起窄 HTTP 读取；通知载荷不得直接执行数据写入、启动自动化引擎或打开浏览器

#### Scenario: 客户端首页数据始终通过 HTTP 读取

- **WHEN** 客户端展示所选环境的今日进展、配额节奏和最近发布摘要，无论该环境自动化引擎为 stopped、paused、connected 或 running
- **THEN** Electron main SHALL 通过具名 customer-auth HTTP 请求逐次读取权威概览；automation WebSocket MUST NOT 直接提供或覆盖这些数据

#### Scenario: 自动化结果只触发概览重拉

- **WHEN** 已连接引擎回报浏览、互动或发布执行结果
- **THEN** 客户端 MAY 立即失效该环境概览缓存并重新发起 HTTP 读取，但 MUST NOT 把引擎事件中的本地增量直接冒充 Cloud 已确认计数或发布历史

#### Scenario: 概览读取失败不制造真实零值

- **WHEN** HTTP 概览读取失败或仍在首次加载
- **THEN** 客户端 SHALL 保留并标记上次成功快照及其时间，或显示获取中/暂时无法获取；MUST NOT 用默认 `0` 冒充 Cloud 已确认的今日数据

#### Scenario: 新能力客户端不接收用量数据推送

- **WHEN** Cloud 向支持 `client_data_plane_automation_engine_v1` 的自动化引擎发送 UI 控制投影
- **THEN** 载荷 MAY 保留 `browserStandby` 等自动化控制提示，但 MUST NOT 包含 `dailyUsage`、最近发布或发布历史；旧客户端 MAY 在兼容窗口继续接收旧快照

#### Scenario: 待审摘要保持 HTTP 审批入口可达

- **GIVEN** 新能力客户端的环境 overview 返回当前发布为 `pending` 或 `reminded`，且自动化 WebSocket 没有内联 `publishPreview`
- **WHEN** 客户端渲染发布卡
- **THEN** 发布卡 SHALL 显示可操作的“查看稿件”入口，而不是只显示“等你确认”却无审批路径
- **AND** 用户打开入口后，Electron main SHALL 通过该环境的具名 customer-auth HTTP 待审列表与详情请求拉取完整稿件
- **AND** renderer MUST NOT 获得令牌、`accountId` 或通用 URL，Cloud/Edge MUST NOT 为恢复该入口重新经 automation WebSocket 推送完整稿件

### Requirement: 自动化引擎连接 MUST 只表示自动化可用性

普通 Edge 子进程 SHALL 作为按需自动化引擎，仅在用户启动或恢复自动化后建立 automation WebSocket。连接成功 SHALL 投影为自动化 `ready`，只有实际任务执行期间才 SHALL 投影为 `running`。登录和 roster 刷新 MUST NOT 自动启动普通引擎。

#### Scenario: 登录后不自动启动引擎

- **WHEN** 客户登录并取得多个可信环境
- **THEN** 客户端显示这些环境可管理但自动化 `stopped`，不得 spawn 普通引擎、建立每环境 automation WebSocket 或启动浏览器

#### Scenario: 引擎连接后等待任务

- **WHEN** 用户启动自动化且引擎握手成功，但当前没有任务
- **THEN** 自动化显示 `ready`/“等待任务”，MUST NOT 显示“正在执行”

### Requirement: 外部平台自动化 MUST 按执行器分类

自动读取或修改外部平台的操作 SHALL 属于 `platform_api_automation` 或 `page_automation` 并要求自动化引擎在线。`platform_api_automation` MUST NOT 取得浏览器槽位、CDP 或页面任务租约；`page_automation` MUST 保留浏览器槽位、真实页面身份复核和任务租约准入。需要人工重新授权时 SHALL 显式转入 `browser_lifecycle`。

#### Scenario: API-only 同步需要引擎但不需要浏览器

- **WHEN** 自动化已启用且视频号使用有效本地 API 会话同步互动
- **THEN** 操作经引擎执行但浏览器保持关闭，不进入槽位队列或取得页面租约

#### Scenario: 自动化暂停时不继续 API-only 外部写

- **WHEN** 用户暂停自动化并断开普通引擎
- **THEN** 系统不得继续新的 API-only 自动回复或外部平台写；客户端 Cloud 数据管理仍可使用

### Requirement: 自动化主操作 MUST 管理引擎并自动准备浏览器

客户端 SHALL 提供启动、暂停、恢复和关闭自动化。启动/恢复 SHALL 自动建立引擎并确保浏览器执行器可用；暂停 SHALL 先有界停止/回报任务再断开普通引擎且不影响客户端数据面；关闭 SHALL 停止引擎并关闭浏览器、释放槽位。用户 MUST NOT 为正常启动/恢复先执行独立“打开浏览器”。

#### Scenario: 恢复时浏览器已被回收

- **WHEN** 自动化处于 `paused` 且浏览器已因空闲回收关闭，用户点击恢复
- **THEN** 客户端自动申请槽位、打开浏览器、复核页面身份并重连引擎，无需额外点击浏览器按钮

#### Scenario: 暂停不影响数据管理

- **WHEN** 用户暂停正在等待任务的自动化
- **THEN** 引擎停止接收任务并断开，当前实现释放浏览器/CDP/槽位，HTTP 人设/草稿/配置操作继续可用；未来只有具备独立、可观测的 shell-owned 租约时才 MAY 保留热浏览器

#### Scenario: 关闭释放全部自动化资源

- **WHEN** 用户关闭自动化
- **THEN** 引擎、CDP、provider、页面租约与浏览器槽位均被有界释放，而客户端保持登录和可管理

### Requirement: 客户端 UI MUST 使用自动化主状态而非核心和 Cloud 长连接状态

新能力客户端 SHALL 公开客户会话、自动化状态及必要的浏览器阻塞信息；MUST NOT 把 `coreState` 或 `cloudState` 作为一级用户状态。引擎传输 MAY 在开发者详情显示为 `engineLinkState`，但 MUST NOT 作为 `cloud_data` 入口准入。

#### Scenario: 自动化停止时环境仍可管理

- **WHEN** 客户会话为 `ready`、自动化为 `stopped` 且浏览器为 `closed`
- **THEN** 环境行状态短标签显示“已就绪”、自动化明细显示“未启动”，而非“客户端离线”，数据管理入口保持可用

#### Scenario: 等待槽位显示真实阶段

- **WHEN** 用户启动自动化但所有浏览器槽位已占用
- **THEN** 自动化显示 `waiting_resource`/“等待浏览器资源”，MUST NOT 显示 `running`、Cloud 离线或客户端核心异常
