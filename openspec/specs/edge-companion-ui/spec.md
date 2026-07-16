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
渲染器 SHALL 将登录 / 云端 / 会话 / 风控 / 边缘进程五路状态合成一句健康结论（「运行中 / 就绪 / 已暂停 / 需要协助 / 运行异常」）呈现于标题带药丸；五路明细 SHALL 可点开查看且以非技术用语呈现。可恢复且需要用户协助的状态 MUST 使用琥珀色，真正导致运行中断的边缘进程异常或账号冻结 MUST 使用红色，二者 MUST NOT 共用同一红色警示态。

#### Scenario: 登录或配置需要用户协助
- **WHEN** 登录失效、缺少 Chrome、需要初始设置，或运行会话暂时无法连接云端
- **THEN** 健康药丸呈现「需要协助」或明确的恢复进度并使用琥珀色
- **AND** MUST NOT 将该状态呈现为红色系统错误

#### Scenario: 真正运行异常使用红色
- **WHEN** 边缘进程异常停止、自动重启已放弃，或账号处于冻结状态
- **THEN** 健康药丸呈现明确的中断结论并使用红色
- **AND** 点开明细可定位需要处理的异常

#### Scenario: 正常运行时结论为运行中
- **WHEN** 边缘进程运行且会话运行、无异常路
- **THEN** 健康药丸呈现「运行中」及平静色，明细五路全部为正常表述

### Requirement: 叙述式活动流取代原始日志作为主信息面
主界面 SHALL 以叙述式活动流为主信息面：每条为一句人话 + 相对时间戳、最新在上、带「刚刚更新 · N 秒前」新鲜度走字；原始日志 SHALL 收进「开发者详情」折叠区。活动流条目 MUST 源自真实核心事件，MUST NOT 编造或美化未发生的动作。

活动流 SHALL 覆盖**账号在该平台上真实做过的写动作**，MUST NOT 因某类动作由内部委托路径执行而使其对运营不可见。一个动作**做了但不显示**与**没做**在客户端上 MUST 可区分：凡执行器已对该动作作出终局判断（成功 / 待第三方批准 / 结构性失败），活动流 MUST 如实呈现该判断。

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

首屏在场感行（当前动作 + 微光/呼吸动效）MUST 仅在会话运行、且最近事件足够新鲜时开启动效；否则 MUST 切换为静态诚实文案（待命 / 已暂停 / 需登录 / 等待云端），MUST NOT 用动效掩盖停滞会话。

在场感行 SHALL 按「终态优先」取值：当云端下发的当日浏览额度已跑满时，在场感行 MUST 呈现今日完成的终态文案，MUST NOT 被仍在新鲜期内的中途动作文案盖住——该顺序 MUST 与同屏探索进度卡一致，两者 MUST NOT 就同一份数据给出互相矛盾的结论。「今日已完成」的唯一依据是云端当日额度窗口；额度未跑满时客户端 MUST NOT 自行推断并宣称今日已完成。

「最近事件新鲜」SHALL 分段表达，MUST NOT 把「执行端已做完、正在等云端下一步」这一静默态呈现为「此刻正在做」：最近事件在近期阈值（≈1 分钟）内时，在场感行 SHALL 展示动作文案、带动效、新鲜度标签表述为刚刚更新；超过近期阈值但仍在有界 idle 阈值（≈5 分钟，与看门狗对齐）内时，动作文案 SHALL 保留（运营需知道最后推进到哪一步），但动效 MUST 停止、新鲜度标签 MUST 改为如实表述已等待时长。

云端连接断开时，在场感行 MUST 一并改写为连接中断的实情文案，MUST NOT 继续展示断连前的中途动作文案。

#### Scenario: 运行且有新鲜事件时开启动效
- **WHEN** 会话运行中且 1 分钟内有核心事件
- **THEN** 在场感行展示最近动作句子并带微光动效与呼吸点，新鲜度标签表述为刚刚更新

#### Scenario: 停止或事件过期时动效止息
- **WHEN** 会话已停止 / 已暂停，或距最近事件超过有界 idle 阈值
- **THEN** 动效停止，在场感行呈现对应静态实情文案，新鲜度戳保持真实

#### Scenario: 当日浏览额度已满时在场感回落终态
- **WHEN** 会话仍报运行中、最近动作文案仍在新鲜期内，但云端下发的当日浏览额度已跑满
- **THEN** 在场感行展示今日完成的终态文案（而非「顺路去作者主页看看…」这类中途动作文案），并给出预计开启新一天计划的时间
- **AND** 同屏探索进度卡同时呈现今日完成，两者口径一致

#### Scenario: 额度未满时不得自称今日完成
- **WHEN** 云端下发的当日浏览额度尚未跑满
- **THEN** 在场感行 MUST NOT 出现今日已完成的文案，即便执行端长时间无新事件

#### Scenario: 执行端已做完、在等云端下一步
- **WHEN** 会话运行中，最近动作文案距今超过 1 分钟但不足有界 idle 阈值，且当日额度未满
- **THEN** 在场感行保留该动作文案，但动效停止、新鲜度标签如实表述已等待时长，MUST NOT 宣称此刻正在做该动作

#### Scenario: 断连时在场感不再演示中途动作
- **WHEN** 云端连接断开
- **THEN** 在场感行改写为连接中断的实情文案，MUST NOT 继续显示断连前的中途动作文案

