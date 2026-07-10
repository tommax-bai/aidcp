# edge-companion-ui Specification

## Purpose
TBD - created by archiving change edge-companion-ui. Update Purpose after archive.
## Requirements
### Requirement: 自定义标题栏保留原生窗控且随风控状态染色
Electron 主窗口 MUST 隐藏系统默认标题栏并以「账号身份 + 综合健康」标题带取代，同时 MUST 保留操作系统原生窗口控件（macOS 红绿灯 / Windows 叠加窗控）；MUST NOT 使用 `frame:false` 手绘窗控。标题带 SHALL 按风控状态染色。

#### Scenario: macOS 隐藏标题栏后红绿灯与拖拽可用
- **WHEN** 应用在 macOS 上启动
- **THEN** 系统标题栏不可见、红绿灯按钮内嵌于标题带且可用，标题带区域可拖拽移动窗口，标题带内控件（齿轮 / 药丸）点击不触发拖拽

#### Scenario: Windows 隐藏标题栏后原生窗控可用
- **WHEN** 应用在 Windows 上启动
- **THEN** 最小化 / 最大化 / 关闭为系统原生叠加窗控且全部可用，不出现自绘窗控

#### Scenario: 风控状态变化时标题带随之染色
- **WHEN** 风控状态从 normal 变为 warned（或更差）
- **THEN** 标题带底色相应切换（正常=平静色 / 警戒=琥珀 / 受限与冻结=警示色），状态恢复后染色随之复原

### Requirement: 五路技术状态合成一句健康结论
渲染器 SHALL 将登录 / 云端 / 会话 / 风控 / 边缘进程五路状态合成一句健康结论（「运行中 / 就绪 / 已暂停 / 需要注意」）呈现于标题带药丸；五路明细 SHALL 可点开查看且以非技术用语呈现。

#### Scenario: 任一路异常时结论为需要注意
- **WHEN** 五路状态中任一路处于异常（需登录 / 缺 Chrome / 云端断连且会话运行 / 边缘进程异常 / 风控受限或冻结）
- **THEN** 健康药丸呈现「需要注意」并以警示色标识，点开明细可定位异常的那一路

#### Scenario: 正常运行时结论为运行中
- **WHEN** 边缘进程运行且会话运行、无异常路
- **THEN** 健康药丸呈现「运行中」及平静色，明细五路全部为正常表述

### Requirement: 叙述式活动流取代原始日志作为主信息面
主界面 SHALL 以叙述式活动流为主信息面：每条为一句人话 + 相对时间戳、最新在上、带「刚刚更新 · N 秒前」新鲜度走字；原始日志 SHALL 收进「开发者详情」折叠区。活动流条目 MUST 源自真实核心事件，MUST NOT 编造或美化未发生的动作。

#### Scenario: 核心事件映射为人话条目
- **WHEN** 核心进程产生已映射的动作日志（如点赞成功 / 提取内容 / 评论发布成功）
- **THEN** 活动流顶部新增一条对应的人话句子并带时间戳，今日计数同步递增

#### Scenario: 无新事件时不造条目
- **WHEN** 核心进程一段时间无新日志
- **THEN** 活动流不新增条目，新鲜度戳如实增长（如「1 分钟前」），不出现任何伪造的「仍在活动」条目

#### Scenario: 未识别日志行不进活动流
- **WHEN** 核心进程输出映射表未覆盖的日志行
- **THEN** 该行仅出现在「开发者详情」原始日志中，活动流不展示半截技术行

### Requirement: 在场感动效由真实事件驱动、静默时诚实待命
首屏在场感行（当前动作 + 微光/呼吸动效）MUST 仅在会话运行且最近事件足够新鲜（阈值与看门狗有界 idle 对齐，≈5 分钟内）时开启动效；否则 MUST 切换为静态诚实文案（待命 / 已暂停 / 需登录 / 等待云端），MUST NOT 用动效掩盖停滞会话。

#### Scenario: 运行且有新鲜事件时开启动效
- **WHEN** 会话运行中且 5 分钟内有核心事件
- **THEN** 在场感行展示最近动作句子并带微光动效与呼吸点

#### Scenario: 停止或事件过期时动效止息
- **WHEN** 会话已停止 / 已暂停，或距最近事件超过阈值
- **THEN** 动效停止，在场感行呈现对应静态实情文案，新鲜度戳保持真实

#### Scenario: 尊重系统减少动态偏好
- **WHEN** 操作系统开启 prefers-reduced-motion
- **THEN** 所有微光 / 呼吸动效关闭，信息呈现不受影响

