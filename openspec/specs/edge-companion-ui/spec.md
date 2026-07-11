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

### Requirement: 发布卡「上次发布」历史态按环境归属、跨环境不串显
主进程 SHALL 为「上次发布」历史态记录环境归属键（自起浏览器为固定键，指纹浏览器为环境 id 派生键），归属键在核心进程 spawn 时刻快照、随历史态一并持久化。当历史态的归属键与当前生效环境不一致、或持久化数据缺失归属键时，界面 MUST NOT 展示该历史态，发布卡 MUST 回落「还没有发布过内容」空态占位（宁缺毋假：归属不明的内容不得挂在当前账号名下）。云端快照带回当前账号的真实发布记录时 SHALL 照常覆盖本地历史态；同环境重启 SHALL 保留历史态（现状不变）。

#### Scenario: 切换到无发布记录的环境后回落空态
- **WHEN** 用户切换浏览器环境并按新设置重启核心，且新环境对应账号在云端无已发布记录
- **THEN** 发布卡随核心启动清掉上一环境的「上次发布」内容、显示空态占位，MUST NOT 继续显示上一账号的发布标题

#### Scenario: 切换到有发布记录的环境后由云端快照回填
- **WHEN** 切换环境重启核心后，云端 hello 快照带回新账号的最近发布记录
- **THEN** 发布卡从空态回填为新账号的「上次发布」，并以新环境键落盘持久化

#### Scenario: 同环境重启历史态保留
- **WHEN** 未更换环境，核心因保存设置 / 恢复 / 重新登录而重启
- **THEN** 「上次发布」历史态保留展示，行为与改动前逐位一致

#### Scenario: 旧版持久化文件缺归属键时不采纳
- **WHEN** 应用升级后首次启动，读到不含归属键的旧版 ui-state 持久化文件
- **THEN** 不采纳其中的历史态、发布卡显示空态占位；待核心启动、云端快照带回真实记录后自愈，首次新写入即带归属键

#### Scenario: 已保存新环境但未重启期间的发布归属旧环境
- **WHEN** 用户保存了新环境设置但尚未重启核心，仍在运行的旧核心此时发布成功
- **THEN** 该「上次发布」记录的归属键 MUST 为旧核心 spawn 时刻的环境键，下次以新环境启动核心时该记录被清出展示

### Requirement: 陪伴视图在多环境下作用于选中环境且按环境隔离不串号

多环境模式下，陪伴主视图（标题带账号身份、五路健康结论、叙述式活动流、今日计数、发布卡、今日用量 + 分时段限额、在场感）SHALL 作用于「当前选中环境」，其全部投影 SHALL 按 envId 隔离——某环境的活动流、计数、发布卡、健康结论、限额分时段窗口 MUST NOT 混入或误显示为另一个环境的数据。陪伴视图自身的内容与交互相对单账号版本 SHALL 保持不变（本需求只约束「作用对象 = 选中环境 + 按环境隔离」，不改既有单账号视图的任何行为）。切换选中环境 SHALL 使整块陪伴视图切换到该环境的投影。

#### Scenario: 切换环境后陪伴视图整体切换且不串号
- **WHEN** 运维从环境 A 切换到环境 B
- **THEN** 标题带身份、活动流、计数、发布卡、健康结论、限额分时段窗口全部切换为环境 B 的投影，MUST NOT 残留环境 A 的任何数据

#### Scenario: 并发环境的投影互不混入
- **WHEN** 多个环境同时在跑并产生各自的活动 / 计数 / 发布 / 限额变化
- **THEN** 当前选中环境的陪伴视图只呈现该环境的数据，其他环境的数据 MUST NOT 混入当前视图

### Requirement: 客户端暂停保留浏览器并提供显式关闭状态

Electron 客户端 SHALL 将临时暂停与最终关闭区分为不同的本地生命周期：暂停 MUST 停止该环境的自动运营、后台监测和云端参与，但 MUST 保持该环境已打开且由客户端拥有的浏览器；关闭 MUST 停止自动运营并关闭、确认回收该环境拥有的浏览器。客户端 SHALL 以独立的 `paused` 与 `closed` 状态如实呈现结果，MUST NOT 在暂停时暗中关闭浏览器或在浏览器未确认关闭时提前显示“已关闭”。