#### Scenario: 尊重系统减少动态偏好
- **WHEN** 操作系统开启 prefers-reduced-motion
- **THEN** 所有微光 / 呼吸动效关闭，信息呈现不受影响

### Requirement: 今日计数降级为小结条

浏览 / 点赞 / 收藏 / 评论 / 关注 / 发布计数 SHALL 作为界面收尾的“今日进展”分段面板呈现，不再以互相独立的大号 KPI 卡片作首屏主视觉。六项指标 SHALL 在同一容器中以分隔线成组；汇总标题、数据来源、统计时间与当前环境的启动 / 暂停 / 恢复 / 关闭控制 SHALL 属于同一个摘要上下文。生命周期控制 MUST NOT 以固定悬浮层覆盖活动流。摘要 MUST 使用进展与计划语义，MUST NOT 将正常动作累计描述为受限用量。

#### Scenario: 计数照常累计且在今日进展呈现
- **WHEN** 会话中发生互动动作
- **THEN** 对应计数在“今日进展”分段面板内递增，首屏主视觉区不出现相互独立的大号计数磁贴
- **AND** 汇总标题与展开入口不使用“用量”或“限额”措辞

#### Scenario: 生命周期控制不再遮挡活动记录
- **WHEN** 当前环境处于就绪、运行或暂停状态
- **THEN** 对应的启动、暂停、恢复或关闭操作显示在今日进展标题区
- **AND** 活动流上方或右下角不存在固定悬浮的会话控制层

### Requirement: UI 事件解析结构化优先、字符串兜底且状态形状兼容
主进程 SHALL 经独立可单测模块解析核心输出为带类型 UI 事件：`[ui-event] {json}` 结构化行优先采用，既有中文日志行经映射表兜底；status 对象 MUST 保持既有字段形状向后兼容（新增 presence / publish 字段不删旧字段），既有计数递增行为不变。

中文日志兜底映射表 SHALL 被视为**小红书浏览会话专属**：其规则措辞只由小红书会话与仅小红书生效的启动块打印，Facebook 会话 MUST NOT 依赖该表产出任何活动条目或在场感。Facebook 打印的日志 MUST NOT 误命中该表中语义不符的规则；当某条 Facebook 日志会命中一条描述小红书专属行为的规则（如把「就地读」误述为「顺路去作者主页看看」）时，该 Facebook 日志措辞 MUST 被改到不再命中，MUST NOT 保留一条会对运营说谎的叙述。

#### Scenario: 结构化事件行直接采用
- **WHEN** 核心输出带 `[ui-event]` 前缀的合法 JSON 行
- **THEN** 解析结果直接驱动活动流 / 在场感 / 发布卡，不再走字符串匹配

#### Scenario: 旧日志行兜底映射保持计数行为
- **WHEN** 核心仅输出既有中文日志行（无结构化事件）
- **THEN** 活动流与计数仍按映射表工作，与改版前的计数行为一致

#### Scenario: 渲染器收到旧形状 status 不崩溃
- **WHEN** status 推送缺失新增的 presence / publish 字段
- **THEN** 渲染器按待命态安全降级渲染，不抛错、不白屏

#### Scenario: Facebook confirmed browse actions produce structured desktop events
- **WHEN** a Facebook child has actually started its enabled browse session, successfully reported `note.detail`, or confirmed `action.completed` for a like
- **THEN** it emits a structured UI event that updates the activity stream and presence projection for that child
- **AND** a successful `note.detail` contributes exactly one local view fallback increment and a confirmed like contributes exactly one local like fallback increment
- **AND** shadow, failed, already-liked, or no-target paths MUST NOT produce a success increment

#### Scenario: Facebook read activity identifies the opened content without raw identifiers
- **WHEN** a Facebook `note.detail` has a readable author nickname and post body
- **THEN** its desktop activity and presence text show bounded, whitespace-normalized author and leading-content excerpts
- **AND** when either field is unavailable, the text MUST degrade to an honest generic description and MUST NOT show a permalink or raw note ID

#### Scenario: Facebook 就地读的日志不得被叙述成跳转作者主页
- **WHEN** Facebook 执行 `profile.open` 的就地读（不离开当前页）
- **THEN** 该核心日志 MUST NOT 命中中文兜底表中描述「顺路去作者主页看看」的跳转规则
- **AND** 客户端 MUST NOT 呈现任何声称已跳转作者主页的在场感文案

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
The Electron companion SHALL show daily plan progress for each supplied action when cloud includes the current quota level's daily caps. Reaching a supplied cap SHALL be presented as completing that action's daily plan, distinct from global risk warnings, captcha restrictions, and execution failures.

#### Scenario: Action reaches the current level's daily plan

- **WHEN** `ui.snapshot.dailyUsage.saturated` includes an action, or the supplied total is greater than or equal to the supplied cap for that action
- **THEN** Electron marks that metric as complete with success styling and presents the action's daily plan as completed
- **AND** it MUST NOT use red warning styling or user-facing limit terminology for that normal completion

#### Scenario: Daily plan is still progressing

- **WHEN** authoritative daily totals and caps are supplied but no action is complete
- **THEN** Electron presents the summary as proceeding according to plan
- **AND** near-complete progress remains a calm progress state rather than a warning

#### Scenario: Quota metadata is missing