### Requirement: 今日计数降级为小结条
浏览 / 点赞 / 收藏 / 评论计数 SHALL 从首屏门面降级为界面收尾的「今日小结」横条，不再以大号 KPI 磁贴作首屏主视觉。

#### Scenario: 计数照常累计且在小结条呈现
- **WHEN** 会话中发生互动动作
- **THEN** 对应计数在「今日小结」条内递增，首屏主视觉区不出现大号计数磁贴

### Requirement: 发布等待卡纯展示、审批授权只在飞书
发布候审期间界面 SHALL 呈现一张纯展示发布卡：白底、四节点旅程（写好内容 → 发到飞书 → 等你确认 → 择时发布）、当前节点为全卡唯一琥珀呼吸点。端上 MUST NOT 提供任何审批授权控件（无确认 / 驳回按钮）；「打开飞书」为纯导航深链且 MUST 在深链不可用时降级为纯文字。卡片状态 MUST 由真实发布链路事件驱动。

#### Scenario: 候审时呈现旅程卡
- **WHEN** 核心进入发布候审（内容已生成、等待飞书审批）
- **THEN** 发布卡出现：内容标题可见、旅程停在「等你确认」节点（唯一琥珀呼吸点）、脚注说明「通过 / 驳回」在飞书完成、卡上无任何审批按钮

#### Scenario: 等待超时只琥珀化时长、宁缺毋假
- **WHEN** 候审等待超过 30 分钟且端上未收到「已再次提醒」事件
- **THEN** 「已等 N 分钟」转警示色，但 MUST NOT 展示「已在飞书再次提醒」等未经证实的文案

#### Scenario: 审批通过后转入择时发布并明示无需操作
- **WHEN** 收到审批通过事件
- **THEN** 旅程推进到「择时发布」节点（呼吸点转平静色），文案明示「无需操作、系统择时发出」

#### Scenario: 发布落地或被拒时卡片收起折进活动流
- **WHEN** 收到已发布（或审批拒绝）事件
- **THEN** 发布卡收起，活动流新增对应记录（已发布计入今日小结；拒绝表述为「暂不发布、内容留档」而非失败）

#### Scenario: 深链不可用时降级纯文字
- **WHEN** 系统无法经深链拉起飞书客户端
- **THEN** 「打开飞书 ↗」退化为纯文字说明，不呈现死链接、不阻塞其余展示

### Requirement: UI 事件解析结构化优先、字符串兜底且状态形状兼容
主进程 SHALL 经独立可单测模块解析核心输出为带类型 UI 事件：`[ui-event] {json}` 结构化行优先采用，既有中文日志行经映射表兜底；status 对象 MUST 保持既有字段形状向后兼容（新增 presence / publish 字段不删旧字段），既有计数递增行为不变。

#### Scenario: 结构化事件行直接采用
- **WHEN** 核心输出带 `[ui-event]` 前缀的合法 JSON 行
- **THEN** 解析结果直接驱动活动流 / 在场感 / 发布卡，不再走字符串匹配

#### Scenario: 旧日志行兜底映射保持计数行为
- **WHEN** 核心仅输出既有中文日志行（无结构化事件）
- **THEN** 活动流与计数仍按映射表工作，与改版前的计数行为一致

#### Scenario: 渲染器收到旧形状 status 不崩溃
- **WHEN** status 推送缺失新增的 presence / publish 字段
- **THEN** 渲染器按待命态安全降级渲染，不抛错、不白屏

### Requirement: 客户端启动不自动开跑任务
应用启动后 MUST NOT 自动启动自动运营任务；任务 SHALL 由用户经会话控制按钮手动启动。应用启动时 SHALL 做一次轻量预检：配置缺失则呈现待配置引导，配置齐备则如实呈现「就绪」。

#### Scenario: 配置齐备时启动停在就绪态
- **WHEN** 应用启动且浏览器配置齐备
- **THEN** 不拉起引擎、不开始任务，界面呈现「就绪」与启动按钮，等待用户手动启动

#### Scenario: 缺配置时启动亮出引导
- **WHEN** 应用启动且缺少必要配置（如 AdsPower 模式缺分身 ID）
- **THEN** 首屏呈现待配置主动引导（可直达设置抽屉），不尝试启动任务

### Requirement: Electron Daily Summary Uses Account-Scoped Cloud Usage

The Electron companion SHALL prefer cloud-supplied account-scoped daily usage over locally accumulated log counters for the "today" summary when `ui.snapshot.dailyUsage` is available.

#### Scenario: Hello snapshot replaces local counters with account today totals