#### Scenario: 运行环境点击暂停后浏览器保持打开
- **WHEN** 用户对正在运行的环境点击“暂停”
- **THEN** 该环境停止自动运营、监测和云端参与并显示“已暂停”
- **AND** 该环境的浏览器窗口及登录上下文保持打开

#### Scenario: 暂停环境提供恢复与关闭两个明确动作
- **WHEN** 环境处于已暂停状态
- **THEN** 客户端同时提供“恢复”和“关闭”动作
- **AND** 点击“恢复”复用已打开浏览器恢复自动运营，MUST NOT 再打开第二个同 profile 浏览器

#### Scenario: 点击关闭后才关闭浏览器并进入已关闭
- **WHEN** 用户对已暂停环境点击“关闭”
- **THEN** 客户端关闭并确认回收该环境拥有的浏览器
- **AND** 仅在最终关闭完成后显示“已关闭”，主动作切换为“启动”

#### Scenario: 生命周期操作按环境隔离
- **WHEN** 用户暂停、恢复或关闭多环境列表中的某一个环境
- **THEN** 操作和状态更新只作用于目标 envId
- **AND** 其他环境的自动运营、浏览器和状态不受影响

#### Scenario: 应用退出仍关闭暂停中的浏览器
- **WHEN** 应用退出或暂停环境被移出运行花名册
- **THEN** 客户端把该意图视为最终关闭并回收其拥有的浏览器
- **AND** MUST NOT 因环境此前处于暂停态而遗留孤儿浏览器

#### Scenario: 暂停控制消息失败时不伪装成功
- **WHEN** 客户端无法把暂停请求交付给目标核心进程
- **THEN** 客户端如实显示暂停失败并保留原运行状态
- **AND** MUST NOT 回落到会关闭浏览器的终止信号后仍宣称“已暂停”

### Requirement: Electron and controlled browser prompt when an account lacks persona
The Electron companion SHALL actively surface persona setup when an environment is logged in, connected to cloud, and the bound account has no persona. It MUST open the account persona dialog and emit a desktop notification once per unresolved environment/account condition. It SHALL also show an AIDCP-owned reminder inside that environment's controlled browser page, including when the environment is not selected in Electron. It MUST remove the controlled-page reminder once the account is persona-bound or no longer ready, MUST NOT repeatedly reopen the Electron dialog on every status tick, and MUST keep browser-page reminder state isolated by environment.

The companion MUST NOT treat a just-connected environment as unbound during a bounded grace window after it first becomes logged-in + cloud-connected. Because the authoritative persona-bound signal is sent sticky-true (only when bound) on a cloud tick after the initial connect, a transient "not yet bound" reading is not authoritative. Within the grace window the companion MUST NOT auto-open the persona dialog, emit a notification, or push the controlled-page reminder. It MUST prompt only after the grace elapses with the account still unbound, and MUST guarantee (via a re-evaluation) that a still-unbound account is eventually prompted even without further status pushes. An account whose persona-bound signal (or successful local persona persistence) arrives within the grace MUST never be prompted. The grace applies to both the Electron dialog/notification and the controlled-page reminder.

#### Scenario: Unbound logged-in account opens persona prompts after the grace
- **WHEN** an environment reports `auth='logged in'`, `cloud='connected'`, and no `personaBound`, and the grace window has elapsed with the account still unbound
- **THEN** Electron opens the account persona dialog for that environment and sends one desktop notification
- **AND** the same environment's controlled browser page shows a reminder to complete persona setup in AIDCP Edge

#### Scenario: Already-bound account is not prompted during the pre-personaBound window
- **WHEN** an environment becomes logged-in + cloud-connected and its authoritative `personaBound=true` signal arrives within the grace window
- **THEN** Electron never auto-opens the persona dialog, never emits a notification, and never pushes the controlled-page reminder for that environment
- **AND** the environment is shown as persona-set