- **WHEN** totals are supplied without quotas
- **THEN** Electron renders the account daily totals without fabricating caps, progress, or plan-completed states

### Requirement: Daily Usage Snapshot Remains Backward Compatible

Cloud and edge SHALL keep `ui.snapshot.dailyUsage` optional and backward compatible with older peers.

#### Scenario: Old edge ignores the field

- **WHEN** an older edge receives `ui.snapshot` with unknown daily usage fields
- **THEN** the message remains a valid snapshot and the old edge can ignore the extra field without breaking identity, last publish, or publish-card rendering

### Requirement: Electron Daily Summary Shows Multi-Window Quota Status
The Electron companion SHALL show plan progress for each cloud-supplied quota window: current session, minute, hour, and day, while keeping the collapsed daily summary focused on today's account totals. User-facing labels SHALL translate those windows into round, current pace, stage, and daily plan concepts while expanded detail preserves exact supplied totals and caps.

#### Scenario: Daily card is collapsed by default

- **WHEN** Electron has received account-scoped daily usage with quota windows
- **THEN** the collapsed card renders the day-window totals for view, like, collect, comment, follow, and publish
- **AND** it does not render session, minute, or hour action details until the user expands the card

#### Scenario: User expands the daily progress card

- **WHEN** the user clicks the daily progress card or its disclosure control
- **THEN** Electron renders plan detail for each supplied window: current round, current pace, stage, and today
- **AND** each window detail lists view, like, collect, comment, follow, and publish as separate action rows when totals are available
- **AND** each action row shows its supplied total and supplied cap when a cap exists

#### Scenario: Cloud supplies all quota windows

- **WHEN** `ui.snapshot.dailyUsage.windows` includes `session`, `minute`, `hour`, and `day`
- **THEN** Electron renders those windows as peer detail groups in the expanded area
- **AND** it marks completed actions distinctly from near-complete actions without relying on a single worst-action summary as the only visible data

#### Scenario: Any window completes its plan

- **WHEN** any supplied window's `saturated` list is non-empty, or any supplied action total is greater than or equal to that window's supplied cap
- **THEN** Electron's aggregate progress status identifies completed action plans
- **AND** the affected action rows use green completion styling without changing global risk, captcha, or engine health states
- **AND** an available future `releaseAt` is described as the time the action will continue, not as quota release

#### Scenario: Session plan is not active

- **WHEN** the session window is supplied with `active: false`
- **THEN** Electron MAY show the configured single-session plan as waiting to start, but MUST NOT imply that an active session is currently consuming that plan

#### Scenario: Window quota metadata is missing

- **WHEN** a window is missing, or an action total has no supplied cap
- **THEN** Electron MUST NOT fabricate caps, percentages, or plan-completed states for that action or window

#### Scenario: Rolling quota window snapshot expires

- **WHEN** a minute or hour window includes timing metadata and the local clock has passed the supplied expiry time without a fresher cloud snapshot
- **THEN** Electron MUST stop presenting that stale window as completed
- **AND** it MAY keep rendering the window as preparing the next round until a new cloud snapshot or local event updates it

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
The Electron companion SHALL distinguish pacing-driven waiting from generic stale activity in the presence strip when cloud-supplied quota-window data shows that the current running or resting session has completed an active capped action. The message SHALL frame the reached cap as a completed round, stage, or daily action plan and explain the next step without implying risk or failure.

#### Scenario: Current pacing window is complete

- **WHEN** Electron is in a running or resting session, the latest presence event is stale, and `ui.snapshot.dailyUsage.windows` shows a current session, minute, hour, or day window with at least one saturated capped action
- **THEN** the presence strip SHALL render a completion message naming the action or its user-facing activity
- **AND** it SHALL state that the platform is being given time to learn from the current activity
- **AND** it SHALL include the estimated remaining wait until `releaseAt` when that timestamp is available and in the future
- **AND** the presence strip MUST NOT animate as if the completed action is still happening
- **AND** it MUST NOT use red warning styling or claim that unrelated actions have stopped

#### Scenario: Pacing evidence is stale or incomplete

- **WHEN** the latest presence event is stale but the relevant quota window is expired, missing, or lacks capped saturated action evidence
- **THEN** Electron SHALL keep the existing stale-activity fallback instead of fabricating a plan-completion explanation

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

### Requirement: 冷待机状态在云恢复期间必须保持待机语义

The Electron companion SHALL present browser cold standby as standby even when the cloud WebSocket is temporarily reconnecting or degraded. It MUST NOT replay ordinary startup activity, show repeated login/browse-start/browse-end events, or present the state as a generic engine crash while no browser wake has been requested.

#### Scenario: 冷待机云恢复中不显示重新登录循环
- **WHEN** an environment is in cold standby and cloud connectivity is reconnecting or degraded
- **THEN** the primary state remains cold standby, with cloud recovery as a subordinate detail
- **AND** the activity stream MUST NOT add synthetic or repeated "account ready / cloud connected / browse started / browse ended" entries unless a real browser startup and browsing session occurred

#### Scenario: 唤醒后才离开冷待机
- **WHEN** the scheduled wake time arrives or the operator manually resumes the environment
- **THEN** the companion may transition from standby into starting/running states and show real startup events from the new browser session

### Requirement: 发布卡纯展示、审批授权走应用内与飞书双通道