- **WHEN** cloud sends `ui.snapshot.dailyUsage` for the account bound to the edge
- **THEN** Electron renders the supplied account daily totals for view, like, collect, comment, follow, and publish instead of treating the local process's current-session deltas as authoritative

#### Scenario: Local counters remain a fallback before cloud usage arrives

- **WHEN** Electron has not yet received `ui.snapshot.dailyUsage`
- **THEN** it MAY continue to show local log-derived deltas for available actions, and MUST NOT present quota caps or saturation as if they were authoritative

### Requirement: Electron Daily Summary Shows Current Daily Quota Saturation

The Electron companion SHALL show daily quota context for each supplied action when cloud includes the current quota level's daily caps.

#### Scenario: Action reaches the current level's daily limit

- **WHEN** `ui.snapshot.dailyUsage.saturated` includes an action, or the supplied total is greater than or equal to the supplied cap for that action
- **THEN** Electron marks that metric as saturated and presents it as a limit-reached state distinct from global risk warnings or captcha restrictions

#### Scenario: Quota metadata is missing

- **WHEN** totals are supplied without quotas
- **THEN** Electron renders the account daily totals without fabricating caps, progress, or limit-reached states

### Requirement: Daily Usage Snapshot Remains Backward Compatible

Cloud and edge SHALL keep `ui.snapshot.dailyUsage` optional and backward compatible with older peers.

#### Scenario: Old edge ignores the field

- **WHEN** an older edge receives `ui.snapshot` with unknown daily usage fields
- **THEN** the message remains a valid snapshot and the old edge can ignore the extra field without breaking identity, last publish, or publish-card rendering

### Requirement: Electron Daily Summary Shows Multi-Window Quota Status

The Electron companion SHALL show quota status for each cloud-supplied quota window: current session, minute, hour, and day, while keeping the collapsed daily summary focused on today's account totals.

#### Scenario: Daily card is collapsed by default

- **WHEN** Electron has received account-scoped daily usage with quota windows
- **THEN** the collapsed card renders the day-window totals for view, like, collect, comment, follow, and publish
- **AND** it does not render session, minute, or hour action details until the user expands the card

#### Scenario: User expands the daily card

- **WHEN** the user clicks the daily usage card or its disclosure control
- **THEN** Electron renders quota detail for each supplied window: session, minute, hour, and day
- **AND** each window detail lists view, like, collect, comment, follow, and publish as separate action rows when totals are available
- **AND** each action row shows its supplied total and supplied cap when a cap exists

#### Scenario: Cloud supplies all quota windows

- **WHEN** `ui.snapshot.dailyUsage.windows` includes `session`, `minute`, `hour`, and `day`
- **THEN** Electron renders those windows as peer detail groups in the expanded area
- **AND** it marks saturated actions distinctly from near-limit actions without relying on a single worst-action summary as the only visible data

#### Scenario: Any window reaches its cap

- **WHEN** any supplied window's `saturated` list is non-empty, or any supplied action total is greater than or equal to that window's supplied cap
- **THEN** Electron's aggregate quota status presents a limit-reached state and identifies the saturated window labels
- **AND** the affected action rows are styled as saturated without changing global risk, captcha, or engine health states

#### Scenario: Session quota is not active

- **WHEN** the session window is supplied with `active: false`
- **THEN** Electron MAY show the configured single-session cap as inactive context, but MUST NOT imply that an active session is currently consuming that budget

#### Scenario: Window quota metadata is missing

- **WHEN** a window is missing, or an action total has no supplied cap
- **THEN** Electron MUST NOT fabricate caps, percentages, or limit-reached states for that action or window

#### Scenario: Rolling quota window snapshot expires

- **WHEN** a minute or hour window includes timing metadata and the local clock has passed the supplied expiry time without a fresher cloud snapshot
- **THEN** Electron MUST stop presenting that stale window as saturated
- **AND** it MAY keep rendering the window as waiting for refresh until a new cloud snapshot or local event updates it

### Requirement: Windowed Usage Snapshot Remains Backward Compatible

Cloud and edge SHALL preserve the existing `ui.snapshot.dailyUsage` daily aliases while adding optional windowed quota data.

#### Scenario: New cloud sends windowed usage to an old edge

- **WHEN** cloud includes `ui.snapshot.dailyUsage.windows`
- **THEN** the existing `dailyUsage.totals`, `dailyUsage.quotas`, and `dailyUsage.saturated` fields still describe the day window
- **AND** an older edge can ignore `windows` without losing the existing daily summary behavior

#### Scenario: New edge receives old daily-only usage