#### Scenario: No prompt within the grace window
- **WHEN** an environment has just become logged-in + cloud-connected and its persona-bound state is not yet known, still within the grace window
- **THEN** Electron does not auto-open the persona dialog, does not emit a notification, and does not push the controlled-page reminder

#### Scenario: Background environment receives its own browser reminder
- **WHEN** an unresolved environment reports missing persona (past its grace) while another environment is selected in Electron
- **THEN** the unresolved environment's own browser page shows the reminder
- **AND** the selected environment's browser page does not receive that reminder

#### Scenario: Status ticks do not spam Electron prompts
- **WHEN** the same unresolved environment/account continues to report unbound persona across repeated status updates
- **THEN** Electron keeps at most one active dialog prompt and desktop notification for that unresolved condition

#### Scenario: Bound account removes all unresolved reminders
- **WHEN** the environment reports `personaBound=true` or persona persistence succeeds locally
- **THEN** Electron clears the unresolved prompt state
- **AND** the edge child removes the AIDCP reminder from the controlled browser page

#### Scenario: Browser navigation preserves unresolved reminder
- **WHEN** the controlled page navigates or its CDP connection recovers while the account remains unresolved
- **THEN** the edge child reapplies the reminder to the current top-level document without requiring another cloud state transition

### Requirement: Controlled-page persona reminder is isolated and non-authoritative
The controlled-page persona reminder SHALL be rendered in a namespaced Shadow DOM host owned by AIDCP. It SHALL contain only reminder copy and a dismiss control, MUST NOT expose the full persona form, MUST NOT mutate site-owned nodes, and MUST NOT claim that dismissing the reminder binds or authorizes a persona.

#### Scenario: Site DOM remains untouched
- **WHEN** the edge child shows the controlled-page reminder
- **THEN** it appends or updates only the AIDCP namespaced host and its shadow tree
- **AND** site-owned DOM nodes and classes remain unchanged

#### Scenario: Operator dismisses browser reminder
- **WHEN** the operator dismisses the controlled-page reminder
- **THEN** the current reminder host is removed from the page
- **AND** the account remains unresolved until persona persistence succeeds in Electron

### Requirement: Persona wizard uses tone and content-preference panels
The Electron persona wizard SHALL present exactly two operator-facing selection panels before generation: `语气调性` first, followed by `内容偏好`. `内容偏好` SHALL group second-level interests under category titles, using the category title as the section title and interest buttons as selectable options.

#### Scenario: Tone panel appears first
- **WHEN** the persona wizard is visible for an unbound ready account
- **THEN** the first selection panel is titled `语气调性`
- **AND** the content-preference panel appears below it

#### Scenario: Recruitment category is first
- **WHEN** the content-preference panel renders
- **THEN** the first category is `招聘求职`
- **AND** it includes `骑手外卖`, `蓝领零工`, `数据标注`, `自有兼职`, and `在校实习`

### Requirement: Content-preference groups allow custom interests
Each content-preference group SHALL expose a `+` custom action. A valid custom interest MUST appear as a selected option in that group, MUST participate in `persona.generate`, and MUST remain bounded by client and cloud persona keyword limits.

#### Scenario: Add custom interest to a category
- **WHEN** the operator clicks `+` beside a content-preference group and enters a valid custom interest
- **THEN** the custom interest appears selected in that group
- **AND** persona generation includes the category title and custom interest in `keywordSelections`

#### Scenario: Empty custom interest is ignored
- **WHEN** the operator submits an empty or whitespace-only custom interest
- **THEN** no custom option is added and existing selections remain unchanged

### Requirement: Browser permission prompts are handled honestly
The Electron shell SHALL deny browser permission requests in the app window unless explicitly allowed by a narrow allowlist. Sensitive or unknown permissions SHALL fail closed and the client SHALL surface a throttled desktop notification explaining the denial. It MUST NOT report the page as successfully authorized.