发布候审期间界面 SHALL 呈现一张**纯展示**发布卡（白底、四节点旅程、当前节点为全卡唯一琥珀呼吸点，状态由真实发布链路事件驱动）；发布卡本身 MUST NOT 承载任何审批控件（零按钮）。审批授权 SHALL 收拢在**稿件预览抽屉**内完成：客户可在抽屉里查看成品稿件并直接「发布 / 取消」。

应用内审批与飞书审批 SHALL 为**并行通道**，二者共享同一份 first-writer-wins 审批信号，MUST NOT 各自成局。客户端 SHALL 为纯传输方：权限、版本、先到先得与择时下发的判定**全在云端**，客户端 MUST NOT 本地改写稿件状态后宣称成功；应答 `ok:true` 的语义 SHALL 严格为「决定已受理」，MUST NOT 被呈现为「已发布」。

下发给客户的预览 SHALL 只含**洗稿后的成品**（标题 / 正文 / 话题 / 配图 / 版本号），MUST NOT 含原稿的标题 / 作者 / 正文 / 链接。

#### Scenario: 候审时在应用内直接审批

- **WHEN** 核心进入发布候审（内容已生成、等待人审）
- **THEN** 发布卡出现且**零按钮**（旅程停在「等你确认」节点）；客户可打开稿件预览抽屉，在抽屉内看到成品稿件并直接「发布 / 取消」

#### Scenario: 飞书侧已先行审批

- **WHEN** 同一稿件已在飞书完成审批（审批信号已落）
- **THEN** 应用内的再次审批 SHALL 被云端以「已审批」诚实拒绝，MUST NOT 二次下发、MUST NOT 在端上伪造成功

### Requirement: 稿件预览抽屉配图可逐张删除、非乐观、最后一张不可删

稿件预览抽屉的配图区 SHALL 在**可审批态**（稿件处于待审）**且配图 ≥ 2 张**时，为每张配图提供**删除入口**；删除 SHALL 经既有的「渲染层 → 主进程 → 核心子进程 → 边-云 WS」链路发往云端（渲染层 MUST NOT 直接访问网络），由云端在其账号绑定的编辑通道上完成落库（见 `publish-draft-client-edit`）。

删除交互 SHALL 满足：

- **二次确认**：删除前 SHALL 就地二次确认，MUST NOT 单击即删。
- **非乐观**：确认后 MUST NOT 先行在本地移除缩略图；SHALL 置忙态等待云端应答，并以**服务端回读的真态**（新配图列表 + 新版本号）重绘。
- **忙态互斥**：删除在途时「发布」「取消」及其余删除入口 SHALL 一并禁用，避免客户以**过期版本号**发起审批而撞版本闸、看到莫名其妙的失败。
- **最后一张不可删**：配图仅剩一张时 SHALL NOT 显示删除入口，并 SHALL 给出「至少保留一张配图」的说明（云端同样拒绝，端上提示不是唯一防线）。
- **拒因诚实**：删除失败 SHALL 按云端具名拒因呈现可区分的中文原因（稿件已更新 / 该配图已不在稿件里 / 稿件已审批过 / 至少保留一张配图 / 未连上云端等），MUST NOT 以「删除成功」或任何乐观措辞掩盖失败，MUST NOT 在失败后仍把该张从界面上抹掉。
- **状态跨帧存活**：确认态与忙态 SHALL NOT 依赖抽屉 DOM 存活（抽屉在每帧云端快照到达时整体重建），MUST NOT 因一次心跳快照而丢失。

删除成功后，客户端所持稿件的**配图列表与版本号** SHALL 立即更新为服务端真态，使随后的「发布」不因版本过期被弹回；该更新 SHALL 由持有稿件状态的主进程写入并广播，MUST NOT 只改渲染层本地副本（否则下一帧广播会把它顶掉、被删的图会「长回来」）。

已删除的配图 MUST NOT 提供撤销 / 重新加入的入口——客户端**只删不注入**。

#### Scenario: 删掉一张多余配图后照常发布

- **WHEN** 待审稿件有 3 张配图，客户在预览抽屉里删掉其中一张并确认
- **THEN** 该张 SHALL 在云端落库删除后从界面消失，其余两张保序留存；抽屉与发布卡的配图张数 SHALL 更新为服务端真态；客户随即点「发布」SHALL NOT 因版本过期失败

#### Scenario: 只剩一张配图

- **WHEN** 待审稿件只剩一张配图
- **THEN** 该张 SHALL NOT 显示删除入口，界面 SHALL 说明至少保留一张配图

#### Scenario: 删除在途时不能审批

- **WHEN** 一次删除请求在途未回
- **THEN** 「发布」「取消」与其余删除入口 SHALL 处于禁用态，直至应答返回

#### Scenario: 删除失败诚实呈现

- **WHEN** 云端以具名拒因拒绝删除（如稿件已被他处修改、该配图已不在稿件里、稿件已审批过、客户端未连上云端）
- **THEN** 界面 SHALL 呈现对应的中文原因、该张配图 SHALL 仍在界面上（未被抹掉），MUST NOT 出现任何成功措辞

### Requirement: 人设绑定态为三态，未知绝不等同未绑

The `personaBound` signal on the `ui.snapshot` stream SHALL carry three states: `true` (cloud confirms bound), `false` (cloud confirms unbound), and **absent** (unknown — the cloud has not said yet). Cloud is the single writer of persona state and therefore SHALL send both `true` and `false`. Edge MUST NOT treat "unknown" as "unbound": no timer, grace window, or timeout may promote unknown into unbound.