- **WHEN** Electron receives `ui.snapshot.dailyUsage` without `windows`
- **THEN** it SHALL continue to render daily totals and daily quota saturation as before
- **AND** it SHALL omit the expanded multi-window detail rather than inventing minute, hour, or session state

#### Scenario: Session window includes uncapped actions

- **WHEN** cloud can determine current-session totals for actions that do not have a single-session cap, such as view or publish
- **THEN** it MAY include those action totals in `windows.session.totals`
- **AND** it MUST omit quotas for uncapped session actions rather than copying caps from another window

#### Scenario: Cloud sends rolling-window timing metadata

- **WHEN** cloud sends minute, hour, or day quota-window status
- **THEN** it SHOULD include `startedAt`, `windowMs`, and `expiresAt` metadata for that window when the values are known
- **AND** older edges can ignore those fields without changing daily alias behavior

### Requirement: Electron Presence Explains Quota Rest State

The Electron companion SHALL distinguish quota-driven waiting from generic stale activity in the presence strip when cloud-supplied quota-window data shows that the current running session has reached an active limit.

#### Scenario: Current quota window is saturated

- **WHEN** Electron is in a running session, the latest presence event is stale, and `ui.snapshot.dailyUsage.windows` shows a current session, minute, hour, or day window with at least one saturated capped action
- **THEN** the presence strip SHALL render a quota-specific rest message naming the action and window
- **AND** it SHALL include the estimated remaining wait until `releaseAt` when that timestamp is available and in the future
- **AND** the presence strip MUST NOT animate as if work is still happening

#### Scenario: Quota evidence is stale or incomplete

- **WHEN** the latest presence event is stale but the relevant quota window is expired, missing, or lacks capped saturated action evidence
- **THEN** Electron SHALL keep the existing stale-activity fallback instead of fabricating a quota-rest explanation

### Requirement: Electron settings expose browser parking modes
The Electron companion SHALL expose a persisted browser parking setting in the settings drawer with exactly three operator-selectable modes: `parking-display`, `edge-strip`, and `offscreen`. The default for missing or invalid settings SHALL be `edge-strip`. The setting SHALL be saved together with the existing browser settings and SHALL be injected into the spawned edge core process when the operator starts or restarts the edge.

#### Scenario: Operator selects a parking mode
- **WHEN** the operator opens the settings drawer and selects one of the three browser parking modes
- **THEN** Electron persists that selected value with the local settings
- **AND** the next start or restart injects that mode into the edge core process

#### Scenario: Existing settings have no parking value
- **WHEN** Electron loads an older settings file without a browser parking mode
- **THEN** it treats the mode as `edge-strip`
- **AND** the settings drawer renders `edge-strip` as selected

#### Scenario: Invalid parking value is ignored
- **WHEN** Electron loads a settings file with an unknown browser parking value
- **THEN** it treats the mode as `edge-strip`
- **AND** it MUST NOT pass the unknown value to the edge core process

### Requirement: Electron provides browser parking recovery controls
The Electron companion SHALL provide an operator recovery path for a parked browser window. It SHALL expose controls to show the driven browser in a normal visible position and to reset future parking coordinates. If no controllable browser window is available, the companion SHALL report that fact honestly and MUST NOT claim recovery succeeded.

#### Scenario: Operator shows parked browser
- **WHEN** the operator clicks the browser recovery control while a driven browser CDP window is available
- **THEN** the browser window is moved to a normal visible position
- **AND** Electron reports the recovery action as applied

#### Scenario: No browser window is available
- **WHEN** the operator clicks the browser recovery control while edge is stopped or no CDP window can be controlled
- **THEN** Electron reports that no controllable browser window is available
- **AND** it MUST NOT claim that the browser was shown or reset

### Requirement: Daily Usage Windows Expose Refresh And Release Timing

Cloud SHALL include optional timing hints on `ui.snapshot.dailyUsage.windows`
when it can compute them without guessing. `refreshAt` SHALL mean the epoch-ms
time when cloud plans or recommends the next usage-window snapshot refresh.
`releaseAt` SHALL mean the epoch-ms time when a saturated quota in that window
is expected to release according to cloud's sliding-window counter. Cloud MUST
omit either field when the value is unknown, non-finite, or not derived from
cloud-owned state.

These fields SHALL be optional and backward compatible. Existing
`dailyUsage.totals`, `dailyUsage.quotas`, `dailyUsage.saturated`, and
`dailyUsage.windows.*.expiresAt` semantics MUST remain unchanged.

#### Scenario: Cloud supplies next refresh time