#### Scenario: Geolocation request is denied and surfaced
- **WHEN** an Electron-loaded page requests geolocation permission
- **THEN** the app denies the request
- **AND** the operator receives a notification explaining that the permission was blocked

#### Scenario: Unknown permission fails closed
- **WHEN** an Electron-loaded page requests an unrecognized permission that is not explicitly allowed
- **THEN** the app denies the request rather than granting it silently

### Requirement: Driven browser windows default to primary-screen parking with reliable placement
The Electron companion SHALL offer a `primary-screen` parking mode and SHALL make it the default. In this mode the driven browser window MUST be placed fully within the primary display's work area (a right-aligned background slot at full render size), a position the operating system honors, so the window neither tucks off-screen unexpectedly nor is clamped back into an unintended position. Parking MUST keep the browser rendering (no minimize/headless) and MUST NOT steal focus. The prior `edge-strip`, `offscreen`, and `parking-display` modes SHALL remain selectable. When a mode's requested bounds fail the post-placement visibility check, the fallback MUST target a reliably-visible on-primary position rather than an off-screen strip. A failure to apply parking at startup MUST NOT disable the per-environment show / re-park control channel.

#### Scenario: Primary-screen is the default and stays on the primary display
- **WHEN** settings do not specify a parking mode, or specify `primary-screen`
- **THEN** the driven window is placed fully within the primary display's work area at full render size
- **AND** the window keeps rendering and does not take focus

#### Scenario: Parking-display without a secondary display falls back to the default
- **WHEN** `parking-display` is selected but no secondary display is available
- **THEN** the window is parked using the default (`primary-screen`) placement
- **AND** the effective mode and the applied bounds are consistent with each other

#### Scenario: Parking-apply failure does not disable control
- **WHEN** applying parking at startup throws (e.g. the visibility check fails for both the primary and fallback bounds)
- **THEN** the environment still installs its stdin control listener
- **AND** the show / re-park commands remain available for that environment

### Requirement: Environment rail avatar cycles select, show-on-primary, and re-park
Clicking an environment's rail entry SHALL act as a three-state control for that environment. The first click (on a not-yet-selected environment) selects it and highlights it with a distinct color. On the already-selected environment, the next click raises that environment's driven browser to the primary screen and focuses it; the following click sends the browser back to its parked slot; further clicks continue to toggle between raised and parked. The selected-environment highlight MUST be visually distinct, and the raised state MUST be visually distinguishable from the merely-selected state. The show and re-park actions MUST reuse the existing per-environment control channel and MUST honestly surface failure; a failed action (for example, the browser is not yet ready) MUST NOT advance the toggle phase. Switching to a different environment MUST reset the toggle phase. The persona icon on a rail entry MUST NOT trigger this toggle.

#### Scenario: First click selects with a distinct highlight
- **WHEN** the operator clicks a rail entry that is not currently selected
- **THEN** that environment becomes selected and is highlighted with the distinct selected color
- **AND** no browser show / re-park command is sent

#### Scenario: Second click raises the browser to the primary screen
- **WHEN** the operator clicks the already-selected environment's rail entry and its browser is parked
- **THEN** the companion requests that environment's browser be moved to the primary screen and focused
- **AND** the rail entry reflects the raised state

#### Scenario: Third click re-parks the browser
- **WHEN** the operator clicks the already-selected environment's rail entry while its browser is raised
- **THEN** the companion requests that environment's browser return to its parked slot
- **AND** the raised state is cleared

#### Scenario: Honest failure does not advance the toggle
- **WHEN** a show or re-park request fails because the environment's browser is not running/ready
- **THEN** the companion surfaces the failure
- **AND** the toggle phase does not advance

### Requirement: Companion window permits its own notifications while denying device access
The Electron companion window permission policy SHALL allow the client's own notifications so operator-facing status can be surfaced, while continuing to deny device-access permissions (geolocation, camera, microphone, and similar) that the local companion UI does not need. This policy governs only the companion window and is independent of the driven fingerprint browser's permission handling.