#### Scenario: 云端确认未绑才算未绑
- **WHEN** cloud has determined the account has no persona
- **THEN** cloud sends `personaBound: false`, and edge may present the account as "未设置"

#### Scenario: 信号未到时保持未知
- **WHEN** the edge is logged in and connected but has not yet received a `personaBound` signal
- **THEN** edge presents the persona state as pending ("待启动"), never as "未设置", and no amount of elapsed time changes that

#### Scenario: 解绑即时可见
- **WHEN** a persona is bound or unbound (including "saving an empty persona = explicit unbind")
- **THEN** cloud repushes the new bound state to the account's online edge immediately, without waiting for the next handshake

#### Scenario: 绑定态不被慢快照拖住
- **WHEN** the hello snapshot requires slow database round-trips to assemble
- **THEN** the persona bound state — a zero-I/O in-memory read — is delivered ahead of them, not behind them

### Requirement: 人设向导只能由权威的「未绑」自动弹出

The desktop client SHALL auto-open the persona setup wizard only when the cloud has authoritatively reported `personaBound: false` for the currently selected environment. Absence of the signal MUST NOT trigger it. Any state reset (core respawn, cold-standby wake, environment removal and re-add) MUST at worst return the state to "unknown", which never prompts.

#### Scenario: 已设置人设的账号永不被误弹
- **WHEN** an account that has a persona restarts its core (e.g. cold-standby wake), transiently returning its bound state to unknown
- **THEN** the wizard does not open and no system notification is sent

#### Scenario: 真正未设置的账号照常被提醒
- **WHEN** cloud reports `personaBound: false` for a logged-in, connected account
- **THEN** the wizard opens once and one system notification is sent

#### Scenario: 系统误弹的窗在权威「已绑」到达时自动收起
- **WHEN** the wizard was opened automatically and an authoritative `personaBound: true` subsequently arrives for that environment
- **THEN** the client closes the auto-opened wizard; a wizard the user opened by hand is never closed for them

### Requirement: 首次连接与断线重连是两种处境，绝不共用一句话

The desktop client SHALL distinguish "this core run has never reached the cloud yet" from "this core run was connected and lost it". The status projection SHALL carry a per-core-run fact recording whether the cloud connection has ever been established on the current core process. A missing cloud connection MUST NOT be presented as "正在重新连接" unless that fact is true — the prefix「重」asserts a prior connection, and asserting one that never happened is a lie of the same family as treating "unknown" as "no".

The fact SHALL be reset to false whenever a new core process is spawned (including crash respawn and explicit restart), and set to true when the core reports the cloud connection is up. Cold-standby wake MUST NOT reset it: the cloud connection is held open across standby by design, so a woken core has indeed been connected.

#### Scenario: 冷启动全程呈现为启动中
- **WHEN** an environment is started and its core is still bringing the browser up — the core has printed log lines (so the engine is demonstrably alive) but has not yet reported the cloud connection
- **THEN** the client presents the environment as「启动中」throughout, and MUST NOT present it as「正在重新连接」

#### Scenario: 正常冷启动绝不冒充需要人工
- **WHEN** an environment is in that same first-connect window
- **THEN** the environment rail shows it at the launching level with no action needed, and it MUST NOT be raised to the attention level or floated to the top of the rail alongside genuine login / captcha / risk-control interventions

#### Scenario: 真正的断线仍然如实报重连
- **WHEN** the cloud connection has been established on the current core run and is subsequently lost while the session is running
- **THEN** the client presents「正在重新连接」at the attention level and marks it as needing attention

#### Scenario: 换核心即失去连上过的资格
- **WHEN** the core process is restarted (explicit restart, or respawn after a crash) — even though the previous core had connected
- **THEN** the new core run starts out having never connected, and its startup window is presented as「启动中」, not as「正在重新连接」

#### Scenario: 冷待机唤醒不退回未连接
- **WHEN** an environment wakes from cold standby, where the cloud connection was deliberately held open while only the browser was closed
- **THEN** the client still regards the cloud as having been connected on this core run, and no first-connect window is re-entered

### Requirement: Electron 主窗口使用统一且正交的视觉语义

Electron 主窗口 SHALL 使用一致的表面、边框、圆角、排版和颜色语义组织标题身份、当前状态、浏览阶段、运行说明、发布结果、今日进展与活动记录。交互选择和焦点 SHALL 使用蓝色；平台色 SHALL 只表达账号平台；绿、琥珀、红、灰等状态色 SHALL 只表达运行结果或紧迫度。正常稳态标题栏 SHALL 使用中性表面，MUST NOT 用平台色或状态色长期铺满页面。

#### Scenario: 正常稳态不制造告警感
- **WHEN** 当前环境处于就绪、运行或正常节奏等待状态
- **THEN** 标题栏和主页面使用中性或柔和蓝色表面，状态结果只在对应药丸、状态点或结果标签中出现
- **AND** 平台红/蓝不被用于表示当前选择或系统健康

#### Scenario: 警戒与异常仍清晰可辨
- **WHEN** 当前环境进入需协助、受限、冻结或真实运行异常
- **THEN** 对应健康结论继续使用既有琥珀或红色语义，MUST NOT 因视觉统一而弱化或隐藏失败