- **WHEN** cloud sends a daily usage window and knows when it will next refresh that window snapshot
- **THEN** the window MAY include `refreshAt` as a finite epoch-ms timestamp
- **AND** older edges can ignore `refreshAt` without losing existing daily usage rendering

#### Scenario: Cloud supplies quota release time

- **WHEN** a supplied minute, hour, or day window is saturated and cloud can compute the sliding-window release time
- **THEN** the window MAY include `releaseAt` as a finite epoch-ms timestamp
- **AND** that value MUST NOT be derived from local client clocks or aggregate totals alone

#### Scenario: Timing is unknown

- **WHEN** cloud cannot compute refresh or release timing for a supplied window
- **THEN** cloud MUST omit the corresponding timing field
- **AND** clients MUST NOT fabricate a countdown, clock time, or recovery promise for that missing field

### Requirement: Electron Daily Summary Displays Window Timing Honestly

The Electron companion SHALL preserve the existing expanded daily usage window
layout and SHALL display cloud-supplied timing hints when present. If a window
is saturated and `releaseAt` is in the future, Electron SHOULD show the release
hint alongside the capped action context. If a window is stale or awaiting a
new snapshot and `refreshAt` is present, Electron SHALL show the planned refresh
time instead of only the generic `等待云端快照` copy. Electron MUST keep the
current fallback wording when timing is absent.

#### Scenario: Saturated window shows release hint

- **WHEN** Electron renders an expanded quota window with a future `releaseAt`
- **THEN** the window metadata identifies the capped action context and includes a human-readable release hint
- **AND** global risk, captcha, or engine health states are not changed by this display-only hint

#### Scenario: Waiting window shows planned refresh

- **WHEN** Electron renders a minute or hour window as waiting for refresh and the window has `refreshAt`
- **THEN** the metadata includes the planned refresh clock time or countdown
- **AND** if that time has already passed without a newer snapshot, Electron MUST still present the state as waiting rather than marking the quota usable

#### Scenario: Old snapshots still render

- **WHEN** Electron receives `ui.snapshot.dailyUsage.windows` without `refreshAt` or `releaseAt`
- **THEN** it SHALL render the existing window state, totals, quotas, and stale fallback text as before

### Requirement: Cloud Refreshes Online Daily Usage Snapshots Best-Effort

After sending account-scoped daily usage to an online edge, cloud SHALL schedule
a best-effort daily-usage-only `ui.snapshot` refresh for that same account and
edge when a finite future `refreshAt` is available. The scheduled refresh MUST
be targeted to the same edge, MUST NOT broadcast to unrelated edges, and MUST
stop retrying when the edge is no longer online or the targeted push is not
delivered.

#### Scenario: Online edge receives a scheduled usage refresh

- **WHEN** cloud has sent daily usage with a future `refreshAt` to an online edge
- **THEN** cloud SHALL attempt a targeted `ui.snapshot` containing fresh `dailyUsage` at or after that time
- **AND** the refreshed snapshot MAY schedule the next refresh using its new timing metadata

#### Scenario: Offline edge does not cause retry storm

- **WHEN** a scheduled daily usage refresh push reaches no edge
- **THEN** cloud MUST stop that scheduled refresh chain for the account-edge pair
- **AND** it MUST NOT broadcast the snapshot to other edges for the account

### Requirement: 异常退出详情在客户端内持久可见
Electron 伴随窗口 SHALL 在边缘进程异常退出时保留并展示最近一次可操作失败详情，直到用户启动新的边缘进程、执行有意暂停/停止，或新的运行状态覆盖该失败。该详情 MUST 来自真实核心输出、进程退出信息或本地启动失败信息，MUST NOT 编造成功或隐藏底层失败原因。系统通知 MAY 同时发送，但 MUST NOT 成为唯一展示该失败详情的渠道。

#### Scenario: AdsPower 启动被拒后详情仍在窗口可见
- **WHEN** AdsPower 模式下核心输出 `browser/start` 失败原因并以非零 code 退出
- **THEN** 伴随窗口在健康/状态区域展示该失败原因的可读摘要，包括 AdsPower 返回的拒绝信息
- **AND** 该摘要在系统通知关闭后仍保持可见

#### Scenario: 新运行开始后清除旧失败详情
- **WHEN** 用户点击启动、重新登录或按新设置重启边缘进程
- **THEN** 伴随窗口清除上一轮异常退出详情，并显示当前启动/运行状态

#### Scenario: 没有核心错误行时仍显示退出事实
- **WHEN** 边缘进程异常退出但没有可解析的 stderr 错误行
- **THEN** 伴随窗口展示包含退出 code 或 signal 的持久失败详情