#### Scenario: Notifications are allowed in the companion window
- **WHEN** the companion window's web content requests notification permission
- **THEN** the request is granted so client status notifications continue to work

#### Scenario: Device-access permissions stay denied in the companion window
- **WHEN** the companion window receives a geolocation, camera, or microphone permission request
- **THEN** the request is denied, matching the existing device-access policy

#### Scenario: Companion policy does not govern the driven browser
- **WHEN** the driven fingerprint browser surfaces a permission request
- **THEN** it is handled by the driven browser's own permission suppression, not by the companion window policy

### Requirement: 用户发起的关闭须以确认的浏览器真死为准

伴随窗提供的会话控制中，暂停 SHALL 保持被驱动浏览器打开（不关闭），关闭 SHALL 只在**被拥有的浏览器已确认真正关闭**后才向操作者呈现「已关闭」。伴随窗 MUST NOT 仅凭核心进程退出即宣称浏览器已关闭——SHALL 反映核心诚实的「已确认关闭 / 未确认关闭」结论：核心确认关闭时呈现「已关闭」，核心报告未确认时保持暂停并如实提示「关闭状态未能确认」，MUST NOT 把未确认掩成成功。当关闭被发起而当前没有在跑的核心子进程（如驻留核心在暂停与关闭之间已死、浏览器却因被外部运行时托管而仍存活）时，伴随窗 MUST NOT 零回收动作直接宣称已关闭：SHALL 对本进程自有 profile 补一次停止 + 本机在跑分身实证后再判定，或如实报告「无法确认已关」。

#### Scenario: 暂停保持浏览器打开
- **WHEN** 操作者对一个运行中的环境点击暂停
- **THEN** 自动运营停止但被驱动浏览器保持打开，会话呈现「已暂停」，并提供关闭 / 恢复入口

#### Scenario: 确认关闭后才呈现已关闭
- **WHEN** 操作者点击关闭且核心确认被拥有的浏览器已真正关闭
- **THEN** 伴随窗呈现「已关闭」

#### Scenario: 未确认关闭则保持暂停并诚实提示
- **WHEN** 操作者点击关闭但核心报告浏览器关闭状态未能确认
- **THEN** 伴随窗保持「已暂停」并展示「关闭状态未能确认、可重试关闭」的诚实提示，MUST NOT 呈现「已关闭」

#### Scenario: 无核心子进程时不得零回收假报已关
- **WHEN** 关闭被发起时当前没有在跑的核心子进程，而该 profile 的浏览器可能仍被外部运行时托管着存活
- **THEN** 伴随窗 SHALL 先对本进程自有 profile 补一次停止 + 本机在跑分身实证，仅在确认已关时才呈现「已关闭」，否则如实报告「无法确认已关」，MUST NOT 零回收直接宣称已关闭

### Requirement: 同账号并发占用终局以可识别的「环境被其它端占用」呈现

当边缘进程因「该分身已被同一账号在别处打开、不允许并发打开」而终止时，伴随窗 SHALL 把失败详情呈现为**可识别的「环境被其它端占用」原因**（在可从拒启信息解析到占用账号时并列出该账号），并提示操作者在占用它的一端关闭后再启动。伴随窗 MUST NOT 只呈现生技术拒启行，也 MUST NOT 呈现「稍后自动重启」这类与「已停止、不再重试」相矛盾的倒计时文案。该原因 MUST 源自真实拒启信息，MUST NOT 编造成功或掩盖底层失败原因。

#### Scenario: 呈现「环境被其它端占用」而非通用 / 生技术文案
- **WHEN** 边缘进程因同账号并发占用被拒而终止
- **THEN** 伴随窗展示「环境被其它设备或窗口占用（可含占用账号）；请在占用它的一端关闭后再启动」的可操作详情，MUST NOT 展示「稍后自动重启」倒计时或仅生技术拒启行

#### Scenario: 原因源自真实拒启信息
- **WHEN** 呈现该终局详情
- **THEN** 详情内容源自真实的提供商拒启信息（分类 / 本地化后），MUST NOT 编造或隐藏底层失败