#### Scenario: 小窗口保持层级与可操作性
- **WHEN** 主窗口宽度不足以单行容纳浏览阶段、进度指标或会话控制
- **THEN** 浏览阶段可横向滚动，进度指标重排为多行，会话控制换行但仍与今日进展同组
- **AND** 任何控件 MUST NOT 覆盖活动记录或被裁出可视区域

### Requirement: 核心日志的严重级别按内容判定，不得按输出通道判定

桌面客户端 MUST 依据核心进程日志行的**内容**判定其严重级别，MUST NOT 依据该行走的是 stdout 还是 stderr 来判定。

理由：Node 的 `console.warn` / `console.error` 一律写 stderr，因而「这行走了 stderr」只是一个**传输事实**，不承载「出错了」这个**语义断言**。核心里绝大多数写 stderr 的行是良性的诊断、进度与排队说明。

- 边缘进程徽标 MUST 仅在该行被判为 `fatal`（真失败形状）时翻成异常态；被判为 `warn` / `info` 的行 MUST NOT 使边缘进程徽标离开 `running`，MUST NOT 使该环境获得「需处理」角标或被排到环境栏顶部。
- 失败归因候选（核心异常退出时呈现给运营的那条「失败原因」）MUST 只由 `fatal` 行填充。良性 stderr 行 MUST NOT 覆盖它。
- 严重级别分类器 MUST 是可单测的纯函数（不依赖 Electron / 进程 / 文件系统）。
- **不吞真失败**：分类器 MUST 把既有失败签名（启动失败 / 不可达 / `not allowed` / `being used` / `no_target` / `code=-N`）与常见运行时异常形状（`Error:` / `TypeError` / `ECONNREFUSED` / `unhandled` / `FATAL` 等）判为 `fatal`。
- **权威判据不变**：核心真正异常退出时的失败呈现 MUST 继续由退出处（退出码 / 信号）权威判定，不受本分类器影响。日志行分类只是**预测**，退出码才是**权威**。
- 日志**文件**（排障回溯用）MUST 继续按真实输出通道记录（stderr 行仍带 `ERR` 标记）——传输事实要如实留痕，只是不再被误读成语义。

#### Scenario: 良性排队说明不再被讲成运行异常

- **WHEN** 核心因浏览器槽位排队而向 stderr 打印「外壳暂时给不出浏览器槽位（…）：本次诚实作答，环境仍在等槽位队列里」
- **THEN** 该环境的边缘进程徽标保持 `running`，环境栏 MUST NOT 显示「异常」、MUST NOT 加「需处理」角标、MUST NOT 把该环境浮到列表顶部，在场文案 MUST NOT 出现「引擎已停止」

#### Scenario: 发布期诊断日志不再闪红

- **WHEN** 一次发布过程中核心向 stderr 打印租约抑制说明与 `[publish-submit-diag]` 诊断行
- **THEN** 该环境徽标全程不翻红、不出现「闪红又秒恢复」，健康结论保持「运行中」

#### Scenario: 真启动失败仍如实翻红

- **WHEN** 核心打印一条真失败行（如 AdsPower `browser/start` 启动失败、`not allowed to open`、`code=-1`）
- **THEN** 边缘进程徽标翻成异常态，该行被记为失败归因候选

#### Scenario: 核心异常退出时归因是真失败行而非最后一条良性 warn

- **WHEN** 核心先打印若干良性 stderr 行（诊断 / 排队说明），随后打印一条真失败行，再异常退出
- **THEN** 呈现给运营的「失败原因」是那条真失败行，MUST NOT 是任何一条良性 stderr 行

#### Scenario: 未识别的良性 stderr 行不被默认判死

- **WHEN** 核心向 stderr 打印一条既不匹配失败签名、也不匹配运行时异常形状的行
- **THEN** 边缘进程徽标 MUST NOT 因此翻红；若核心确实随后异常退出，红仍由退出处权威判据给出

### Requirement: 今日进展折叠控件直接表达展开状态

今日进展的窗口详情 disclosure 控件 SHALL 同时显示动作文字与方向箭头：收起态显示“展开”及向下箭头，展开态显示“收起”及向上箭头。该控件 MUST 使用次要 ghost 样式，视觉权重 MUST 低于启动、暂停、恢复或关闭等生命周期主操作，并 MUST 同步 `aria-expanded` 与可访问名称。

#### Scenario: 今日节奏详情默认收起

- **WHEN** 客户端已收到可展开的配额窗口且详情尚未展开
- **THEN** disclosure 控件显示“展开”及向下箭头
- **AND** 控件的 `aria-expanded` 为 `false`，可访问名称明确表达展开今日节奏

#### Scenario: 今日节奏详情已经展开

- **WHEN** 用户通过今日进展卡或 disclosure 控件展开窗口详情
- **THEN** disclosure 控件显示“收起”及向上箭头
- **AND** 控件的 `aria-expanded` 为 `true`，可访问名称明确表达收起今日节奏

### Requirement: 无发布记录的占位卡默认收起且可主动展开

当当前环境没有进行中的发布流程、也没有可展示的历史发布记录时，Electron 伴随窗口 SHALL 将“还没有发布过内容”的发布卡默认收起为薄条；该默认状态 MUST NOT 因引擎或会话处于运行、暂停、停止或尚未启动而改变。薄条 SHALL 保留空态身份与摘要，用户点击后 SHALL 能临时展开完整占位内容与四阶段旅程，并可再次收起。有真实待确认或已确认待发布流程到来时，发布卡 MUST 自动展开，MUST NOT 继续以空态薄条隐藏真实发布进度。

#### Scenario: 客户端未运行且从未发布过内容

- **WHEN** 当前环境没有发布记录、没有进行中的发布流程，且引擎或会话尚未运行
- **THEN** 发布卡默认显示为“发布过的 AI 写好的笔记 / 还没有发布过内容”薄条，而不是展开的占位卡

#### Scenario: 用户主动查看空态旅程

- **WHEN** 用户点击默认收起的空态薄条
- **THEN** 发布卡临时展开并显示“等待第一条笔记”与完整四阶段旅程，用户可通过既有卡头交互再次收起

#### Scenario: 空态期间到达真实发布流程

- **WHEN** 空态薄条存在时收到待确认或已确认待发布的真实稿件状态
- **THEN** 发布卡自动展开并显示真实发布进度，MUST NOT 继续展示空态薄条

### Requirement: 委派浮层入口轻量可达且不挤压陪伴主视图

陪伴主视图 SHALL 在在场感行最右侧提供视觉权重克制的委派图标入口。入口 MUST 使用既有交互蓝与圆角表面语义，打开态 MUST 可辨，并同步 `aria-expanded`、可访问名称和关联浮层。存在非终态委派任务时入口 SHALL 提供克制的进行中指示，但 MUST NOT 使用成功、警告或失败状态色冒充任务结果。

委派浮层 SHALL 锚定入口并适配主窗口边界：宽度随窄窗口收缩，高度不得超过可视区，任务较多时仅浮层主体滚动；浮层 MUST NOT 改变在场感、运行价值、发布卡、今日进展或活动流在主文档流中的位置。

#### Scenario: 默认首屏没有委派卡片占位
- **WHEN** 客户端加载且用户尚未打开委派入口
- **THEN** 在场感行右端显示委派图标，委派浮层不可见且不占主文档流高度
- **AND** 后续运行价值、发布卡与今日进展保持原有层级

#### Scenario: 浮层在窗口边界内展示并内部滚动
- **WHEN** 用户在窄窗口或较矮窗口中打开委派浮层且任务列表超过可用高度
- **THEN** 浮层宽度收缩到窗口内、高度受可视区限制，头部和关闭入口可达，任务内容在浮层主体内部滚动
- **AND** 浮层不会把主列内容向下推移

#### Scenario: 用户可用常见方式关闭浮层
- **WHEN** 委派浮层已打开，用户再次点击入口、点击关闭按钮、点击浮层外部或按 Escape
- **THEN** 浮层关闭，`aria-expanded` 更新为 `false`
- **AND** 通过 Escape 关闭时键盘焦点返回委派入口

#### Scenario: 进行中任务只显示克制指示
- **WHEN** 当前环境的真实任务列表含 queued、planning、waiting_approval、executing 或 deferred 等非终态任务
- **THEN** 委派入口显示小型交互蓝指示并在可访问名称中说明有进行中任务
- **AND** 入口 MUST NOT 因该指示宣称任务成功或失败

### Requirement: Facebook 已确认点赞记录标识实际被点赞内容

客户端 SHALL 在 Facebook 点赞经后置校验确认成功后，使用点赞执行器从实际被作用帖子读取的见证数据生成活动流摘要；当作者与正文/标题开头可用时，摘要 SHALL 同时展示二者并进行单行空白规范化与有界截断。摘要 MUST NOT 复用上一条阅读记录猜测目标，MUST NOT 展示 permalink 或原始 note ID，也 MUST NOT 改变云端归账或本地点赞计数语义。

#### Scenario: 已确认点赞展示作者与稿件摘要
- **WHEN** Facebook 点赞后置校验成功，且实际被作用帖子的见证包含作者和正文/标题开头
- **THEN** 客户端新增一条同时包含有界作者与正文/标题摘要的“赞”活动记录
- **AND** 该记录贡献且只贡献一次现有本地点赞兜底计数

#### Scenario: 点赞见证字段缺失时诚实降级
- **WHEN** Facebook 点赞确认成功，但见证只包含作者或正文/标题开头，或两者都缺失
- **THEN** 客户端使用可用字段生成部分摘要，或回退为通用“点了个赞”文案
- **AND** 活动记录 MUST NOT 展示 permalink、原始 note ID，也 MUST NOT 从上一条阅读记录补齐缺失字段

#### Scenario: 非成功点赞不生成成功摘要
- **WHEN** Facebook 点赞处于 shadow、失败、已点赞、未找到目标或后置校验未确认状态
- **THEN** 客户端 MUST NOT 生成点赞成功活动记录或本地点赞成功增量

### Requirement: Facebook 写动作必须在客户端如实分档呈现

客户端 SHALL 为 Facebook 的**评论、加群、搜索**产出结构化活动条目，且 MUST NOT 因这些动作由委托处理器（而非浏览会话主出口）执行而静默无声。叙述 MUST NOT 新增任何成功判定：客户端 SHALL 只叙述执行器**已经作出、且已回报云端**的判断，判据与回报云端的 `action.completed` 完全一致，客户端与云端 MUST NOT 就「某动作是否发生」给出互相矛盾的结论。

四档 SHALL 互斥且穷尽：

- **成功**——仅当执行器既有后置校验判成（评论经本人身份服务器确认、加群经成员信号或结构确认）。
- **待第三方批准**——一手 DOM 观察到待审徽章或参与审批弹层。MUST 自成一档、MUST NOT 表述为已发布 / 已加入、MUST NOT 贡献任何计数。
- **结构性失败**——结构上做不到（评论框没找到 / 没权限 / 没结果）。MUST 呈现人话原因，MUST NOT 直接吐机器码。
- **未开始**——资源被占、被独占任务抢占、会话关闭中、能力不支持、只观察不点。MUST NOT 产条目，MUST NOT 计为失败。

「未开始」的判定 SHALL 以**拒绝集**（列举不算数的原因）实现，MUST NOT 以白名单（列举算数的原因）实现——后者会使未来新增的失败原因静默消失。

计数 SHALL 只在评论真成功时贡献一次本地兜底 `comments` 增量；加群与搜索 MUST NOT 贡献任何计数（二者在云端权威计数投影中均不存在对应字段）。

活动条目的主语 SHALL 只取自一手数据（打进去的评论文本、现读到的群名、下发的搜索词），MUST NOT 展示 permalink 或原始 note ID；群名读取失败 MUST 回落通用文案，MUST NOT 用 URL 顶替。

#### Scenario: 评论真成功
- **WHEN** Facebook 评论经本人身份服务器确认落地（执行器回 `ok:true`）
- **THEN** 活动流新增一条含评论文本有界摘要的「评论了」条目
- **AND** 该条目贡献且只贡献一次本地 `comments` 兜底增量

#### Scenario: 评论卡在群参与审批
- **WHEN** 执行器观察到待审徽章或参与审批弹层，回 `ok:false, reason:'pending_group_approval'`
- **THEN** 活动流新增一条明确表述「评论待管理员批准、还没显示出来」的条目
- **AND** 该条目 MUST NOT 表述为已发布，MUST NOT 贡献任何计数

#### Scenario: 评论框没找到
- **WHEN** 执行器回 `ok:false, reason:'editor_not_found'`
- **THEN** 活动流新增一条含人话原因的「评论没发出去」条目，MUST NOT 直接展示 `editor_not_found` 机器码

#### Scenario: 被占用或被抢占不产条目
- **WHEN** 命令因 `busy` / `preempted_by_task` / `session_closing` / `browse_disabled` / `capability_unsupported` 回非成功
- **THEN** 活动流 MUST NOT 新增任何条目，且 MUST NOT 把该情形叙述为一次失败

#### Scenario: 未知失败原因默认可见
- **WHEN** 执行器回一个拒绝集之外、映射表未覆盖的新失败原因
- **THEN** 活动流 MUST 仍产出一条回落通用文案的失败条目，MUST NOT 静默吞掉

#### Scenario: 加群成功以云端同一证据闸为准
- **WHEN** 加群回 `ok:true` 且 `clicked===true`
- **THEN** 活动流新增一条含现读群名的「加入了小组」条目
- **AND** 该判据 MUST 与云端 `interaction.occurred` 的加群闸一致

#### Scenario: 加群待批准与需答问卷
- **WHEN** 加群回 `pending` 或 `questionnaire_required`
- **THEN** 活动流新增一条表述「等待管理员通过」或「需要回答入群问题、没有自动作答」的条目，MUST NOT 表述为已加入

#### Scenario: 已是成员或只观察不产条目
- **WHEN** 加群回 `already_member` 或 `observation_only`
- **THEN** 活动流 MUST NOT 新增条目——二者均未发生一次真实加群动作

#### Scenario: 搜索呈现容器与真实结果数
- **WHEN** Facebook 定向搜索在某群内成功返回候选
- **THEN** 活动流新增一条含现读群名、搜索词与真实候选数的条目
- **AND** 该条目 MUST NOT 贡献任何计数

#### Scenario: 搜索零结果与搜索失败可区分
- **WHEN** 搜索成功执行但零候选，或搜索因结构性原因失败
- **THEN** 前者 MUST 表述为「没有匹配的帖子」、后者 MUST 表述为搜索失败并给出人话原因，二者 MUST NOT 混为一谈

### Requirement: 同一条开帖在两条路径上的叙述必须一致

`note.open` 经浏览路径与经评论路径（按 permalink 开帖）SHALL 产出**同一套**「读」叙述与同一次本地浏览兜底增量，MUST NOT 因执行路径不同而一路可见、一路隐形。

当评论路径开帖成功读到内容、但评论框始终催不出来（回非成功以便云端换下一个候选）时，客户端 MUST NOT 产出「读失败」条目——帖子确实打开并读到了，该情形 SHALL 沉默，MUST NOT 把一次成功的阅读叙述成失败。

#### Scenario: 评论路径开帖产出与浏览路径一致的读条目
- **WHEN** 评论路径按 permalink 开帖并成功上报帖子详情
- **THEN** 活动流新增一条与浏览路径措辞一致的「读」条目
- **AND** 贡献且只贡献一次本地浏览兜底增量

#### Scenario: 开帖成功但评论框没找到不叙述为读失败
- **WHEN** 评论路径开帖成功、读到正文，但评论框未就绪，回 `editor_not_found`
- **THEN** 活动流 MUST NOT 新增「读失败」条目

