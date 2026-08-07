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

当 Facebook Reel 已被 Edge 证明为新的活动卡片并上报为 `listKind:'reels'` 时，活动流 MUST 同步新增且仅新增一条“读”分类记录。该记录 SHALL 使用“看了/浏览了”的呈现事实措辞，MUST NOT 宣称看完或深度阅读；作者或摘要缺失时 MUST 使用通用人话回退，MUST NOT 暴露 URL 或原始 id。若同一 Reel 随后因 `facebook.note.open` 上报详情，客户端 MUST 保留详情数据流但 MUST NOT 再新增第二条“读”记录或第二次本地浏览增量。

#### Scenario: 核心事件映射为人话条目
- **WHEN** 核心进程产生已映射的动作日志（如点赞成功 / 提取内容 / 评论发布成功）
- **THEN** 活动流顶部新增一条对应的人话句子并带时间戳，今日计数同步递增

#### Scenario: 无新事件时不造条目
- **WHEN** 核心进程一段时间无新日志
- **THEN** 活动流不新增条目，新鲜度戳如实增长（如「1 分钟前」），不出现任何伪造的「仍在活动」条目

#### Scenario: 未识别日志行不进活动流
- **WHEN** 核心进程输出映射表未覆盖的日志行
- **THEN** 该行仅出现在「开发者详情」原始日志中，活动流不展示半截技术行

#### Scenario: 新 Reel 呈现立即形成一条读记录
- **WHEN** Edge 确认切换到一个新的活动 Reel 并上报单卡 Reels 批次
- **THEN** “今天做了这些”新增一条“读”分类记录，优先显示实际摘要和作者
- **AND** 本地浏览回退计数只增加一次

#### Scenario: Reel 元数据缺失时诚实回退
- **WHEN** 新活动 Reel 缺少作者或摘要
- **THEN** 活动流显示有界的摘要级或通用“看了一个 Reel”文案
- **AND** 不显示 Reel URL、noteId 或其它机器标识

#### Scenario: 随后的详情上报不重复读记录
- **WHEN** 已产生 Reel 呈现记录的同一规范 Reel 随后上报 `note.detail`
- **THEN** 详情继续送达 Cloud 和内容评估链
- **AND** 客户端不新增第二条“读”记录、不重复增加本地浏览回退计数

#### Scenario: Reel 未切换时不造读记录
- **WHEN** Reel 导航失败、活动身份不变或命中已见身份而未上报新单卡批次
- **THEN** 活动流不新增 Reel “读”记录

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

云端为该账号投影出的每一项用量指标 SHALL 作为界面收尾的“今日进展”分段面板呈现，不再以互相独立的大号 KPI 卡片作首屏主视觉。指标集合 SHALL 由云端按平台投影后下发决定，MUST NOT 写死为固定项数；面板布局 MUST NOT 依赖指标数量恒定。各项指标 SHALL 在同一容器中以分隔线成组；汇总标题、数据来源、统计时间与当前环境的启动 / 暂停 / 恢复 / 关闭控制 SHALL 属于同一个摘要上下文。生命周期控制 MUST NOT 以固定悬浮层覆盖活动流。摘要 MUST 使用进展与计划语义，MUST NOT 将正常动作累计描述为受限用量。

#### Scenario: 计数照常累计且在今日进展呈现
- **WHEN** 会话中发生互动动作
- **THEN** 对应计数在“今日进展”分段面板内递增，首屏主视觉区不出现相互独立的大号计数磁贴
- **AND** 汇总标题与展开入口不使用“用量”或“限额”措辞

#### Scenario: 生命周期控制不再遮挡活动记录
- **WHEN** 当前环境处于就绪、运行或暂停状态
- **THEN** 对应的启动、暂停、恢复或关闭操作显示在今日进展标题区
- **AND** 活动流上方或右下角不存在固定悬浮的会话控制层

#### Scenario: 指标数量随平台变化时分隔线与分组不塌
- **WHEN** 云端为该账号投影出的指标少于或多于另一个平台的指标数
- **THEN** 分段面板按实际下发的指标成组、分隔线随之对齐
- **AND** 面板不出现空格位、错位分隔线或残留的占位磁贴

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
- **WHEN** Facebook 就地身份读取（`identity.read_current`，不离开当前页）产生核心日志（词汇批 4 后 FB 会话结构上收不到任何作者主页命令，历史 `profile.open` 就地读形态由此取代）
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
- **THEN** Electron renders the supplied account daily totals for exactly the actions the cloud supplied, instead of treating the local process's current-session deltas as authoritative
- **AND** it renders no metric for an action the cloud did not supply

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
The Electron companion SHALL show plan progress for each cloud-supplied quota window: current session, minute, hour, and day, while keeping the collapsed daily summary focused on today's account totals. Expanded labels SHALL identify those scopes as “本轮计划”, “近 1 分钟”, “近 1 小时”, and “今日计划”. The client MUST NOT describe the session as a rolling “近 N 分钟” window. Expanded detail SHALL preserve exact supplied totals and caps while presenting a cap as a secondary “最多 N” boundary rather than a slash-form completion target.

#### Scenario: Daily card is collapsed by default

- **WHEN** Electron has received account-scoped daily usage with quota windows
- **THEN** the collapsed card renders the day-window totals for exactly the actions the cloud supplied for that account
- **AND** it does not render session, minute, or hour action details until the user expands the card

#### Scenario: User expands the daily progress card

- **WHEN** the user clicks the daily progress card or its disclosure control
- **THEN** Electron renders plan detail labeled “本轮计划”, “近 1 分钟”, “近 1 小时”, and “今日计划” for the supplied session, minute, hour, and day windows respectively
- **AND** each window detail lists as separate action rows exactly those actions for which that window supplies a total or a cap, and no others
- **AND** each capped action row shows its supplied total followed by secondary “最多 N” wording
- **AND** an uncapped action row shows its supplied total without `/-`, a fabricated cap, or cap progress styling

#### Scenario: Active session has trustworthy timing

- **WHEN** the session window is active and supplies finite `startedAt` and future `expiresAt` timestamps
- **THEN** the “本轮计划” group shows the remaining round time in its state area
- **AND** its metadata shows the local start time and expected end time
- **AND** the client derives both displays from the supplied timestamps rather than hard-coding the configured round duration

#### Scenario: Cloud supplies all quota windows

- **WHEN** `ui.snapshot.dailyUsage.windows` includes `session`, `minute`, `hour`, and `day`
- **THEN** Electron renders those windows as peer detail groups ordered session, minute, hour, and day
- **AND** the groups use a 2×2 grid at the normal companion width and a one-column grid at the existing narrow breakpoint
- **AND** it marks completed actions distinctly from near-complete actions without relying on a single worst-action summary as the only visible data

#### Scenario: Any window completes its plan

- **WHEN** any supplied window's `saturated` list is non-empty, or any supplied action total is greater than or equal to that window's supplied cap
- **THEN** Electron's aggregate progress status shows `完成 N 项`, counting every completed supplied action plan
- **AND** the `完成 N 项` state text uses the completion color
- **AND** the whole window card and completed row use completion styling only when browsing is complete
- **AND** when browsing is incomplete, a completed like, favorite, comment, follow, or publish action keeps the card and its action row in the normal visual style without changing global risk, captcha, or engine health states
- **AND** an available future `releaseAt` is described as the time the action will continue, not as quota release

#### Scenario: Session plan is not active

- **WHEN** the session window is supplied with `active: false`
- **THEN** Electron MAY show the configured single-session plan as waiting to start, but MUST NOT imply that an active session is currently consuming that plan
- **AND** it MUST NOT fabricate remaining time or an expected end time

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

发布候审期间界面 SHALL 呈现一张**纯展示**发布卡（白底、四节点旅程、当前节点为全卡唯一琥珀呼吸点，状态由真实发布链路事件驱动）；发布卡本身 MUST NOT 承载任何审批控件（零按钮）。审批授权 SHALL 收拢在**占满主内容区的稿件审核页面**内完成：客户可在页面里查看成品稿件并直接「发布 / 取消」。审核页面 MUST 保留全局标题栏、当前账号、环境入口与真实运行健康状态，并提供返回来源页和关闭回运行首页的应用内导航。

应用内审批与飞书审批 SHALL 为**并行通道**，二者共享同一份 first-writer-wins 审批信号，MUST NOT 各自成局。客户端 SHALL 为纯传输方：权限、版本、先到先得与择时下发的判定**全在云端**，客户端 MUST NOT 本地改写稿件状态后宣称成功；应答 `ok:true` 的语义 SHALL 严格为「决定已受理」，MUST NOT 被呈现为「已发布」。

下发给客户的预览 SHALL 只含**洗稿后的成品**（标题 / 正文 / 话题 / 配图 / 版本号），MUST NOT 含原稿的标题 / 作者 / 正文 / 链接。

#### Scenario: 候审时在应用内直接审批

- **WHEN** 核心进入发布候审（内容已生成、等待人审）
- **THEN** 发布卡出现且**零按钮**（旅程停在「等你确认」节点）；客户可打开稿件审核页面，在主内容区看到成品稿件并直接「发布 / 取消」

#### Scenario: 飞书侧已先行审批

- **WHEN** 同一稿件已在飞书完成审批（审批信号已落）
- **THEN** 应用内的再次审批 SHALL 被云端以「已审批」诚实拒绝，MUST NOT 二次下发、MUST NOT 在端上伪造成功

#### Scenario: 审核页返回与关闭

- **WHEN** 客户从运行首页或内容页进入稿件审核后点击返回或关闭
- **THEN** 返回恢复进入审核前的页面状态，关闭回到运行首页，且主窗口与边缘核心继续运行

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

`facebook.note.open` 经浏览路径与经评论路径（按 permalink 开帖）SHALL 产出**同一套**「读」叙述与同一次本地浏览兜底增量，MUST NOT 因执行路径不同而一路可见、一路隐形。

当评论路径开帖成功读到内容、但评论框始终催不出来（回非成功以便云端换下一个候选）时，客户端 MUST NOT 产出「读失败」条目——帖子确实打开并读到了，该情形 SHALL 沉默，MUST NOT 把一次成功的阅读叙述成失败。

#### Scenario: 评论路径开帖产出与浏览路径一致的读条目
- **WHEN** 评论路径按 permalink 开帖并成功上报帖子详情
- **THEN** 活动流新增一条与浏览路径措辞一致的「读」条目
- **AND** 贡献且只贡献一次本地浏览兜底增量

#### Scenario: 开帖成功但评论框没找到不叙述为读失败
- **WHEN** 评论路径开帖成功、读到正文，但评论框未就绪，回 `editor_not_found`
- **THEN** 活动流 MUST NOT 新增「读失败」条目

### Requirement: 视频号工作区必须提供互动读取设置与三层真态

InteractionWorkspace SHALL 在当前环境顶部提供“收取互动”总开关、评论收取开关和私信收取开关，并分别展示 Cloud stored 意图、Edge application status 与 effective read capability。切换 MUST 通过具名 IPC 调用客户 read-controls API、携 expectedVersion 并在回包 envKey 不匹配时丢弃；pending/冲突/失败期间 MUST 保持诚实 busy 或错误状态，MUST NOT 本地先改成已生效。

读取开关的可编辑性 SHALL 只由「这次写入本身能不能被受理」决定，判据 SHALL 限于：授权态 active、已取到 Cloud stored 真态（因而有 expectedVersion 可携）、当前数据不是 stale、具名 IPC 通道存在。该环境**核心子进程的在线状态**（`connectivity`）MUST NOT 参与该判定——这次写入由客户端主进程直发 Cloud HTTP，链路上不存在该核心子进程；Cloud 在无 Edge 在线时 SHALL 按 CAS 正常落库并回报 `edgeDelivery.status=deferred`，Edge 下次连接时经欢迎信封的 runtime-controls 快照收敛。客户端 MUST NOT 因为该环境未启动、已停止或核心子进程离线，在本地拦下一次 Cloud 完全能够受理的写入；此类本地拦截 MUST NOT 被呈现为该能力不可用。

授权态 `status` 与浏览器现场 `browserState` MUST 保持正交：`status=active` 且 `browserState=closed`（后台 API-only 运行）SHALL 继续视为可编辑，MUST NOT 被合并成单一“是不是起着”的判定。

保存结果 SHALL 按 Cloud 回包的 `edgeDelivery` 如实分档，并在读取设置区**持久可见**，MUST NOT 只写入会被后续任意动作清空的一次性通知位：`enqueued` SHALL 表述为已保存并已下发本机；`deferred` SHALL 表述为已保存、待该环境下次连接后生效，并指明需要启动该环境。两者 MUST NOT 表述为已生效或已应用；只有 Edge 回报的 applicationStatus 与 storedVersion 一致时才 MAY 表述为本机已应用。

#### Scenario: 总开关同时更新两个读取渠道
- **WHEN** 客户在当前视频号环境打开“收取互动”
- **THEN** 客户端提交两个 read=true 与当前 storedVersion，收到 Cloud 真态后刷新；写字段没有入口也没有请求字段

#### Scenario: 环境已停止时读取开关仍可编辑并真的写入 Cloud
- **WHEN** 当前视频号环境的核心子进程未启动或已停止（connectivity 不为 connected），而 status=active、stored 已取到且数据不是 stale
- **THEN** 三个读取开关 SHALL 可编辑，切换 SHALL 真的携 expectedVersion 发出 read-controls 请求
- **AND** MUST NOT 因 connectivity 在本地拦下该请求或把开关禁用

#### Scenario: 离线保存必须显示待生效而不是已生效
- **WHEN** 上述写入被 Cloud 受理并回 `edgeDelivery.status=deferred`
- **THEN** 读取设置区 SHALL 持久显示已保存、待该环境下次连接后生效，并指明需要启动该环境
- **AND** MUST NOT 显示“本机已应用”“已生效”或任何等价措辞
- **AND** 该呈现 MUST NOT 因客户随后进行其他操作而消失

#### Scenario: 已下发本机与延后下发可区分
- **WHEN** 同一写入被 Cloud 受理并回 `edgeDelivery.status=enqueued`
- **THEN** 呈现 SHALL 表述为已保存并已下发本机，与 deferred 的措辞可区分
- **AND** 在 Edge 回报同一版本前 MUST NOT 表述为已应用

#### Scenario: 浏览器已关闭的后台运行环境保持可编辑
- **WHEN** 环境 status=active 且 browserState=closed（含冷待机：浏览器已关、核心仍在线）
- **THEN** 读取开关 SHALL 保持可编辑
- **AND** status 与 browserState MUST NOT 被合并成单一可编辑判定

#### Scenario: 授权失效或数据 stale 仍然拦截
- **WHEN** status 非 active，或当前显示的是上次成功数据（stale，storedVersion 可能已落后）
- **THEN** 读取开关 SHALL 保持禁用并显示对应原因，避免携过期 expectedVersion 发起 CAS

#### Scenario: Cloud 已保存但 Edge 尚未应用
- **WHEN** stored read 已开启而 applicationStatus=pending
- **THEN** 页面显示“已保存，等待本机应用”，MUST NOT 显示“同步正常”

#### Scenario: Edge 已应用但平台读取能力不可用
- **WHEN** stored/applied 均就绪但 commentsRead 或 dmRead effective capability=false
- **THEN** 对应渠道显示“平台能力未就绪”并给出登录/probe 处理提示，另一渠道 MAY 独立正常

### Requirement: 互动空态必须区分未开启与确实无消息

页面 SHALL 只有在对应 read stored=true、applicationStatus=applied、effective capability=true 且存在成功数据时间时显示“当前没有评论互动/私信会话”或“同步正常”。读取关闭、待应用、能力不可用、auth 阻断和 Cloud stale MUST 各自显示原因与可执行入口；局部刷新在读取关闭时 MUST NOT 冒充会带来新数据。

#### Scenario: 两个读取开关都关闭
- **WHEN** 当前账号 commentsReadEnabled=false 且 dmReadEnabled=false
- **THEN** 顶部显示“互动收取已关闭”，空态引导开启收取，MUST NOT 显示“评论/私信同步正常”

#### Scenario: 已启用渠道真实空结果
- **WHEN** 对应渠道三层门禁均通过且最近同步成功但 items 为空
- **THEN** 页面才显示该渠道当前没有互动，并保留数据时间

### Requirement: 非平台发送动作不得被发送 capability 静默拦截

renderer SHALL 将通用可写门禁与 channel send capability 分离。保存最终文字、重新生成、忽略、转人工和批准 MUST NOT 仅因 commentsReply/dmSendText=false 而被本地拦截；只有“发送回复”按钮 SHALL 在对应发送 capability=false 时禁用。任何禁用动作 MUST 显示可读原因，handler 与按钮状态 MUST 一致，MUST NOT 出现看似可点但点击无反应。

#### Scenario: 只读账号仍可整理收件箱
- **WHEN** 评论读取可用但 commentsReply=false
- **THEN** 客户仍可忽略或转人工，并可在有有效 published config 时编辑/重新生成/批准；发送回复明确禁用并解释原因

#### Scenario: auth 或 Cloud stale 继续阻断所有修改
- **WHEN** auth 非 active 或当前数据为 stale
- **THEN** 草稿与队列修改仍全部禁用并显示对应阻断原因

### Requirement: 回复配置缺失必须有可达引导

工作区 SHALL 展示 replyConfig 的 missing/draft_only/published 真态。missing 或 draft_only 时 SHALL 保留历史收件箱，显示“回复设置”入口及管理后台准确路径，依赖 published 配置的动作禁用；published 时显示版本。客户端 MUST NOT 自行构造默认模板、发布配置或调用 internal API。

#### Scenario: 配置缺失时从空错误变为可处理引导
- **WHEN** replyConfig.status=missing
- **THEN** 页面说明“先在管理后台的账号-回复设置初始化并发布”，提供可达说明入口，收取开关仍可独立使用

### Requirement: 新互动必须有 env-scoped 未读标记与去重通知

客户端 SHALL 使用 customer API 的 `unread` 字段渲染列表未读标记并更新当前环境角标。首次成功加载 SHALL 只建立基线，不为历史项弹通知；后续加载发现新的 unread messageId 时 SHALL 通过具名 IPC 发一次系统通知并按 envKey/messageId 去重。切换环境 MUST NOT 串用 seen 集合或由迟到回包更新另一环境角标。

#### Scenario: 首次打开已有历史未读不刷屏
- **WHEN** 客户首次进入环境且列表含多条 unread=true 历史项
- **THEN** 列表与角标显示未读，但不弹系统通知

#### Scenario: 后续收到一条新评论只通知一次
- **WHEN** 同一环境后续刷新首次出现新的 unread messageId，之后多次返回同一项
- **THEN** 系统通知恰好一次且环境角标保持真实计数

#### Scenario: 环境 A 的迟到响应不更新环境 B
- **WHEN** 用户从 A 切到 B 后 A 的互动列表响应才返回
- **THEN** B 的列表、角标和系统通知均不使用 A 的数据

### Requirement: 慢启动状态与开关在今日进展卡内如实呈现

客户端 SHALL 在「今日进展」摘要卡内以常驻脚注行呈现当前选中环境的慢启动状态与开关。该行 MUST NOT 位于默认收起区或会因窗口无数据而整块隐藏的容器内；慢启动允许在账号登录前按环境预先设置。

该行 MUST NOT 置于自定义标题栏内。标题栏空间与窄窗约束不变，环境级配置也不需要挤入标题区域。

`ui.snapshot` 或 env-scoped 读取的慢启动字段 SHALL 为权威环境配置；字段整体缺省仍表示未知。客户端 MUST NOT 把未知渲染为“未开启”。当投影同时包含 `binding_unknown` 与明确 `state` 时，`state` 表达环境配置，`binding_unknown` 表达当前没有账号执行对象；两者 MUST NOT 互相覆盖或被压成一个禁用态。

客户端 MUST NOT 把当前账号称为“新账号”或推断平台年龄，也 MUST NOT 暗示慢启动会使动作变慢、更像真人或改变节奏。慢启动只改变当前环境账号的每日额度上限，不进节奏系数。

#### Scenario: 字段未到时不渲染而非默认关闭

- **WHEN** 客户端尚未取得当前环境的慢启动字段
- **THEN** 该脚注行整行隐藏，MUST NOT 渲染为未勾选开关，无论经过多久

#### Scenario: 开启中显示天数与总天数

- **WHEN** 云端投影 `state=active`、`day=3`、`binding=true`
- **THEN** 客户端显示“慢启动 · 第 3/7 天”且开关为勾选态

#### Scenario: 曲线不比档位更严时如实说明

- **WHEN** 云端投影 `state=active`、`day=5`、`binding=false`
- **THEN** 客户端如实标注当前档位已更严、慢启动不额外限制
- **AND** MUST NOT 表述为正在压低配额

#### Scenario: 环境已配置但没有账号时保持开关真态

- **WHEN** 云端投影 `state=active`、`eligible=false`、`ineligibleReason=binding_unknown`
- **THEN** 客户端保持开关勾选且可操作，并说明设置属于该环境、登录账号后按曲线生效
- **AND** MUST NOT 显示为未开启、写入失败、待下发边缘或配额已被压低

#### Scenario: 毕业态显式告知而非静默消失

- **WHEN** 云端投影 `state=graduated`
- **THEN** 客户端显示已完成态并给出恢复日期，开关仍如实反映环境配置为开启
- **AND** 徽章 MUST NOT 静默消失、MUST NOT 显示为未勾选

#### Scenario: 平台或云端不适用时禁用并说明原因

- **WHEN** 云端投影 `eligible=false` 且原因为平台不支持、平台未知、客户接口未启用或云端全局停用，而非 `binding_unknown`
- **THEN** 开关禁用且按原因如实说明，MUST NOT 静默禁用

#### Scenario: 断连时降级而非清空

- **WHEN** 云端连接断开，客户端保留当前环境上一次慢启动状态
- **THEN** 客户端标注状态可能已过期并禁用开关
- **AND** MUST NOT 把停止更新渲染成已关闭或未知

#### Scenario: 开关点击不触发今日进展折叠

- **WHEN** 用户点击该脚注行内的开关或文字标签
- **THEN** 今日进展展开/收起状态保持不变，开关恰好切换一次

#### Scenario: 仅已确认冷启动时显示曲线说明

- **WHEN** 当前环境最后确认的慢启动状态为 `active` 或 `graduated`
- **THEN** 客户端显示 `?` 曲线帮助入口和常驻说明，明确设置属于当前环境、每日额度按曲线逐日放开、完成后按当前账号档位运行，且实际额度取曲线与当前账号档位中更严的一个
- **AND** MUST NOT 依赖悬浮或额外交互才能看到常驻说明

#### Scenario: 已确认非冷启动时隐藏曲线说明

- **WHEN** 当前环境最后确认的慢启动状态为 `off` 或其它运行方式已被 Cloud 确认
- **THEN** 客户端继续显示可用的慢启动选择控件，但隐藏 `?` 曲线帮助入口和曲线说明

#### Scenario: 提交期间沿用最后确认的说明可见性

- **WHEN** 开启或关闭慢启动的写入尚未取得 Cloud 写后回读
- **THEN** 曲线帮助和说明的可见性继续取最后确认状态
- **AND** MUST NOT 根据本地目标勾选值提前显示或隐藏

#### Scenario: 未知与跨环境状态不得泄漏说明

- **WHEN** 当前环境的慢启动读取中、读取失败或完整权威状态未知，或上一环境的响应晚到
- **THEN** 客户端隐藏当前环境的曲线帮助和说明
- **AND** MUST NOT 沿用另一环境的说明可见性

### Requirement: Cloud MUST NOT supply usage metrics for actions the platform cannot perform

The cloud MUST NOT supply a client-facing usage metric — neither a cap nor a total — for an action that the connected account's platform structurally cannot perform. Supplying such a metric presents the account with a plan the system can never carry out and a count that can never move, which the client renders as a cap, a percentage, a progress bar that can never advance, and a zero that will never become anything else — the fabrication this capability already forbids the client from inventing on its own.

Conversely, the cloud MUST supply the usage metric for an action that the platform declares it can perform and whose usage the risk counters already record. An action the account really performs, really spends a daily budget on, and that the operator-facing surfaces already report MUST NOT be invisible on the client-facing one: two surfaces disagreeing about the same account is itself the fabrication.

This rule is about the metric, not about the surface that carries it: it MUST hold for every usage projection the cloud supplies toward the client, whatever window it describes and whichever configuration it was read from — the daily projection, each per-window projection including the session window whose budget comes from a different, platform-blind configuration, and the receipt returned by an unrelated write.

The determination MUST come from the platform's own support declarations. Because support may be declared in either the note-scoped action matrix or the orchestration capability matrix, the projection MUST consult both; consulting only one is a defect, not a scoping choice. The mapping from each client-facing metric to the declaration that governs it MUST be stated exhaustively, so that introducing a further metric forces that mapping to be stated rather than defaulted. Support MUST NOT be encoded numerically — a cap configured to zero MUST NOT be used to mean "unsupported", and the quota configuration MUST NOT be given a platform dimension. The projection MUST NOT consult a second, display-only table of platforms or metrics: a platform's own declarations are the only admissible source.

**The projection MUST preserve today's shape whenever it cannot decide.** Only an explicit unsupported declaration may withhold a metric the client renders today; only an explicit supported declaration may introduce a metric the client does not render today. These are one rule, not two: a declaration is the only thing that may change the status quo. If the account's platform cannot be resolved, or any support lookup throws, the cloud MUST supply exactly the projection it supplied before this rule existed — nothing withheld, nothing introduced. A lookup failure MUST NOT be able to remove a supported platform's metric, and MUST NOT be able to conjure a metric for a platform that has no such concept.

The client SHALL render exactly the actions the cloud supplied, and MUST NOT render an action the cloud withheld — not as a zero, not as an empty row. A supplied total of zero is a real observation and MUST still be rendered. The client MUST NOT reintroduce a withheld action locally: neither a normalisation step that materialises a fixed set of keys, nor an optimistic increment applied on a local event, may put back an action absent from the cloud projection. The client's layout MUST NOT depend on the number of metrics being fixed. Before any cloud usage projection has arrived, the client MAY continue to render its local fallback metrics as it does today.

#### Scenario: Facebook is offered neither caps nor totals for collect or follow

- **WHEN** the cloud projects usage for a Facebook account, whose platform declares collect unsupported in the note-scoped action matrix and follow unsupported in the orchestration capability matrix
- **THEN** the supplied caps omit both collect and follow
- **AND** the supplied totals omit both collect and follow
- **AND** every other supplied metric is unchanged
- **AND** the client renders no collect metric and no follow metric at all — not a zero, not an empty row

#### Scenario: Facebook is offered the group-join metric

- **WHEN** the cloud projects usage for a Facebook account, whose platform declares group joining supported
- **THEN** the supplied totals include the group-join count and the supplied caps include its configured cap
- **AND** the client renders a group-join metric alongside the other supplied metrics

#### Scenario: Xiaohongshu is not offered the group-join metric

- **WHEN** the cloud projects usage for a Xiaohongshu account, whose platform declares group joining unsupported
- **THEN** no supplied surface carries a group-join total or cap, including the session window
- **AND** every metric Xiaohongshu is supplied today is supplied unchanged

#### Scenario: Every metric-bearing surface is covered, not just the daily one

- **WHEN** the cloud supplies usage for a Facebook account across more than one surface — the daily projection, the per-window projections including the session window whose budget comes from a different, platform-blind configuration, and the receipt returned by an unrelated settings write
- **THEN** none of them carries a metric for collect or follow
- **AND** no surface presents a metric that another surface withholds, because two surfaces disagreeing about the same account is itself the fabrication

#### Scenario: A platform that supports the action still receives its metric

- **WHEN** the cloud projects usage for an account whose platform declares every projected action supported
- **THEN** the supplied caps and totals are byte-for-byte what the configured quota tier and the counters produce

#### Scenario: Platform resolution fails while projecting usage

- **WHEN** the account's platform cannot be resolved, or a support lookup throws, while the cloud projects usage
- **THEN** the cloud supplies the full set of metrics it supplied before this rule existed
- **AND** it introduces no metric that the client does not render today
- **AND** the client is never left without usage information, and never shown a new metric, because a lookup failed

#### Scenario: Withholding is caused by a declaration, never by an ordering mistake

- **WHEN** the projection runs at any point in the assembly of a usage payload
- **THEN** it runs after the step that materialises the full set of metric keys, never before
- **AND** a withheld metric is never re-materialised as a zero and then read as a plan of zero that is already complete

#### Scenario: The client does not resurrect a withheld metric locally

- **WHEN** the cloud has withheld an action's metric, and the client then applies a local optimistic increment for some other action, or re-normalises the payload it already holds
- **THEN** the withheld action MUST NOT reappear
- **AND** the client MUST NOT briefly render it until the next cloud snapshot corrects it

#### Scenario: Withheld metrics do not block the day-completed state

- **WHEN** every action that has a supplied cap has reached it, and an action has no supplied metric at all
- **THEN** the client presents the daily plan as completed
- **AND** the completed-state wording counts only the plans that exist, because an action with no plan cannot be an incomplete plan

#### Scenario: Client renders a supplied total that has no supplied cap honestly

- **WHEN** the client receives a usage payload whose totals include an action that has no supplied cap
- **THEN** the client renders that action's total with no cap, no percentage, and no progress bar
- **AND** the client does not treat that action as a plan that can complete

### Requirement: The group-join metric reports attempts against the quota, not confirmed memberships

The client-facing group-join metric SHALL read the same counter and the same cap as the operator-facing usage surface: its numerator is the number of join attempts that reached the platform today — a click that the platform accepted, including one still awaiting an administrator's approval — and its denominator is the configured risk quota for that action. It MUST NOT be sourced from the membership ledger, and it MUST NOT be relabelled to suggest confirmed memberships.

This is the usage face, whose subject is the budget; the membership face, whose subject is which groups the account is actually in, answers a different question and continues to count only confirmed joins. The two faces disagreeing on a number is correct and expected. What is not permitted is the client and the operator surfaces disagreeing about the *same* face.

#### Scenario: A pending join shows on the usage metric

- **WHEN** the account clicks join on a group that requires approval, and the platform accepts the request but the administrator has not approved it
- **THEN** the client's group-join metric increments
- **AND** the operator-facing usage surface shows the same number for the same account
- **AND** the membership face still does not list that group as joined

#### Scenario: The metric is not restated as memberships

- **WHEN** the client renders the group-join metric
- **THEN** its label and any hover text describe joining activity measured against the daily plan
- **AND** they do not claim a number of groups the account has joined

### Requirement: 视频号收件箱采用单栏两级导航

InteractionWorkspace 的收件箱 SHALL 呈现为单栏两级结构：**列表级**只渲染互动列表；**详情级**在客户选中某条互动后，以覆盖层铺满收件箱区域并完整遮挡列表。列表 DOM MUST NOT 在覆盖层打开期间被卸载，使关闭后列表滚动位置保持不变。

覆盖层的隐藏 MUST 由显式且优先级足够的样式声明生效——面板容器自身的 `display` 声明 MUST NOT 压过隐藏声明。关闭态 SHALL 同时不渲染详情内容，MUST NOT 仅依赖样式隐藏。任一条失效都会让覆盖层永久遮挡列表且不产生任何错误，客户将无法选择任何互动。

#### Scenario: 点开一条互动后详情遮挡列表

- **WHEN** 客户在列表级点击任意一条互动
- **THEN** 详情覆盖层铺满原列表区域并完整遮挡昵称列表，消息上下文可读

#### Scenario: 关闭后列表滚动位置保留

- **WHEN** 客户滚动列表到第 N 条、点开该条后再关闭
- **THEN** 回到列表级时滚动位置仍在第 N 条附近，MUST NOT 跳回列表顶部

#### Scenario: 关闭态不残留详情内容

- **WHEN** 收件箱处于列表级
- **THEN** 详情覆盖层既不可见也不渲染其消息内容，列表全部条目均可点击

### Requirement: 收件箱 MUST NOT 默认选中互动

进入视频号工作区、切换分类标签、以及列表刷新后，收件箱 SHALL 停留在列表级且不选中任何一条互动，MUST NOT 自动选中第一条或为其预取详情。只有客户显式点击才进入详情级。

#### Scenario: 首次进入工作区为列表级空态

- **WHEN** 客户进入视频号工作区且列表加载出多条互动
- **THEN** 不选中任何一条、不请求任何详情，页面停留在列表级

#### Scenario: 切换分类标签回到列表级

- **WHEN** 客户在详情级切换到另一个分类标签
- **THEN** 收件箱回到列表级且不选中新分类下的任何一条

### Requirement: 列表条目只呈现摘要

列表条目 SHALL 只呈现头像、昵称、时间、渠道来源与状态徽章，MUST NOT 呈现消息正文预览行。消息正文与对话上下文 SHALL 只在详情级出现。昵称缺失时仍 SHALL 显示既有的诚实占位，MUST NOT 以空白或伪造昵称冒充已获取。

#### Scenario: 未获取昵称的条目仍诚实可辨

- **WHEN** 某条互动的昵称未获取到
- **THEN** 该条目显示既有占位文案与时间、来源、状态，且不显示消息预览

### Requirement: 两级切换时标签排锚定到视口顶部

打开与关闭详情时，客户端 SHALL 将分类标签排滚动锚定到视口顶部，使收件箱区域一次完整露出。锚定 SHALL 尊重系统的减弱动态偏好：偏好开启时直接定位、不做平滑滚动。

#### Scenario: 点开互动后消息区一次露全

- **WHEN** 工作区因上方概览卡与设置卡占位而使收件箱位于折线以下，客户点开一条互动
- **THEN** 页面自动滚动使标签排位于视口顶部，客户无需再手动滚动即可看到消息区

#### Scenario: 减弱动态偏好下不做平滑滚动

- **WHEN** 系统开启减弱动态偏好且客户点开或关闭详情
- **THEN** 锚定直接跳转到位，MUST NOT 播放平滑滚动动画

### Requirement: 详情级提供图标化的刷新与退回控件

详情级 SHALL 以图标按钮提供「刷新状态」与「关闭」，并在头部提供返回控件；`Esc` SHALL 等效于关闭。每个图标按钮 MUST 带可读的无障碍名称与键盘可见焦点态，MUST NOT 只靠图形传达用途。关闭 SHALL 回到列表级并清除选中。

#### Scenario: 图标按钮对读屏与键盘可用

- **WHEN** 客户以键盘遍历详情级头部
- **THEN** 刷新、关闭与返回控件均可聚焦、有可见焦点态并播报各自的可读名称

#### Scenario: Esc 退回列表级

- **WHEN** 客户在详情级按下 `Esc`
- **THEN** 收件箱回到列表级且不再选中任何一条

#### Scenario: 刷新仍是既有的诚实取数

- **WHEN** 客户点击刷新图标
- **THEN** 触发与既有「刷新状态」按钮相同的取数与真态呈现，MUST NOT 因图标化而改变其成功/失败语义

### Requirement: 灵感库空态必须区分真的空与还不知道是谁

灵感库的「什么都没有」SHALL 只在云端确认「这个账号确实零条」时呈现。当云端回报的是**账号无法确定**——该环境尚未上报过登录账号、绑定被跨客户争用、或精选存储不可用——客户端 MUST NOT 呈现「精选池还是空的 / 系统发现适合当前账号的内容后，会出现在这里」之类的空态文案。

「该环境尚未上报过登录账号」SHALL 是一等可见状态，且 MUST 自解释：它 SHALL 说明系统还不知道这个环境上登录的是哪个账号，并指出**把该环境连上云端一次**即可自行解决；MUST NOT 让运营以为需要提工单或以为功能损坏。该状态在系统上线当日是**多数环境的常态**，把它画成一次通用失败会让运营把一次正常的自愈期误报为故障。

原因文案 SHALL 遵循「只翻译已知码、未知码原样透传」：未识别的原因 MUST 原样透传，MUST NOT 被归一为空态、MUST NOT 被归一为一句无信息的通用失败。

#### Scenario: 未绑定环境不画成空池

- **WHEN** 客户在灵感库选中一个云端回报「尚未上报过登录账号」的环境
- **THEN** 界面呈现自解释的「还不知道这个环境上是谁」状态，并说明连一次云端即可解决
- **AND** MUST NOT 呈现「精选池还是空的」

#### Scenario: 真的零条仍照常呈现空态

- **WHEN** 云端成功解析出该环境的账号且该账号确实零条
- **THEN** 界面照常呈现既有的空态文案

#### Scenario: 存储不可用与空池可区分

- **WHEN** 云端回报精选存储不可用
- **THEN** 界面呈现可区分的失败态并提供重新加载
- **AND** MUST NOT 呈现空态文案

### Requirement: 慢启动开关 MUST NOT 被环境内核在线状态闸住

慢启动开关的可用性 SHALL 只取决于「客户端能否够到云端客户 API」，MUST NOT 取决于该环境内核子进程的云端链路状态、浏览器是否运行、或该环境是否已启动。

该写入经具名 IPC 直达云端客户鉴权 HTTP API、全程不经过环境内核子进程；以内核在线与否为前置 SHALL 被视为缺陷。客户端 MUST NOT 为「保持一致」而在 IPC 层或请求层新增任何浏览器 / 环境在线闸。

请求失败（含够不到云端）SHALL 复用既有的按环境隔离的失败反馈就地如实展示，MUST NOT 静默吞掉，MUST NOT 表现为开关自行弹回而无原因。

#### Scenario: 环境已停止时开关仍可点

- **WHEN** 当前选中环境处于已停止状态（内核子进程未运行、无云端链路），且该环境存在有效账号绑定
- **THEN** 慢启动开关 MUST 可点击
- **AND** 点击后 MUST 向云端客户 API 发出请求，MUST NOT 被本地拦截

#### Scenario: 浏览器关闭但内核在线时开关仍可点

- **WHEN** 当前选中环境处于冷待机（浏览器已关闭、内核与云端连接仍在）
- **THEN** 慢启动开关 MUST 可点击

#### Scenario: 够不到云端时如实说明

- **WHEN** 用户拨动开关但客户端无法够到云端客户 API
- **THEN** 客户端 MUST 就地显示可读的失败原因并恢复点击前的权威状态
- **AND** MUST NOT 显示为已生效

### Requirement: 慢启动卡 SHALL 分别标注云端真态与本机用量的新鲜度

「今日节奏」卡上有两条来源不同的数据，客户端 SHALL 分别表达其新鲜度，MUST NOT 用其中一条的陈旧去否定另一条：

- **慢启动真态**（state / day / since / binding / 当日上限）：由云端计算，写入回执当场刷新，边缘离线时**依然有效**。
- **用量计数**（今日已发生多少次动作）：由边缘上报，边缘离线时**确实陈旧**，SHALL 明确标注为可能已过期。

边缘离线 MUST NOT 被表述为慢启动状态不可信或开关不可用。慢启动真态 MUST NOT 被标注为「等待本机应用」「已保存待下发」或任何等价措辞——其执行体在云端，云端写入成功即为已生效，标注一个不存在的中间态与谎报成功同属不诚实。

#### Scenario: 离线时用量陈旧但开关真态照常呈现

- **WHEN** 当前选中环境的边缘未连接，且客户端持有该环境的慢启动真态
- **THEN** 客户端 MUST 照常呈现慢启动徽章与开关真态
- **AND** MUST 就地标注用量计数可能已过期
- **AND** MUST NOT 把整行呈现为不可用或状态不可信

#### Scenario: 离线写入成功不得标注为待应用

- **WHEN** 边缘离线时慢启动写入成功并返回写后真态
- **THEN** 客户端 MUST 呈现为已生效
- **AND** MUST NOT 显示「已保存，等待本机应用」或任何等价的二态措辞

#### Scenario: 陈旧用量 MUST NOT 被当作慢启动真态

- **WHEN** 客户端只持有该环境的陈旧用量计数
- **THEN** 客户端 MUST NOT 据此推算慢启动天数、绑定性或当日上限

### Requirement: Video-channel overview prioritizes engine and authentication over browser state

The video-channel interaction overview SHALL present environment engine connectivity and WeChat Channels authentication as the primary status pair. Browser state SHALL be presented only in a secondary manual-inspection area and an unconfirmed browser state MUST NOT visually replace or obscure the primary engine/authentication state.

The manual "打开浏览器" action SHALL remain visible for a valid selected local WeChat Channels environment regardless of the engine lifecycle state or WeChat authentication state. Its default help copy SHALL be “仅用于人工查看，引擎以上方鉴权状态为准”. The desktop action SHALL occupy a visibly larger proportional width than a content-fit button while the narrow layout SHALL remain responsive. Dynamic success copy SHALL state that browser visibility is auxiliary and that authentication remains determined by the separate WeChat status.

#### Scenario: Engine and authentication are healthy

- **WHEN** the environment engine is running and Cloud-connected and WeChat authentication is active
- **THEN** the overview shows primary success states for both "引擎" and "视频号"
- **AND** browser state and "打开浏览器" appear in the secondary manual-inspection area

#### Scenario: Browser state is unconfirmed while core states are known

- **WHEN** browser state is unconfirmed but engine connectivity and WeChat authentication have known values
- **THEN** the known engine and authentication values remain the primary status display
- **AND** browser state is labeled as an auxiliary unconfirmed report rather than the workspace's main blocker

#### Scenario: Engine is stopped or authentication needs login

- **WHEN** the selected local WeChat Channels environment's engine is stopped or its authentication is not active
- **THEN** the primary chips truthfully show those states
- **AND** "打开浏览器" remains available without enabling or starting the engine

#### Scenario: Manual inspection is idle on desktop

- **WHEN** no browser-open action notice is active and the workspace uses the desktop layout
- **THEN** the help copy is exactly “仅用于人工查看，引擎以上方鉴权状态为准”
- **AND** the browser action occupies 18% of the manual-inspection row with a usable minimum width

#### Scenario: Manual inspection is shown in a narrow window

- **WHEN** the workspace width reaches the narrow responsive breakpoint
- **THEN** the manual-inspection content and browser action stack vertically
- **AND** the browser action stretches within the available row without horizontal overflow

### Requirement: 精选详情双栏分别夹紧滚动边界

桌面客户端在精选详情的宽屏双栏布局中 SHALL 将参考图栏与稿件文字栏作为两个独立的原生纵向滚动区。指针位于任一栏时，纵向滚动 MUST 只改变该栏的滚动位置，MUST NOT 联动另一栏。任一栏到达底部或顶部后 MUST 停留在自身边界，MUST NOT 因继续滚动或另一栏的位置而产生持续扩大的空白。每栏末尾 SHALL 只保留固定且有限的舒适留白。

#### Scenario: 图片栏先到底后文字栏继续

- **WHEN** 客户在宽屏精选详情的参考图栏向下滚动并到达底部，而稿件文字栏仍有未读内容
- **THEN** 参考图栏停留在带固定小段尾部留白的底部位置，文字栏保持原滚动位置；客户在文字栏滚动时只推进文字栏

#### Scenario: 文字栏先到底后图片栏继续

- **WHEN** 客户在宽屏精选详情的稿件文字栏向下滚动并到达底部，而参考图栏仍有未浏览图片
- **THEN** 文字栏停留在带固定小段尾部留白的底部位置，参考图栏保持原滚动位置；客户在参考图栏滚动时只推进参考图栏

#### Scenario: 两栏滚动位置互不联动

- **WHEN** 两栏当前滚动位置不同且客户在其中一栏向上或向下滚动
- **THEN** 仅该栏的位置发生变化，另一栏保持原位置

#### Scenario: 已到底栏不把滚动传给另一栏

- **WHEN** 指针位于已经到底的一栏且客户继续向下滚动，另一栏仍可滚动
- **THEN** 已到底栏与另一栏都保持原位置，滚动 MUST NOT 被联动或传递；客户将指针移到另一栏后可独立继续

#### Scenario: 窄屏恢复单栏普通滚动

- **WHEN** 客户端窗口进入既有单栏响应式断点
- **THEN** 精选详情按单列文档流使用普通纵向滚动，不保留并列滚动区

### Requirement: 精选详情独立滚动区隐藏视觉滚动条

桌面客户端在宽屏精选详情中 SHALL 隐藏参考图栏与稿件文字栏的视觉滚动条轨道、滑块及预留槽，同时 MUST 保留两栏的原生独立滚动能力。系统 MUST NOT 通过 `overflow: hidden` 或脚本模拟来换取视觉隐藏；滚轮、触控板、键盘及程序化滚动行为 MUST 保持可用。

#### Scenario: 两栏可滚动但不显示灰色滚动条

- **WHEN** 宽屏精选详情的参考图栏或稿件文字栏内容超过可视高度
- **THEN** 客户可在对应栏内正常独立滚动，但界面不显示原生滚动条轨道、滑块或为其预留的窄槽

#### Scenario: 隐藏滚动条不影响独立位置

- **WHEN** 客户滚动其中一栏
- **THEN** 仅该栏滚动位置变化，另一栏保持原位置，行为与隐藏前一致

#### Scenario: 其它滚动区域不受影响

- **WHEN** 客户使用精选详情以外的列表、抽屉或日志滚动区
- **THEN** 本变更的滚动条隐藏样式不作用于这些区域

### Requirement: Electron client startup windows use a 900px default width

The Electron login window and authenticated main window SHALL each use 900px as their initial default width. Their existing minimum width, default height, minimum height, and native frame behavior SHALL remain unchanged.

#### Scenario: Client starts without a valid customer session

- **WHEN** the Electron client opens the login window
- **THEN** the login window initial width is 900px

#### Scenario: Client starts or proceeds with a valid customer session

- **WHEN** the Electron client opens the authenticated main window
- **THEN** the main window initial width is 900px

### Requirement: 精选正文与列表卡片使用分级跨平台字体排版

桌面客户端的精选详情正文内容、灵感库列表标题、正文摘要与状态标签 SHALL 使用以下有序字体回退链：`system-ui, "Apple Color Emoji", "Segoe UI Emoji", "Segoe UI Symbol", "Noto Color Emoji", -apple-system, "Segoe UI", Roboto, Ubuntu, Cantarell, "Noto Sans", sans-serif, BlinkMacSystemFont, "Helvetica Neue", Arial, "PingFang SC", "PingFang TC", "PingFang HK", "Microsoft Yahei", "Microsoft JhengHei"`。详情正文 SHALL 使用 `16px / 400`；列表标题 SHALL 使用 `16px / 700`；列表正文摘要 SHALL 使用 `14px / 400`；“可创作”等列表状态标签 SHALL 使用 `11px / 700`。列表标题 SHALL 保持单行省略，正文摘要 SHALL 保持两行截断，状态标签 SHALL 保持不收缩。该排版 MUST NOT 改变作者、话题、元信息、按钮、详情页徽标或其它内容工作区页面；详情页徽标 SHALL 继续使用 `9.5px` 字号。既有行高、换行、间距与滚动行为 SHALL 保持不变。

#### Scenario: 精选详情正文应用指定字体排版

- **WHEN** 客户打开包含文字内容的精选详情
- **THEN** 正文使用指定字体回退链、`16px` 字号与 `400` 字重显示

#### Scenario: 灵感库列表卡片形成清晰文字层级

- **WHEN** 灵感库列表卡片同时显示标题、正文摘要和“可创作”等状态标签
- **THEN** 标题使用 `16px / 700`，摘要使用 `14px / 400`，状态标签使用 `11px / 700`，且三者使用指定字体回退链

#### Scenario: 列表标题与摘要截断保持不变

- **WHEN** 灵感库列表标题或正文摘要超过可用空间
- **THEN** 标题继续单行省略，正文摘要继续按既有两行规则截断，卡片布局保持不变

#### Scenario: 详情页徽标不随列表标签放大

- **WHEN** 客户打开带状态徽标的精选详情
- **THEN** 详情页徽标继续使用既有 `9.5px` 字号，不继承列表状态标签的 `11px` 字号

#### Scenario: 字体调整不扩散到其它元素

- **WHEN** 精选详情或灵感库列表同时显示作者、话题、元信息和操作按钮
- **THEN** 本变更不改变这些元素或其它内容工作区页面的字体样式

#### Scenario: 正文滚动与换行保持不变

- **WHEN** 精选详情正文超过文字栏可视高度
- **THEN** 正文继续按既有行高和换行规则排版，文字栏继续独立滚动

### Requirement: Environment nickname double-click is a show-only browser gesture

The Electron environment rail SHALL interpret a double-click on an environment nickname as an explicit request to show that environment's driven browser. The second physical click belonging to the same double-click gesture MUST NOT advance the ordinary `select -> show -> park` phase a second time. A nickname double-click MUST NOT emit a park request, including when the environment was already selected before the gesture.

#### Scenario: Operator double-clicks an already-selected nickname

- **WHEN** the selected environment's browser is parked and the operator double-clicks its nickname
- **THEN** the companion requests that environment's browser be shown
- **AND** it emits no park request for that gesture

#### Scenario: Operator double-clicks an unselected nickname

- **WHEN** the operator double-clicks another environment's nickname
- **THEN** the companion selects that environment and requests its browser be shown
- **AND** it emits no park request for that gesture

### Requirement: 客户端稿件审核页完整呈现当前账号待审队列

客户端稿件审核页 SHALL 读取当前环境绑定账号的全部 `pending_approval` 候选稿并以服务端一致总数分页。两条及以上 MUST 使用类似灵感池的卡片列表与详情钻取；单条 MAY 直接进入详情；零条 MUST 显示真实空态。卡片 SHALL 展示封面、标题、正文摘要、更新时间与发布方式，详情 SHALL 展示完整配图、标题、正文、话题、内容版本和发布计划。账号切换 MUST 清空旧列表/详情/已处理集合并丢弃迟到响应。

#### Scenario: 多条待审稿使用卡片列表

- **WHEN** 当前账号有三条待审稿并打开稿件审核页
- **THEN** 客户端显示三张可进入详情的审核卡片，而不是只展示最新一条或隐藏其余两条

#### Scenario: 单条待审稿直接审核

- **WHEN** 当前账号仅有一条待审稿
- **THEN** 客户端可直接展示该稿详情与批准/取消操作，不要求客户先经过空洞列表页

#### Scenario: 详情返回保留列表上下文

- **WHEN** 客户从待审列表某页进入稿件详情后返回
- **THEN** 原页码与滚动位置恢复，未处理稿件仍按原账号展示

#### Scenario: 账号切换丢弃旧稿

- **WHEN** 账号 A 的待审列表或详情请求在途时切换到账号 B
- **THEN** A 的迟到响应不得渲染，B 页面不得出现 A 的标题、正文、图片、版本或发布计划

#### Scenario: 多稿中处理一条保留其余稿件

- **WHEN** 客户成功批准或取消列表中的一条稿件且仍有其它待审稿
- **THEN** 已处理稿从本次页面会话移除并回到剩余列表或下一条，不关闭整个审核工作区、不把其余稿件标为已处理

### Requirement: 发布计划在批准位置选择并诚实校验

稿件详情的批准区域 SHALL 回显 Cloud 草稿当前发布方式，并允许小红书稿件选择“立即发布 / 定时发布”。定时模式 MUST 使用北京时间分钟值，并说明当前时刻后至少 1 小时且不超过 14 天；空值或越界值 MUST 禁止批准。取消稿件 MUST NOT 依赖发布计划。提交在途时 MUST 禁止当前稿重复操作；失败 MUST 保留稿件、计划选择与真实拒因。

#### Scenario: 立即发布批准

- **WHEN** 客户选择立即发布并批准当前版本稿件
- **THEN** 客户端提交 `publishMode=immediate`、`publishTime=null` 与当前内容版本，不宣称平台已发布

#### Scenario: 定时发布批准

- **WHEN** 客户选择定时发布并输入当前北京时间后 2 小时的分钟值
- **THEN** 客户端提交 `publishMode=scheduled` 与对应 epoch ms，成功只表示该版本已批准并进入下发

#### Scenario: 非法定时时间禁止批准

- **WHEN** 定时输入为空、少于未来 1 小时或超过 14 天
- **THEN** 批准按钮不可用且不发送审批 IPC，取消按钮仍可用

#### Scenario: 审批失败保留上下文

- **WHEN** Cloud 返回版本冲突、时间失效、账号不可用或其它拒因
- **THEN** 客户端保留当前稿件与发布时间选择，展示对应失败且不将卡片移出待审列表

### Requirement: 精选详情与参考创作退出按钮返回灵感库

桌面客户端的精选正文详情标题区 SHALL 在详情滚动期间保持吸顶，并 SHALL 以单行紧凑高度只显示当前内容标题与右侧退出按钮。详情吸顶态 MUST NOT 显示左侧返回按钮、“灵感详情”类型行或作者副行。精选正文详情与“选择参考方式”页面的右侧退出按钮 SHALL 使用 `×` 图形，MUST 可见、可点击并具有“返回灵感库”的可访问名称；点击后 SHALL 返回灵感库并保留进入详情前的列表状态，MUST NOT 关闭内容工作区。“选择参考方式”页面的 `×` SHALL 跳过中间详情页直接返回灵感库，其左侧返回按钮 SHALL 继续返回当前参考内容的详情。详情标题栏 SHALL 在正常布局中占据自身高度，MUST NOT 以覆盖层遮挡参考图或正文内容。灵感库、稿件审核及其它非精选详情、非参考创作页面的关闭按钮 SHALL 继续关闭内容工作区并保留“关闭内容工作区”的可访问名称。

#### Scenario: 滚动任一详情栏时单行标题保持可见

- **WHEN** 客户在宽屏精选正文详情滚动参考图栏或稿件文字栏
- **THEN** 单行标题区保持在应用标题栏下方，仅显示当前标题和右侧 `×`，不显示左侧返回、详情类型或作者副行

#### Scenario: 点击详情退出按钮返回灵感库

- **WHEN** 客户点击精选正文详情标题右侧具有“返回灵感库”可访问名称的 `×`
- **THEN** 内容工作区保持打开并返回灵感库，进入详情前的列表状态与滚动位置得到恢复

#### Scenario: 点击参考创作退出按钮直接返回灵感库

- **WHEN** 客户从精选详情进入“选择参考方式”页面后点击右上角具有“返回灵感库”可访问名称的 `×`
- **THEN** 内容工作区保持打开、跳过正文详情并直接返回灵感库，进入详情前的列表状态与滚动位置得到恢复

#### Scenario: 参考创作左侧返回仍回详情

- **WHEN** 客户在“选择参考方式”页面点击左侧返回按钮
- **THEN** 页面返回当前参考内容的精选详情，而不是直接返回灵感库

#### Scenario: 详情标题不遮挡正文

- **WHEN** 精选正文详情处于紧凑吸顶态
- **THEN** 参考图与正文从标题栏下方开始且不被遮挡

#### Scenario: 其它页面关闭行为保持不变

- **WHEN** 客户在灵感库、稿件审核或其它非精选详情、非参考创作页面点击具有“关闭内容工作区”可访问名称的关闭按钮
- **THEN** 内容工作区按既有行为关闭

### Requirement: 灵感库按洗稿触发状态分组且隐藏列表滚动条

客户端灵感库 SHALL 提供“未创作”“已创作”和“全部”筛选，并 SHALL 默认选择“未创作”。“未创作”和“已创作”MUST 共同且不重叠地覆盖原可创作集合，即正文非空的图文内容；视频、评论和空正文内容 MUST 只出现在“全部”。一条灵感只要当前账号已经成功持久化至少一条针对它的洗稿触发任务，就 MUST 归入“已创作”，无需等待稿件生成，且后续任务失败、取消或其它终态 MUST NOT 使它回到“未创作”；只有客户端本地点击但服务端未形成任务记录时仍归入“未创作”。返回列表 SHALL 恢复进入详情前的筛选、页码和滚动位置。灵感库列表 SHALL 保持可滚动并恢复滚动位置，但 MUST NOT 显示其右侧滚动条轨道或滑块。

#### Scenario: 默认未创作筛选总数一致

- **WHEN** 客户打开灵感库或选择“未创作”
- **THEN** 服务端只统计并分页返回正文非空、图文类型且当前账号没有持久化洗稿触发任务的内容，当前页、总页数和总条数使用同一筛选条件

#### Scenario: 触发并持久化后立即成为已创作

- **WHEN** 同一可创作灵感成功发起洗稿并写入当前账号的委派任务记录
- **THEN** 该灵感出现在“已创作”且不出现在“未创作”

#### Scenario: 后续状态不改变已创作归类

- **WHEN** 某洗稿触发任务仍在排队、执行中，或后续失败、取消、完成
- **THEN** 只要该任务记录已经持久化，对应灵感仍出现在“已创作”

#### Scenario: 本地点击但服务端未受理仍是未创作

- **WHEN** 客户点击参考创作但服务端拒绝请求或未能写入任务记录
- **THEN** 对应灵感仍出现在“未创作”，不得由客户端乐观移入“已创作”

#### Scenario: 全部保留不可创作内容

- **WHEN** 客户选择“全部”
- **THEN** 服务端返回当前账号的全部精选内容，包括视频、评论、空正文、未创作和已创作图文

#### Scenario: 从详情返回恢复列表位置

- **WHEN** 客户从某一页的某条详情返回
- **THEN** 客户回到原筛选、原页码与原滚动位置，而不是被重置到未创作第一页顶部

#### Scenario: 触发后返回列表重读服务端归类

- **WHEN** 服务端已受理洗稿触发任务，客户从参考创作页返回灵感库
- **THEN** 客户端重新读取服务端列表，使该条立即从“未创作”移入“已创作”，不得保留受理前的本地旧页

#### Scenario: 隐藏滚动条但仍可滚动

- **WHEN** 灵感库内容超过列表可视高度
- **THEN** 用户仍可通过滚轮、触控板、触摸或键盘滚动列表，右侧不显示滚动条轨道或滑块

### Requirement: 客户端主体活动流与开发者日志隐藏纵向滚动条

桌面客户端 SHALL 隐藏主文档、“今天做了这些”活动流容器和“开发者详情”日志容器的纵向原生滚动条轨道与滑块，同时 MUST 保留这些区域的原生纵向滚动能力。隐藏样式 MUST 仅作用于纵向滚动条，MUST NOT 隐藏、缩窄或以其它方式改变横向滚动条；系统 MUST NOT 通过 `overflow: hidden` 或脚本模拟换取视觉隐藏。

#### Scenario: 主文档可滚动但不显示右侧竖条

- **WHEN** 客户端主体内容超过窗口可视高度
- **THEN** 客户可继续通过滚轮、触控板、键盘或程序化方式纵向滚动，窗口右侧不显示纵向滚动条轨道或滑块

#### Scenario: 活动流与开发者日志独立纵向滚动

- **WHEN** “今天做了这些”或“开发者详情”的内容超过各自可视高度
- **THEN** 对应容器保持既有高度与独立纵向滚动行为，但不显示其纵向滚动条轨道或滑块

#### Scenario: 开发者日志横向滚动条保持不变

- **WHEN** “开发者详情”中存在需要横向滚动才能查看的长日志内容
- **THEN** 横向滚动条继续按客户端原有样式显示并可操作，本变更不得隐藏或改变其高度

### Requirement: 稿件审核发布计划交互保持阅读位置

客户端稿件审核详情 SHALL 在客户切换发布模式、打开日期时间选择器或修改定时时间时保持当前审核滚动容器的阅读位置。发布计划交互 MUST NOT 重建完整稿件详情或把视口跳回顶部；标题、正文、配图及发布计划状态 SHALL 保持同一稿件上下文。该约束不得改变既有时间校验、批准按钮状态或审批提交载荷。

#### Scenario: 选择定时发布不跳回顶部

- **WHEN** 客户已滚动到稿件详情底部并选择“定时发布”
- **THEN** 日期时间控件就地出现，稿件详情节点和滚动位置保持不变，客户无需重新滚动

#### Scenario: 打开日期时间选择器不跳回顶部

- **WHEN** 客户在定时发布模式点击日期时间选择控件
- **THEN** 客户端保持审核容器原滚动位置并允许继续选择时间，不跳到稿件标题或页面顶部

#### Scenario: 时间变化仍执行既有校验

- **WHEN** 客户选择合法或非法的日期时间
- **THEN** 滚动位置保持不变，批准按钮仍按既有未来 1 小时至 14 天规则启用或禁用，提交载荷语义不变

### Requirement: 人工回复必须以一次审核发送动作表达

视频号客户工作区对 `approval_required` job SHALL 提供一次“审核并发送”主动作。存在未保存文字时，该动作 SHALL 先保存，再批准，再使用批准返回的最新 version 请求发送；任一步失败 MUST 停止后续步骤并呈现真实状态。Cloud 内部 `approved`、`queued`、`sending` 与 `sent` 状态 MUST 保持分离，客户端 MUST NOT 因批准成功就显示已发送。

#### Scenario: 审核发送完整成功
- **WHEN** 客户确认一条合法草稿且保存、批准、发送入队依次成功
- **THEN** 客户只执行一次主动作
- **AND** 客户端显示已进入发送流程而非提前显示平台成功

#### Scenario: 批准成功但发送失败
- **WHEN** 批准 API 成功而发送 API 被动态门禁拒绝
- **THEN** job 保持“已批准，尚未发送”
- **AND** 客户端显示发送拒因并允许从 approved 状态重试

### Requirement: 稿件审核配图可双击查看大图

客户端稿件审核详情 SHALL 为每张成功加载的配图缩略图提供双击查看大图能力。大图查看层 SHALL 使用原图片地址等比完整呈现当前图片，并 MUST 与当前账号、当前稿件及当前服务端配图列表保持一致；该能力 MUST NOT 改变单击、删图二次确认、审批提交、发布计划或稿件版本语义。

#### Scenario: 双击缩略图查看完整大图

- **WHEN** 客户在稿件审核详情中双击一张可用配图缩略图
- **THEN** 客户端打开模态大图查看层并以完整等比方式展示该张图片
- **AND** 单击缩略图不打开大图，既有删图入口仍只进入删图二次确认

#### Scenario: 客户主动关闭大图

- **WHEN** 大图查看层已打开，客户点击关闭按钮、点击图片外遮罩或按下 `Escape`
- **THEN** 大图查看层关闭并清理当前图片引用，稿件审核详情仍保持打开且内容与审批状态不变

#### Scenario: 审核上下文变化时不残留旧图

- **WHEN** 大图查看层已打开后客户切换稿件、关闭稿件审核、切换账号，或服务端真态已不再包含该张图片
- **THEN** 客户端关闭大图查看层并清理旧图片
- **AND** MUST NOT 在新的账号或稿件上下文中继续展示上一张图片

### Requirement: 客户端今日进展将搜索作为独立进度项

Electron SHALL 在 Cloud 为当前账号明确供给 `search` 今日用量时，以“搜索”独立进度项呈现真实次数与当前有效上限，并将其排序在“浏览”之后、点赞等互动之前。search SHALL 参与节奏详情窗口、配额饱和、休息与计划完成判断；MUST NOT 合并进浏览、评论或其他动作。

#### Scenario: Facebook 显示搜索零次和有效计划

- **WHEN** 客户端收到 Facebook 账号 `totals.search=0` 且 `quotas.search=10`
- **THEN** 今日进展在浏览之后显示“搜索 0/10”，而不是隐藏、并入浏览或显示为未知动作

#### Scenario: 搜索达到上限参与完成提示

- **WHEN** Cloud 投影某一有效窗口 `search` 已达到正数上限并标为 saturated
- **THEN** 客户端把搜索纳入该窗口完成状态，并使用“搜索”标签生成既有完成/休息语义

#### Scenario: 搜索窗口详情保持逐窗真实值

- **WHEN** session、minute、hour、day 的 search 次数或上限不同
- **THEN** 展开今日节奏后每个窗口分别显示 Cloud 提供的 search 值，不用 day alias 覆盖其他窗口

### Requirement: 搜索格对旧端和缺席字段保持加性兼容

Electron SHALL 仅渲染 Cloud 明确供给的 `search` 键。旧 Cloud 未供给 search、平台投影摘除 search 或客户 HTTP 首次读取尚未成功时，客户端 MUST 保持搜索格缺席，不得凭本机平台标签、搜索日志或缺字段补成 `0/0`；已取得的 HTTP 确认真态 SHALL 沿用既有缓存与新鲜度语义，不依赖浏览器或引擎在线。

#### Scenario: 旧 Cloud 缺少搜索键时保持既有布局

- **WHEN** Electron 收到不含 search 的旧版 dailyUsage
- **THEN** 既有指标继续显示且搜索格保持缺席，界面不报错

#### Scenario: Cloud 明确供给零次时仍显示

- **WHEN** dailyUsage 明确包含 `search=0` 和正数有效上限
- **THEN** 客户端显示搜索格，因为供给的零是真实观测而不是字段缺失

#### Scenario: 自动化停止不清空 HTTP 搜索真态

- **WHEN** 客户端已通过环境级客户鉴权 HTTP 取得 search 用量，随后浏览器或自动化停止
- **THEN** 今日进展保留该 Cloud 确认值并按既有规则标记新鲜或陈旧，不回退成本机猜测

### Requirement: 小红书内容首页 SHALL 复用当前环境生命周期控制

小红书环境价值首页中的启动、关闭和浏览器操作 SHALL 委托现有当前环境生命周期控件与状态源。环境关闭时，首页启动按钮 SHALL 明确可用，浏览器控件 SHALL 按现有登录/检查能力如实禁用或呈现；环境启动后控件、首页文案和工作状态 SHALL 同步。价值首页 MUST NOT 建立第二套 running 状态或自行假定启动成功。

#### Scenario: 从环境价值首页启动环境
- **WHEN** 环境已关闭且客户点击价值首页“启动当前环境”
- **THEN** 客户端触发现有真实启动按钮的同一动作链，只有权威状态变为运行后才更新为运行中并恢复允许的浏览器控制

#### Scenario: 关闭环境需要确认
- **WHEN** 当前环境正在运行且客户从价值首页请求关闭
- **THEN** 客户端使用现有环境关闭确认与当前 envId，确认前不关闭，且不得影响其它环境

### Requirement: 首次用户引导 SHALL 指向真实启动按钮

首个真实环境完成创建并进入权威花名册后，若当前环境动作明确为 start，客户端 SHALL 在真实启动按钮旁显示一次性说明和有限光环。客户必须点击真实启动按钮才完成启动；引导按钮 MUST NOT 模拟成功或代替生命周期动作。点击启动、切换环境、权威状态变化、主动关闭或稍后处理 SHALL 清除本次引导。

#### Scenario: 首个环境创建后点击真实启动
- **WHEN** 新用户创建首个环境并在提示下点击真实启动按钮
- **THEN** 提示立即结束，客户端走正常启动链并等待真实回执，不在提示层伪造运行状态

#### Scenario: 用户稍后再说
- **WHEN** 用户关闭一次性引导
- **THEN** 环境保持未启动，真实启动按钮仍可随时使用，其它内容读取不被阻断

### Requirement: 内容首页 SHALL 在主窗口尺寸内无横向溢出

小红书环境价值首页、工作面板、账号排期、启动引导、按钮组、精选卡和稿件调整器 SHALL 在环境主内容区的支持宽度内换行或堆叠，不得撑出应用壳或环境栏。顶部工作面板桌面态含 padding 与边框 MUST 不超过 255px，完成消息图标与字体 SHALL 保持一致尺寸。

#### Scenario: 窄主窗口查看环境价值首页
- **WHEN** 主窗口缩窄到客户端支持的最小内容宽度
- **THEN** 控件换行或分栏堆叠，页面无横向滚动，账号排期、工作过程文字、状态图标和操作按钮均可见可操作

#### Scenario: 环境栏压缩了首页实际宽度
- **WHEN** Electron 窗口仍满足桌面媒体查询但环境栏和外层布局使价值首页容器进入中等宽度
- **THEN** 首页依据自身容器而不是窗口宽度调整分栏，标题、摘要、赞藏证据和按钮保持客户可读尺寸且空态不留下失衡的大块空白

### Requirement: Selected Facebook environment shows an explicit compact restricted recovery row

The Electron companion SHALL render authoritative risk state in the selected environment's context. A selected Facebook environment in `restricted` SHALL be labeled `账号受限` in the title health result, risk detail, and environment rail, and SHALL show one compact row below the existing “今日进展” controls containing only one `解除受限` action button, one `?` help trigger, and inline failure feedback when needed. The UI MUST NOT duplicate the status label inside this row, add a large recovery card, or show the action for `normal`, `warned`, `frozen`, non-Facebook, or unknown risk state.

For a live environment the displayed state SHALL follow the live Cloud snapshot. For a stopped or disconnected environment the client SHALL obtain a fresh customer-auth environment-scoped risk read; it MUST NOT trust a locally initialized `normal` fallback, merge state across environments, or turn a failed read into a normal display.

When the effective state is `restricted`, that state SHALL override the generic `session=resting` presence fallback. The companion MUST NOT describe a risk-triggered pause as a completed browse round or promise the normal automatic-resume countdown.

#### Scenario: Stopped restricted Facebook environment remains visibly restricted
- **WHEN** the selected Facebook environment is stopped and its environment-scoped Cloud read returns `restricted`
- **THEN** the companion shows `账号受限` and the compact recovery row for that environment
- **AND** switching to another environment does not carry the state or button across

#### Scenario: Other states and platforms do not show the action
- **WHEN** the selected environment is not Facebook or its authoritative state is `normal`, `warned`, `frozen`, or unknown
- **THEN** the compact recovery row is hidden

#### Scenario: Risk-triggered standby is not presented as completed work
- **WHEN** the selected environment is `restricted`, its session projection is `resting`, and browse progress is still below quota
- **THEN** the presence headline says automatic operation is paused because the account is restricted
- **AND** it does not say the round completed or show the normal auto-resume countdown

#### Scenario: Restricted wording is explicit
- **WHEN** an environment is `restricted`
- **THEN** health, risk detail, and rail use `账号受限`
- **AND** they MUST NOT weaken the state to `节奏已调整` or `已调整节奏`

### Requirement: Recovery interaction reports Cloud write-after truth

Clicking `解除受限` SHALL first show a compact application-owned modal, not a native browser/system confirmation. The modal SHALL identify the selected environment, ask the customer to verify Facebook is usable, and state that the action only resumes AIDCP automation rather than proving Facebook's own block is cleared. After confirmation, the renderer SHALL call a named preload/main IPC with only the selected environment key. The client MUST NOT send an account identifier, risk signal selector, target status, audit reason, or command outcome.

While the initial request is pending, the same button SHALL be disabled. A `200` response SHALL be treated as success only when it contains the same `envKey` and automation's write-after `normal` state. A `202` response SHALL keep the environment visibly `restricted`, retain a pending state scoped to the exact `envKey + commandId`, and poll that command through the customer-auth environment-scoped result boundary. The client MUST NOT resubmit recovery merely because the initial response was `202`, locally clear `restricted`, synthesize `normal`, or claim that Edge resumed before Cloud returns an `applied` receipt.

While polling, `processing` SHALL keep the action disabled and preserve the last authoritative risk state. Only an `applied` result for the same selected environment and command, carrying write-after `normal`, SHALL clear the restricted presentation and consume the real resumed-edge count. A response for another environment or command MUST be discarded. Switching environments MUST NOT carry a pending command, result, status, or failure message into the newly selected environment.

`refused`, `failed`, and `unknown` SHALL have distinct customer-readable failure states. None of them may clear `restricted` locally or display recovery success. A terminal non-applied result or transport failure SHALL stop the pending presentation and make the action usable again when the environment's latest authoritative state still permits recovery; any subsequent status change SHALL come from a fresh Cloud risk-state response, not from inference based on the command outcome.

The `?` help panel SHALL explain that Facebook security checks, captcha evidence, or explicit throttle signals can pause automation; the customer should first confirm the account works; and a still-present platform block can stop work again. The UI MUST NOT claim that pressing the button solved the Facebook checkpoint or captcha itself.

#### Scenario: Confirmed recovery updates only the current environment
- **WHEN** the customer confirms recovery and Cloud returns `200` for the same `envKey` with automation's write-after `normal`
- **THEN** the button remains pending until that response and the restricted row then disappears for that environment
- **AND** other environments remain unchanged

#### Scenario: Accepted asynchronous recovery remains visibly pending
- **WHEN** the initial recovery request returns `202` with the same `envKey`, a `commandId`, and `processing`
- **THEN** the client keeps `账号受限` visible, keeps the recovery action disabled, and polls that exact command through the same environment
- **AND** it does not issue another recovery submission or present acceptance as success

#### Scenario: Polling completes with applied write-after truth
- **WHEN** polling later returns `applied` for the same environment and command with write-after `normal`
- **THEN** the client consumes that authoritative state, ends pending, removes the restricted row, and may display the returned real resumed-edge count
- **AND** it does not derive success from elapsed time, a local timer, or an earlier `202`

#### Scenario: Processing does not clear restricted state
- **WHEN** a recovery result poll continues to return `processing`
- **THEN** the selected environment remains visibly `账号受限` and the action remains pending
- **AND** the client does not replace the last authoritative state with `normal`, an empty state, or a generic success

#### Scenario: Refused, failed, and unknown remain distinct
- **WHEN** the result endpoint returns `refused`, `failed`, or `unknown`
- **THEN** the client ends the pending presentation and shows outcome-specific inline feedback rather than one generic success or endless processing state
- **AND** it does not locally clear `restricted` or claim that Edge resumed

#### Scenario: A stale result cannot update another environment
- **WHEN** the selected environment changes or a response carries a different `envKey` or `commandId` while recovery is pending
- **THEN** the renderer discards that response for the current view and does not change the current environment's risk state, button, or message

#### Scenario: Cancel does not call Cloud
- **WHEN** the customer clicks `暂不解除`, closes the modal, or presses Escape
- **THEN** no recovery IPC is sent and the restricted row remains unchanged

#### Scenario: Confirmation stays scoped to the environment shown
- **WHEN** the selected environment or its authoritative risk state changes while the modal is open
- **THEN** confirming the stale modal sends no recovery IPC
- **AND** the UI re-renders from the current environment's truth

#### Scenario: Recovery transport failure remains honest
- **WHEN** Cloud cannot be reached during submission or result polling
- **THEN** the environment remains at its last authoritative risk state, the pending presentation ends, and the action becomes usable again when recovery is still permitted
- **AND** an inline failure is shown without claiming that recovery or Edge resume occurred

### Requirement: Facebook Feed-video presentations appear exactly once in the activity stream

When Edge reports an ordinary Facebook Feed batch containing exactly one `isVideo:true` card with a canonical non-Reel Facebook post identity, the client SHALL add exactly one “读” activity for that presented video. The activity SHALL use truthful “看了” wording with the reported caption and author when present, MUST use a bounded generic fallback when metadata is absent, and MUST NOT expose a URL, noteId, or other machine identifier. The event MAY add one immediate local fallback view, but Cloud customer-auth `dailyUsage` SHALL remain the authoritative total.

The client MUST deduplicate the activity by canonical post identity for the active session. A repeated cards batch or later detail report for an already-projected Feed video SHALL continue through the existing Cloud data path but MUST NOT add another read activity or local fallback view. Non-video, empty, multi-video, malformed-identity, and Reel-shaped Feed batches MUST NOT produce this activity.

#### Scenario: Strict Feed video produces one readable activity

- **WHEN** Edge reports one ordinary Feed video with a canonical post identity, caption, and author
- **THEN** “今天做了这些” adds one “读” activity using the actual caption and author
- **AND** the local fallback view increases once until Cloud refreshes the authoritative total

#### Scenario: Missing metadata uses a safe generic fallback

- **WHEN** an otherwise valid Feed-video presentation lacks caption and author metadata
- **THEN** the activity uses bounded generic “看了一个视频” wording
- **AND** it exposes no URL, post id, or other machine identifier

#### Scenario: Duplicate presentation and later detail remain idempotent

- **WHEN** the same canonical Feed video is reported again or later produces `note.detail` in the same active session
- **THEN** the Cloud cards/detail data continues through its existing path
- **AND** the client adds no second read activity and no second local fallback view

#### Scenario: Unqualified Feed batches remain silent

- **WHEN** a Feed batch has zero or multiple video cards, lacks a canonical post identity, is non-video, or carries a Reel-shaped identity
- **THEN** the client emits no Feed-video read activity and adds no local fallback view

#### Scenario: Feed video uses the existing read marker

- **WHEN** a `feed_video_view` activity reaches the renderer
- **THEN** the activity stream displays the existing “读” marker rather than a generic system marker

### Requirement: 开发者详情展示安全且阶段诚实的引擎命令诊断

客户端 SHALL 在“开发者详情”中为当前环境展示 Cloud 主动下发到 Edge 的命令诊断。每条诊断 SHALL 包含接收时间、命令类型、当前可证明阶段、安全摘要和短关联标识，并 MUST 明确区分已收到、已拒绝、已交给执行器及 Edge 接收层能够直接观测的步骤结果。`received` 或 `dispatched` MUST NOT 被表述为命令已经执行成功、业务已经完成或平台已经确认。

命令摘要 MUST 由逐命令字段白名单生成。`facebook.reels.scroll{reason:'facebook_reels_primary'}` 与 `facebook.reels.scroll{reason:'empty_feed_reels_fallback'}` SHALL 使用“进入 Reels”命令名称，并分别使用固定的主入口或 Feed 结束回退摘要；其它滚动命令（`{platform}.{feed|search}.scroll` 及不携 Reels 入口 reason 的 `facebook.reels.scroll`）SHALL 保留“页面滚动 / 滚动当前页面”。正文、标题、评论、私信、搜索词、群聊码、Cookie、Token、二维码、截图内容、完整 URL、浏览器调试地址、账号身份字段、任务永久键和原始 payload MUST NOT 进入命令诊断事件、renderer 状态或可见诊断行。文本字段只可展示有界字符数，URL 只可展示是否存在，安全枚举和有界计数可按需展示。未知命令或新增 payload 字段 MUST 默认不展示内容。

诊断 SHALL 仅保存在 Edge 本机内存中，按环境隔离并具有数量与时间双重上限；它 MUST NOT 进入普通活动流、Cloud 数据库或自动化回执。旧客户端状态缺少诊断字段时界面 MUST null-safe 降级。

#### Scenario: 已登记命令显示接收与交付边界

- **WHEN** 当前环境收到一条已登记、通过校验且存在本地处理器的主动命令
- **THEN** 开发者详情出现该命令，并将阶段更新为“已交给执行器”
- **AND** 界面明确该阶段不表示执行成功或平台确认

#### Scenario: Reels 主入口显示导航意图

- **WHEN** Edge 收到 `facebook.reels.scroll{reason:'facebook_reels_primary'}`
- **THEN** 开发者详情显示“进入 Reels”及固定的主浏览入口摘要
- **AND** 阶段仍只显示 Edge 已收到或已交付的事实，不宣称已经进入 Reels

#### Scenario: Feed 结束回退显示导航意图

- **WHEN** Edge 收到 `facebook.reels.scroll{reason:'empty_feed_reels_fallback'}`
- **THEN** 开发者详情显示“进入 Reels”及固定的 Feed 结束回退摘要
- **AND** 不把该命令显示为普通页面滚动

#### Scenario: 普通页面滚动保留原文案

- **WHEN** 滚动命令（`{platform}.{feed|search}.scroll` / `facebook.reels.scroll`）不携带任一 Reels 入口 reason
- **THEN** 开发者详情继续显示“页面滚动 / 滚动当前页面”

#### Scenario: 非法或未协商命令诚实显示拒绝

- **WHEN** Edge 收到未登记、能力未协商、payload 非法或没有本地处理器的主动命令
- **THEN** 诊断阶段显示“已拒绝”及固定安全原因，不显示已执行或成功
- **AND** 诊断行为不得改变原有 fail-closed 路由结果

#### Scenario: 只有可直接观测的步骤才显示结果

- **WHEN** `plan.response` 的顺序步骤在 EdgeClient 内完成并得到逐步结果
- **THEN** 对应诊断可更新为“步骤已完成”或“步骤失败”
- **AND** 该结果不得表述为整项业务完成或平台结果已确认

#### Scenario: 异步处理器不猜测终态

- **WHEN** 命令已经交给一个返回 `void` 或自行异步执行的业务处理器
- **THEN** 诊断停留在“已交给执行器”，直到未来有显式结果事件
- **AND** 客户端不得依据交付动作自行补造成功或失败

#### Scenario: 敏感 payload 只产生白名单摘要

- **WHEN** 评论、回复、发布、搜索、验证码或导航命令携带文本、账号标识、任务键、图片、坐标或完整 URL
- **THEN** 命令诊断只展示固定动作说明、允许的枚举、有界数量或文本字符数
- **AND** renderer 状态和可见诊断行中不存在上述原始内容或完整 payload

#### Scenario: 多环境命令诊断不串号

- **WHEN** 环境 A 与环境 B 同时收到不同命令且用户在二者之间切换
- **THEN** 开发者详情只展示当前选中环境的命令诊断
- **AND** 每个环境分别执行最多 50 条且最长 30 分钟的保留规则

#### Scenario: 普通活动流不展示接收噪声

- **WHEN** Edge 收到、拒绝或交付一条引擎命令
- **THEN** 该接收诊断只出现在开发者详情
- **AND** “今天做了这些”不得因此新增一条动作成功、失败或处理中记录

### Requirement: 首页状态卡统一层级并保持平台能力真实

Electron 首页的“今日进展”和“内容发布” SHALL 在小红书与 Facebook 环境中使用一致的客户级表面、内层内容卡、状态标签、间距、悬停、键盘焦点和窄窗口响应式语言。视觉一致 MUST NOT 被解释为功能等同：今日进展的可见指标 SHALL 继续完全由当前环境的权威平台投影决定；Facebook 慢启动脚注 SHALL 只在其既有真实条件下显示；平台切换 MUST 清除上一平台的视觉修饰、文案和操作入口。

#### Scenario: Facebook 今日进展使用共享视觉但保留真实指标
- **WHEN** 客户选择一个 Cloud 投影为 Facebook 的环境
- **THEN** 今日进展 SHALL 使用共享卡片层级并只呈现该投影实际提供的 Facebook 指标，MUST NOT 补画小红书收藏等不存在的指标
- **AND** Facebook 慢启动脚注仍 SHALL 按既有环境级真态显示

#### Scenario: 切换平台不残留前一平台状态
- **WHEN** 客户在小红书与 Facebook 环境之间切换
- **THEN** 今日进展与内容发布 SHALL 立即切换到当前平台的表面修饰、文案与可用操作，MUST NOT 残留前一平台的 class、队列导航或指标格

### Requirement: Facebook 内容发布卡使用单稿语义而非小红书队列语义

Facebook 环境的内容发布卡 SHALL 使用与小红书队列卡一致的视觉层级，但 MUST 只投影当前环境既有的单稿 `publish / lastPublish / publishPreview` 真态。其阶段 SHALL 表达“准备内容、发布审批、提交平台、发布结果”，并按 pending/reminded、approved、submitted、published 等既有状态推进；页面 MUST NOT 显示小红书队列数量、左右切稿、“查看全部进度”或定时发布能力。稿件查看入口 SHALL 仅在既有可审批稿件能力判定为可用时出现，并继续调用既有审批链路。

#### Scenario: Facebook 待审批内容显示单稿状态
- **WHEN** 当前 Facebook 环境有一条 `pending` 或 `reminded` 稿件且稿件预览可用
- **THEN** 内容发布卡 SHALL 显示 Facebook 单稿的待审批状态和“查看内容”入口
- **AND** “发布审批”为当前阶段，“提交平台”和“发布结果”为未完成阶段
- **AND** 队列数量、左右切稿和“查看全部进度” MUST NOT 出现

#### Scenario: Facebook 已审批内容等待提交
- **WHEN** 当前 Facebook 环境的稿件状态为 `approved`
- **THEN** 内容发布卡 SHALL 将“准备内容”和“发布审批”显示为已完成，将“提交平台”显示为当前阶段，并以无需重复操作的真实文案说明后续处理

#### Scenario: Facebook 已提交但结果未确认
- **WHEN** 当前 Facebook 环境的稿件状态为 `submitted`
- **THEN** 内容发布卡 SHALL 显示已提交 Facebook、正在确认公开结果，MUST NOT 将其显示为已发布

#### Scenario: Facebook 空态和窄窗口保持可读
- **WHEN** 当前 Facebook 环境没有进行中稿件和发布历史，或窗口宽度不超过 430px
- **THEN** 空态 SHALL 继续按既有规则默认收起并可展开，展开后的平台文案与阶段语义 SHALL 保持正确
- **AND** 窄窗口中阶段、脚注与合法操作 MUST NOT 横向溢出或被左右轮播控件遮挡

### Requirement: 发布卡显式展示已提交但公开结果未确认

Electron 陪伴界面收到当前环境的 `publish.state = submitted` 时 SHALL 将本次发布显示为独立的“已提交，平台确认中”卡片状态，并 SHALL 以本次稿件的标题、编号与提交时间覆盖发布卡主体；即使同一环境仍保存更早的 `lastPublish`，旧历史也 MUST NOT 盖住本次提交。该状态 MUST NOT 使用“已发布”文案，MUST NOT 把公开结果未确认的稿件写入已发布历史，并 MUST 保留真实 `lastPublish` 供后续失败回退或已确认发布替换。

#### Scenario: 新提交优先于旧的上次发布

- **WHEN** 当前环境已有一条历史 `lastPublish`，随后收到标题、编号和时间齐全的 `publish.state = submitted`
- **THEN** 发布卡自动展开并显示本次稿件及“已提交，平台确认中”，不继续把旧稿标题作为卡片主体
- **AND** 卡片 MUST NOT 显示“已发布”或把四个旅程节点全部标为完成

#### Scenario: 没有历史发布时仍展示提交真态

- **WHEN** 当前环境没有 `lastPublish`，但收到 `publish.state = submitted`
- **THEN** 发布卡显示本次提交而非“还没有发布过内容”空态
- **AND** 文案说明发布请求已经提交、公开结果仍待确认且无需用户重复操作

#### Scenario: 公开结果确认后转为上次发布

- **WHEN** 同一稿件在 `submitted` 后收到 `publish.state = published`
- **THEN** 发布卡按既有逻辑转为“上次发布”并以该稿件更新历史态
- **AND** 只有此时卡片才显示“已发布”并将四个旅程节点全部标为完成

#### Scenario: 新版客户端重启后从客户 HTTP 数据面恢复提交真态

- **GIVEN** 客户端支持 `client_data_plane_automation_engine_v1`，同一环境的云端发布记录仍为 `submitted`，且本地只保存更早的 `lastPublish`
- **WHEN** 客户端登录、重启或重新选择该环境
- **THEN** Electron SHALL 通过 customer-auth HTTP 的环境级只读概览恢复当前提交与真实最近发布摘要
- **AND** 卡片 SHALL 在 HTTP 结果到达后显示当前 `submitted` 稿件，不得继续以本地旧 `lastPublish` 作为当前主体
- **AND** Renderer、HTTP 请求或响应 MUST NOT 接受或暴露 Cloud `accountId`

#### Scenario: 云端概览尚未确认时不冒充旧状态

- **WHEN** 新版客户端首次读取环境概览仍在进行或失败
- **THEN** 发布卡 SHALL 显示读取中或暂时不可用，不得把本地旧历史当作已确认的当前云端状态
- **AND** 已有一次成功概览后刷新失败时 MAY 保留上次确认值，但 SHALL 明确标识为缓存或陈旧数据并有界重试

### Requirement: XHS publish home surface SHALL summarize the current environment queue

Electron 陪伴界面 SHALL 在明确的小红书环境中把原单记录发布区域呈现为“发布进度”摘要。摘要 SHALL 优先展示等待客户确认的内容，并提供进入完整发布队列的入口；仅有系统处理中内容时 SHALL 保持紧凑，无活跃内容时 SHALL 展示最近真实发布或“暂无进行中”。既有稿件审核入口、发布/取消和版本安全语义 MUST 保持不变。

#### Scenario: 待确认稿件自动突出

- **WHEN** 当前环境队列含至少一条 waiting approval 内容
- **THEN** 首页摘要自动展开最需要处理的一条，显示“确认前不会发布”并提供现有稿件审核入口

#### Scenario: 只有系统处理中的内容

- **WHEN** 当前环境只有 queued、generating 或 submitted 内容且无需客户操作
- **THEN** 首页显示紧凑数量摘要和“查看全部”，不为每条内容占据运行首页空间

### Requirement: Home status surfaces SHALL prioritize today progress before publish content

Electron 运行首页 SHALL 在 DOM 与视觉顺序中将完整“今日进展”卡放在内容发布卡之前。实现 MUST 保持今日进展的环境控制、展开状态与指标节点完整，保持发布卡的折叠、轮播、审核和队列入口完整，并且 MUST NOT 通过仅改变 CSS 视觉顺序造成辅助技术或键盘顺序不一致。

#### Scenario: 今日进展与待发布卡同时出现

- **WHEN** 当前环境同时展示今日进展和展开或收起的内容发布卡
- **THEN** 用户先阅读和操作今日进展，再到内容发布卡；“今天做了这些”活动流继续位于两张卡之后

### Requirement: Expanded publish summary SHALL support restrained item switching

Electron 展开态发布摘要 SHALL 在当前环境可展示项超过一条时，提供位于卡片最左和最右的上一条、下一条按钮，并显示当前位置与总数。按钮 SHALL 默认使用弱化颜色，在 hover 与 `focus-visible` 时轻度加深；按钮 SHALL 是原生键盘可达控件并以目标内容标题提供可访问名称。单条、加载、错误与收起态 MUST 隐藏并禁用切换控件。

切换序列 SHALL 先展示待确认 active，再展示其它 active 与尚未开跑 tasks；无进行中内容时 MAY 在 recent 内切换。左右边界 SHALL 循环。HTTP 刷新后若当前稳定身份仍存在 SHALL 保持当前项，消失时 SHALL 回到新的首项；切换环境或平台 MUST 清除选择。切换 MUST NOT 发送写请求、改变任务顺序、跨环境复用索引，或把展示位置描述成精确队列名次。

#### Scenario: 鼠标或键盘切换到下一稿件

- **WHEN** 客户点击右侧按钮，或在该原生按钮上按 Enter / Space
- **THEN** 卡片更新为下一条内容，位置提示与按钮可访问名称同步更新，完整队列和 Cloud 状态保持不变

#### Scenario: 当前稿件在刷新后仍存在

- **WHEN** 客户正在查看第二条内容且 HTTP 刷新仍返回同一稳定身份，即使列表位置改变
- **THEN** 卡片继续展示该内容，不因刷新跳回首项；若该身份消失才回到新的首项

#### Scenario: 切换环境或只剩一条内容

- **WHEN** 客户切换账号、平台，或刷新后当前环境只剩一条可展示内容
- **THEN** 客户端清除旧选择，隐藏且禁用左右按钮，不保留可聚焦的不可见控件

### Requirement: Expanded publish summary SHALL reuse the full queue visual hierarchy

Electron 的 XHS 展开态发布摘要 SHALL 使用与完整发布队列一致的状态徽标、白底细边任务卡、紧凑四阶段轨道和主次按钮层级。摘要 MUST NOT 使用没有真实稿件图片证据的装饰封面。每个有 Cloud 阶段证据的步骤 SHALL 同时显示阶段标签与客户状态文字；尚未开跑的 task SHALL 显示未开始，不得伪造阶段进度。

“查看全部进度” SHALL 是次级原生按钮。“审核稿件” SHALL 是主按钮，且只在当前轮播项自身为 waiting approval 并且审核能力可用时展示。说明文字与操作按钮 SHALL 分区布局。左右切换控件 MUST 留在外层边缘并且不遮挡标题、步骤或操作；窄窗口 SHALL 使用纵向阶段轨道且无横向溢出。非 XHS 与旧单稿回退 MUST NOT 继承 XHS 队列摘要样式。

#### Scenario: 当前轮播项是待确认稿

- **WHEN** 当前 XHS 展开态摘要选中 waiting approval journey
- **THEN** 内层任务卡显示等待确认徽标、稿件标题、四阶段标签与状态，操作区显示次级“查看全部进度”和主按钮“审核稿件”，且不显示装饰封面

#### Scenario: 切换到创作中或排队任务

- **WHEN** 客户从待确认稿切换到 generating journey 或 queued task
- **THEN** 标题、状态徽标与阶段文字同步切换；审核主按钮隐藏，完整队列次级入口保留，queued task 的四阶段均显示未开始

#### Scenario: 窄窗口查看重构后的摘要

- **WHEN** XHS 发布摘要在 430px 或更窄的可用宽度展开
- **THEN** 当前任务信息、纵向四阶段状态、说明与操作按钮完整可读，左右切换不遮挡内容且页面无横向溢出

### Requirement: Publish queue SHALL reuse the in-app content workspace safely

Electron SHALL 在现有主窗口内容工作区页面栈内展示发布队列，不创建新的系统窗口。关闭 SHALL 返回运行首页；打开稿件审核后返回 SHALL 回到队列。环境切换 SHALL 清除取消确认、忙态和旧内容；旧环境迟到回包 MUST NOT 重新打开或覆盖新环境页面。

#### Scenario: 从队列进入稿件审核再返回

- **WHEN** 客户从等待确认的队列项打开稿件审核并完成查看后返回
- **THEN** 客户回到同一环境发布队列且不丢失当前分区

#### Scenario: 取消确认中切换环境

- **WHEN** 客户正在确认取消环境 A 的任务时切换到环境 B
- **THEN** 确认态立即关闭，任何 A 的在途回包不得修改 B 的队列或显示成功提示

### Requirement: Renderer SHALL use narrow publish queue IPC only

Renderer SHALL 只通过 preload 暴露的发布队列读取与取消方法操作当前本地 `envId`。Electron main SHALL 解析真实 envKey、持有客户令牌并构造固定路径；renderer MUST NOT 直接访问 customer-auth HTTP、传入任意 URL/鉴权头/`accountId`，或在取消时省略 task version。

#### Scenario: Renderer 发起取消

- **WHEN** 客户确认取消当前队列中的任务
- **THEN** renderer 只向 preload 提交当前 envId、任务 id 与整数 version，main 将其绑定到该环境的固定客户取消路径

### Requirement: Publish progress rail SHALL read as one connected, non-interactive sequence

发布队列的四阶段步骤条 SHALL 在宽屏将节点和文案按同一四列对齐，并只在相邻圆点外缘之间绘制连接线。第一节点之前与最后节点之后 MUST NOT 出现线段，连接线 MUST NOT 穿过圆点或阶段文案。窄屏 SHALL 改为等价的纵向连接，保持阶段顺序与状态文字可读。步骤项只表达状态，MUST NOT 使用 hover、手型光标或点击反馈暗示可操作性。

#### Scenario: 已确认稿件等待发布

- **WHEN** 前三阶段完成而发布结果尚未开始
- **THEN** 第三个圆点与第四个圆点之间显示已推进连接，第四个圆点保持待处理样式，轨道首尾无悬空短线且文字不遮挡线段

#### Scenario: 窄屏查看四阶段

- **WHEN** 客户在窄屏窗口查看同一任务
- **THEN** 四阶段按从上到下排列，连接线只连接相邻圆点，完整标签与状态文字换行可读且页面无横向溢出

### Requirement: 终态自动化失败必须同时保留重试与关闭入口

Electron 伴随窗口在本机自动化意图仍为启动、但引擎已因终态启动失败退出时，SHALL 如实显示失败详情，并同时提供“重试启动”和“关闭自动化”两个可区分动作。“关闭自动化”MUST 结束本机自动化意图、取消本机排队或重试并清除该轮失败；MUST NOT 被路由成打开浏览器、重新登录或其他隐式重试。

#### Scenario: AdsPower 占用终态可关闭本机自动化

- **WHEN** AdsPower 启动被其他设备或窗口占用拒绝，引擎已退出且自动化状态为终态错误
- **THEN** 客户端 SHALL 显示“启动”用于显式重试，并显示“关闭”用于结束本机自动化
- **AND** 点击“关闭” SHALL 调用单环境自动化关闭动作，MUST NOT 调用浏览器打开动作

#### Scenario: 已停止环境仍保留浏览器辅助动作

- **WHEN** 环境的本机自动化意图已经为停止且没有终态错误
- **THEN** 主动作 SHALL 保持“启动”，次动作 MAY 保持既有“浏览器”登录/检查入口
- **AND** MUST NOT 把普通停止态误呈现为仍需关闭的自动化任务

#### Scenario: 关闭失败终态不牵连其他环境

- **WHEN** 操作者关闭某一个终态错误环境的本机自动化
- **THEN** 只有该环境的启动意图和失败详情 SHALL 收敛
- **AND** 其他环境的引擎、浏览器与运行状态 MUST NOT 受影响

#### Scenario: 外部占用关闭文案不冒充远端浏览器已关

- **WHEN** 启动因外部占用被拒后，操作者关闭本机自动化
- **THEN** 客户端 SHALL 显示本机自动化已关闭且占用端会话未受影响
- **AND** MUST NOT 用无范围的“已关闭浏览器”覆盖该结论

### Requirement: Facebook Reel follows appear truthfully in activity and today's progress

When Cloud supplies `dailyUsage.follow` for a Facebook account, the client SHALL render the follow total, applicable quota, saturation, and window progress in the existing “今日进展” surface exactly as it renders other supplied actions. The client MUST NOT hide the follow row merely because the selected platform is Facebook. A newly verified Reel follow SHALL also emit one structured local follow activity with one fallback `follows` increment; Cloud daily usage SHALL remain the authoritative total when refreshed.

#### Scenario: Cloud supplies Facebook follow usage
- **WHEN** a Facebook environment receives daily usage with `follow` totals and quotas
- **THEN** “今日进展” displays the 关注 item and its real total/quota/window values
- **AND** the unsupported Facebook 收藏 item remains absent

#### Scenario: New Reel follow is immediately visible
- **WHEN** the Facebook Reel executor reports `ok:true` for a newly verified follow
- **THEN** the activity stream adds one human-readable Reel follow entry with a distinct 关注 marker
- **AND** the local fallback follow total increments once until Cloud refreshes the authoritative total

#### Scenario: No-op and failure do not look successful
- **WHEN** a Reel follow returns `already_followed`, shadow, no-target, ambiguous-target, state-unchanged, verify-indeterminate, or another failure
- **THEN** the client adds neither a successful follow activity nor a follow fallback increment

#### Scenario: Edge version lacks Reel follow activity support
- **WHEN** Cloud daily usage includes Facebook follow but the installed Edge predates structured Reel follow events
- **THEN** the existing generic daily-usage renderer still displays the authoritative follow total
- **AND** Cloud does not send automatic follow commands unless that Edge declared `facebook_reel_follow_v1`

### Requirement: 桌面灵感库 SHALL 展示来源发布时间而非精选更新时间

桌面灵感库列表卡片与详情作者副行 SHALL 使用 Cloud 返回的来源发布时间证据。解析成功时 SHALL 按 `minute|hour|day` 精度格式化；不可解析但有原文时 SHALL 展示原文并标明未转换；完全缺失时 SHALL 显示“发布时间未知”。`updatedAt` MAY 继续用于缓存和治理，但 MUST NOT 在原稿发布时间位置显示或被描述为原稿时间。

#### Scenario: 列表展示来源发布日期

- **WHEN** 灵感列表项带日精度标准来源时间
- **THEN** 作者副行显示该来源日期，不显示精选记录更新时间

#### Scenario: 详情展示不可解析原文

- **WHEN** 灵感详情只带不可解析的来源时间原文
- **THEN** 作者副行显示原文与未转换标识，不猜测绝对时间

#### Scenario: 旧行显示未知

- **WHEN** 灵感行不带任何来源发布时间字段
- **THEN** 列表与详情显示“发布时间未知”，不回落到 `updatedAt`

### Requirement: 手动打开账号人设时不依赖环境引擎并展示 Cloud 真态

用户点击环境栏人设图标 SHALL 触发该环境的具名 customer-auth 人设读取，MUST NOT 以 core、浏览器、平台登录或边云 WebSocket 在线作为手动查看前置。读取在途 SHALL 显示明确加载态；只有 Cloud 返回 `configured` 才显示已设置，只有 Cloud 返回 `missing` 才显示未设置。网络失败、服务不可用、归属失败或绑定失败 MUST NOT 被渲染为未设置。

手动读取与草稿状态 SHALL 按环境隔离；切换环境、请求乱序或在线 status 推送 MUST NOT 把 A 的人设、失败、草稿或保存回执显示到 B。自动弹窗仍只由在线 Cloud 权威的 `personaBound === false` 触发，手动离线读取不得把未知状态推断成自动提醒。

#### Scenario: 停止环境可查看当前人设

- **WHEN** 用户点击一个已持久绑定账号但 core 停止的环境的人设图标
- **THEN** 浮层加载并展示 Cloud 当前人设真态，MUST NOT 显示“请先启动”作为查看前置

#### Scenario: 加载失败不冒充未设置

- **WHEN** 人设读取因网络、服务、归属或绑定冲突失败
- **THEN** 浮层显示对应失败与重试入口，MUST NOT 显示“未设置”或开放保存成功态

#### Scenario: 从未识别账号诚实引导首次启动

- **WHEN** Cloud 返回 `binding_unknown`
- **THEN** 浮层说明该环境尚未识别过登录账号，并提供首次启动登录动作
- **AND** MUST NOT 从环境昵称、平台资料或本地缓存猜测账号

#### Scenario: 多环境请求乱序不串号

- **WHEN** 用户先打开环境 A 人设、再切到 B，随后 A 的读取或生成结果晚到
- **THEN** B 的浮层不显示 A 的人设、草稿、错误或成功回执

### Requirement: 已设置人设以精简摘要优先并可进入调整流程

已设置账号的人设浮层 SHALL 默认展示简洁摘要，至少包含人设名/定位、语气、内容方向，以及平台适用时的发言语言和点赞倾向；完整 soul YAML SHALL 收在默认折叠的“查看完整定义”内。界面 SHALL 提供一个明确的“调整人设”入口，进入后复用现有选择→生成草稿→预览确认流程，MUST NOT 默认暴露可直接编辑的 YAML 或增加解绑入口。

调整流程 SHALL 尽量预填当前人设中可精确映射的选项；确认按钮与提示 MUST 说明保存会整体替换当前人设。生成草稿不改变已设置徽标；保存请求在第一个 await 前 SHALL 显示在途并禁用重复动作，成功回执后才刷新摘要，失败则保留原摘要和草稿。

#### Scenario: 当前人设摘要优先于泛化绿卡

- **WHEN** Cloud 返回 configured 人设
- **THEN** 浮层展示该人设的真实姓名/定位、语气与内容方向，而不是只显示“已设置、正在运营”的泛化状态

#### Scenario: 完整定义默认折叠

- **WHEN** 已设置人设浮层首次打开
- **THEN** 可读摘要直接可见，完整 YAML 只在用户主动展开“查看完整定义”后出现

#### Scenario: 调整生成不覆盖现有人设

- **WHEN** 用户进入调整并生成新草稿但未确认
- **THEN** 原人设摘要和已设置语义保持，界面明确草稿待确认，MUST NOT 本地翻成已更新

#### Scenario: 保存失败回退并呈现真实原因

- **WHEN** 确认保存被 Cloud 拒绝或网络失败
- **THEN** 在途状态解除、原人设保持可见、草稿可重试，并显示真实失败原因，MUST NOT 出现成功措辞

### Requirement: Video-channel authorization guidance is actionable and identity-aware
The Edge client SHALL explain first authorization, successful identity binding, reauthorization, challenge, and identity mismatch using structured interaction auth data. It MUST NOT instruct ordinary users to configure internal account IDs or infer success from a request-accepted response.

#### Scenario: First authorization is required
- **WHEN** the selected video-channel environment has `status=login_required` and no bound identity projection
- **THEN** the workspace explains that the opened profile will bind the currently scanned video-channel account, names the selected environment, and offers one explicit action to open the login window

#### Scenario: Reopen request is accepted
- **WHEN** customer-auth accepts `interaction.auth.reopen` but no later active auth status has arrived
- **THEN** the workspace displays that the browser-open request was accepted and continues to show authorization pending rather than success

#### Scenario: Finder identity mismatches the binding
- **WHEN** auth state reports `WECHAT_IDENTITY_MISMATCH`
- **THEN** the workspace explains that the browser is logged into another video-channel account, keeps historical content readable, disables all writes, and directs the user to switch to the originally bound account

### Requirement: Edge capability copy reflects Cloud-applied account controls
The workspace SHALL render current comment/DM availability from the effective capabilities reported by Edge after applying the account-scoped Cloud control version. It MUST NOT present a saved Console configuration as proof that the Edge applied it.

#### Scenario: Control is saved while Edge is offline
- **WHEN** Cloud stores a newer runtime-control version but the selected Edge is offline or has not reported capabilities from that version
- **THEN** the client distinguishes saved account configuration from current Edge availability and keeps affected actions disabled

### Requirement: Interaction workspace exposes guarded test reset controls
InteractionWorkspace SHALL show a “测试数据” reset surface only when the current interaction list response reports `testTools.dataResetEnabled=true`. It SHALL offer separate comment and DM actions, explain that the operation deletes only Cloud copies and rereads the platform, and state that it neither deletes platform data nor sends a reply. Each action MUST require entry of the channel-specific confirmation phrase before invoking a named IPC method.

#### Scenario: User confirms comment reset
- **WHEN** the dev tool is enabled and the user selects comment reset, reads the warning, and enters `重置评论`
- **THEN** the client sends one current-env comment reset request with a fresh idempotency key and disables both reset buttons while it is pending

#### Scenario: Confirmation text does not match
- **WHEN** the confirmation phrase is missing or does not exactly match the selected channel
- **THEN** the client performs no IPC call and keeps the current inbox visible

#### Scenario: Tool is unavailable
- **WHEN** list data reports the reset tool disabled or unavailable
- **THEN** the destructive reset controls are not rendered as actionable controls

### Requirement: Reset UI reports accepted, refused, and partial states honestly
After an accepted reset the workspace SHALL clear only the selected channel from its local list/selection, display “已清空，正在重新拉取”, and refresh from Cloud. It MUST NOT claim that platform data was deleted or that a sample returned until list data proves it. Safety-gate rejection and post-delete dispatch failure SHALL be shown as distinct human-readable states without hiding the currently loaded other-channel data.

#### Scenario: Reset is accepted
- **WHEN** customer-auth returns accepted for DM reset
- **THEN** the current DM selection is removed, comment items remain visible where applicable, and the workspace polls the real inbox for reread results

#### Scenario: Cloud cleared but Edge dispatch failed
- **WHEN** customer-auth returns the partial-completion error
- **THEN** the workspace says the Cloud DM copy was cleared but automatic reread did not start and offers a retry without claiming success

### Requirement: 慢启动开关必须即时反馈提交过程并以云端真态收敛

客户端 SHALL 在用户拨动账号级慢启动开关后立即显示与目标动作一致的提交中样式，并在云端返回前明确说明正在等待确认。该临时态 MUST 只表达请求在途，MUST NOT 冒充慢启动已经生效，MUST NOT 本地推算天数、绑定状态或计划量。

写入在途期间，客户端 MUST 禁止同一环境重复提交，且 MUST NOT 让旧的 `ui.snapshot` 把目标开关或提交中样式拨回。临时态及错误 MUST 按环境隔离。

#### Scenario: 开启请求立即进入等待确认样式

- **WHEN** 用户在一个可用的 Facebook 环境中将慢启动从关闭拨为开启，且云端请求尚未完成
- **THEN** 开关 MUST 在同一交互周期显示为目标开启态并被暂时禁用
- **AND** 同一行 MUST 显示“正在开启”及等待云端确认的可见反馈
- **AND** 客户端 MUST NOT 在此时显示“第 1/7 天”或任何本地推算的生效计划量

#### Scenario: 关闭请求立即进入等待确认样式

- **WHEN** 用户将慢启动从开启拨为关闭，且云端请求尚未完成
- **THEN** 开关 MUST 立即显示为目标关闭态并被暂时禁用
- **AND** 同一行 MUST 显示“正在关闭”及等待云端确认的可见反馈

#### Scenario: 在途旧快照不得覆盖目标样式

- **WHEN** 慢启动写入仍在途，客户端收到该环境写入前的旧 `ui.snapshot`
- **THEN** 客户端 MUST 保留当前目标开关与提交中样式
- **AND** 权威快照数据本身 MUST NOT 被本地临时态篡改

#### Scenario: 成功后立即采用写后真态

- **WHEN** 云端成功回包并携带该环境的写后 `slowStart` 真态与 `dayQuotas`
- **THEN** 客户端 MUST 清除提交中样式，并立即按回执渲染慢启动徽章和当日计划值
- **AND** 客户端 MUST NOT 等待下一次周期性快照才显示已生效结果

#### Scenario: 失败后恢复原状态并保留原因

- **WHEN** 云端拒绝写入、请求异常或超时
- **THEN** 客户端 MUST 清除提交中样式并恢复点击前的权威开关与徽章状态
- **AND** 同一行 MUST 保留可读的失败原因，直至用户再次提交或该环境反馈被明确替换

#### Scenario: 环境切换不串写反馈

- **WHEN** 环境 A 的慢启动请求在途期间用户切换到环境 B
- **THEN** 环境 B MUST NOT 显示环境 A 的提交中样式、目标开关或失败原因
- **AND** 环境 A 的回执 MUST NOT 改写环境 B 的状态

### Requirement: 客户灵感库提供清晰且可恢复的服务端排序控件

桌面客户端灵感库 SHALL 在列表工具栏右侧、总数之后提供次级排序下拉，不得把排序放进全局标题栏、单条卡片或伪装成第四个创作状态筛选。控件 SHALL 提供“综合热度”“收藏最多”“点赞最多”和“最近更新”，默认 SHALL 为“综合热度”；菜单 SHALL 解释综合热度为“点赞 + 收藏 × 1.43”，并 SHALL 说明排序依据系统最近一次采集的赞藏数据，不得宣称实时热度。

排序值 SHALL 通过具名 IPC 交给主进程白名单校验，再由 Cloud 在分页前执行；渲染层 MUST NOT 拉取全池后自行排序。排序状态 SHALL 按环境保存：切换排序回到第一页和顶部，切换创作状态保留排序，从详情返回恢复排序、筛选、页码和滚动位置，另一环境不得继承当前环境的列表结果。

#### Scenario: 桌面工具栏区分筛选和排序

- **WHEN** 客户在常规宽度打开灵感库
- **THEN** “未创作 / 已创作 / 全部”保持在工具栏左侧，总数与安静的次级排序按钮位于右侧，排序不使用主操作实底色

#### Scenario: 最小窗口下工具栏有序换行

- **WHEN** 客户将主窗口缩到支持的最小宽度附近
- **THEN** 创作状态筛选保持完整可点，总数与排序控件换到独立行且不重叠、不截断卡片内容

#### Scenario: 切换排序请求服务端第一页

- **WHEN** 客户从“综合热度”切换到“收藏最多”
- **THEN** 客户端以 `sort=collects` 请求当前账号和当前筛选的第一页，将列表滚动位置归零，并且不在当前页本地重排冒充分页结果

#### Scenario: 排序中保留已确认列表

- **WHEN** 当前列表已有内容且新的排序请求尚未返回
- **THEN** 客户端保留原卡片并显示克制的加载反馈，暂时禁止重复排序，不把列表替换为空池或通用失败态

#### Scenario: 瞬时排序失败恢复原状态

- **WHEN** 新排序请求因普通网络或暂时服务错误失败，且当前客户会话与环境归属仍未被明确否定
- **THEN** 客户端恢复上一次已确认的排序、页码、滚动位置和卡片，并展示“排序未更新”的真实失败反馈，不渲染其它账号内容

#### Scenario: 身份或归属失败清除缓存内容

- **WHEN** 新排序请求明确回报会话失效、环境撤权、绑定未知、绑定冲突或绑定不可证实
- **THEN** 客户端不得继续显示先前缓存的灵感卡片，必须清除列表并展示对应具名 fail-closed 状态

#### Scenario: 从详情返回恢复排序上下文

- **WHEN** 客户从已排序列表进入灵感详情后返回
- **THEN** 客户端恢复进入详情前的排序、筛选、页码和滚动位置，不重置为默认综合热度第一页

#### Scenario: 排序菜单可用键盘操作

- **WHEN** 键盘用户聚焦排序按钮并打开菜单
- **THEN** 方向键可移动选项，Enter 可选择，Escape 可关闭，按钮和选项具有正确的展开与选中可访问状态

### Requirement: 未绑定账号的环境 SHALL 可预设并看懂慢启动

当云端就某环境返回明确环境 `state` 且 `ineligibleReason=binding_unknown` 时，客户端 SHALL 渲染慢启动整行并保持开关可操作。客户端 SHALL 将“环境配置已保存”和“当前没有账号可被 clamp”分开表达。

该状态 MUST NOT 表现为整行隐藏、开关禁用、写入失败或“已保存待下发”。开启时显示“已为此环境开启，登录账号后按曲线生效”；关闭时说明可以在登录账号前先为此环境开启。客户端 MUST NOT 展示 `binding`、当日上限或“已压低”等只有 controller 才能确认的内容。

客户端 MUST NOT 因环境从未连接而跳过该行；没有活快照时 SHALL 经不依赖边缘的 env-scoped 读取取得环境配置态。

#### Scenario: 未绑定且已开启时显示环境配置

- **WHEN** 用户选中自己拥有、未绑定账号且环境投影 `state=active` 的 Facebook 环境
- **THEN** 慢启动整行可见，开关勾选且可点击
- **AND** 文案说明登录账号后生效，MUST NOT 声称当前配额已被压低

#### Scenario: 未绑定且关闭时允许预先开启

- **WHEN** 用户选中自己拥有、未绑定账号且环境投影 `state=off` 的 Facebook 环境
- **THEN** 慢启动整行可见，开关未勾选且可点击
- **AND** 用户开启后客户端提交 env-scoped PUT，不要求先启动浏览器或完成登录

#### Scenario: 从未启动的环境经云端读取渲染出该行

- **WHEN** 用户选中一个边缘从未连接、因而没有活快照的 Facebook 环境
- **THEN** 客户端经 env-scoped 读取取得慢启动环境配置并渲染该行
- **AND** MUST NOT 因缺少边缘快照而隐藏或默认关闭

#### Scenario: 多来源不得逐字段拼接

- **WHEN** 同一环境同时存在活快照、env-scoped 读取结果与写入回执
- **THEN** 客户端按既定优先级整体采用其中一个来源
- **AND** MUST NOT 把不同来源字段合并成任何来源都未报告的混合状态

### Requirement: 稿件审核页面配图可逐张删除、非乐观、最后一张不可删

稿件审核页面的配图区 SHALL 在**可审批态**（稿件处于待审）**且配图 ≥ 2 张**时，为每张配图提供**删除入口**；删除 SHALL 经既有的「渲染层 → 主进程 → 核心子进程 → 边-云 WS」链路发往云端（渲染层 MUST NOT 直接访问网络），由云端在其账号绑定的编辑通道上完成落库（见 `publish-draft-client-edit`）。

删除交互 SHALL 满足：

- **二次确认**：删除前 SHALL 就地二次确认，MUST NOT 单击即删。
- **非乐观**：确认后 MUST NOT 先行在本地移除缩略图；SHALL 置忙态等待云端应答，并以**服务端回读的真态**（新配图列表 + 新版本号）重绘。
- **忙态互斥**：删除在途时「发布」「取消」及其余删除入口 SHALL 一并禁用，避免客户以**过期版本号**发起审批而撞版本闸、看到莫名其妙的失败。
- **最后一张不可删**：配图仅剩一张时 SHALL NOT 显示删除入口，并 SHALL 给出「至少保留一张配图」的说明（云端同样拒绝，端上提示不是唯一防线）。
- **拒因诚实**：删除失败 SHALL 按云端具名拒因呈现可区分的中文原因（稿件已更新 / 该配图已不在稿件里 / 稿件已审批过 / 至少保留一张配图 / 未连上云端等），MUST NOT 以「删除成功」或任何乐观措辞掩盖失败，MUST NOT 在失败后仍把该张从界面上抹掉。
- **状态跨帧存活**：确认态与忙态 SHALL NOT 依赖稿件审核页面 DOM 存活（页面在每帧云端快照到达时可以重绘），MUST NOT 因一次心跳快照而丢失。

删除成功后，客户端所持稿件的**配图列表与版本号** SHALL 立即更新为服务端真态，使随后的「发布」不因版本过期被弹回；该更新 SHALL 由持有稿件状态的主进程写入并广播，MUST NOT 只改渲染层本地副本（否则下一帧广播会把它顶掉、被删的图会「长回来」）。

已删除的配图 MUST NOT 提供撤销 / 重新加入的入口——客户端**只删不注入**。

#### Scenario: 删掉一张多余配图后照常发布

- **WHEN** 待审稿件有 3 张配图，客户在审核页面里删掉其中一张并确认
- **THEN** 该张 SHALL 在云端落库删除后从界面消失，其余两张保序留存；审核页面与发布卡的配图张数 SHALL 更新为服务端真态；客户随即点「发布」SHALL NOT 因版本过期失败

#### Scenario: 只剩一张配图

- **WHEN** 待审稿件只剩一张配图
- **THEN** 该张 SHALL NOT 显示删除入口，界面 SHALL 说明至少保留一张配图

#### Scenario: 删除在途时不能审批

- **WHEN** 一次删除请求在途未回
- **THEN** 「发布」「取消」与其余删除入口 SHALL 处于禁用态，直至应答返回

#### Scenario: 删除失败诚实呈现

- **WHEN** 云端以具名拒因拒绝删除（如稿件已被他处修改、该配图已不在稿件里、稿件已审批过、客户端未连上云端）
- **THEN** 界面 SHALL 呈现对应的中文原因、该张配图 SHALL 仍在界面上（未被抹掉），MUST NOT 出现任何成功措辞

### Requirement: 视频号只替换当前环境右侧 workspace

Electron 客户端 SHALL 保持现有全局标题栏与左侧环境栏；当前环境 platform=`wechat_channels` 时，只在右侧渲染 InteractionWorkspace。MUST NOT 新增永久第二侧栏、替换环境栏或展示 browse/like/collect/follow/publish 的无意义零指标。XHS/Facebook 继续使用既有 workspace。

#### Scenario: 切换到视频号保留应用壳
- **WHEN** 用户从 XHS/FB 环境切换到 wechat_channels 环境
- **THEN** 左侧环境栏与标题栏保持位置/功能，右侧原子切成互动队列与详情

#### Scenario: 切回旧平台零回归
- **WHEN** 用户从视频号环境切回 XHS/Facebook
- **THEN** 原工作区恢复且不残留视频号 tabs、thread 或写按钮

### Requirement: 环境切换必须取消旧请求并校验 envKey

列表、详情、auth/sync 状态与所有写回包 SHALL 绑定当前 `envKey`。切换环境 MUST 取消可取消请求并丢弃迟到回包；新环境加载中显示自身 loading/unknown，MUST NOT 复用旧账号数据。最终文本草稿 MUST 绑定原 env/job，不能静默移到新环境。

#### Scenario: A 的迟到回包不覆盖 B
- **WHEN** 用户快速 A→B 切换且 A 的详情响应后到
- **THEN** renderer 校验 envKey 后丢弃 A 响应，B 页面不闪现 A 的昵称/私信/动作

### Requirement: 视频号 workspace 必须保留当前环境生命周期控制

InteractionWorkspace SHALL 在顶部提供当前视频号环境可见的生命周期控件，并与 XHS 使用同一状态矩阵和判定优先级。会话为 paused 时 SHALL 优先同时显示“恢复”和独立的“关闭”；其余核心为 stopped/warning 时 SHALL 只显示“启动”；其余 starting/running 时 SHALL 只显示“暂停”。“暂停” MUST 保留当前浏览器/会话；“关闭” MUST 仅在暂停态可见且可执行，关闭完成后 SHALL 按主进程回传真态回到“启动”。所有动作 MUST 复用既有单环境 lifecycle IPC 并携当前 `envKey`；MUST NOT 调用 fleet 全部启动、把显示浏览器/重新登录冒充启动、操作其他环境、清除登录凭证或触发 offboard。

#### Scenario: 离线视频号环境可以就地启动
- **WHEN** 用户选中 edge=stopped 的 wechat_channels 环境并点击“启动”
- **THEN** 客户端只向该环境的单环境启动 IPC 传递当前 envKey，其他环境保持原状态

#### Scenario: 生命周期状态切换使用同一入口
- **WHEN** 当前视频号环境从 running 进入 paused，或从 paused 恢复运行
- **THEN** 按钮依次显示“暂停”“恢复”“暂停”，每次动作都绑定当前 envKey 且以主进程回传真态刷新

#### Scenario: 暂停后可以显式关闭当前环境
- **WHEN** 当前视频号环境为 paused
- **THEN** workspace 同时显示“恢复”和“关闭”；点击“关闭”只调用当前 envKey 的单环境关闭 IPC，完成后显示“启动”，且其他环境、登录凭证和 offboard 状态保持不变

#### Scenario: 非暂停态不暴露关闭入口
- **WHEN** 当前视频号环境为 starting、running、stopped 或 warning
- **THEN** “关闭”入口不可见且 handler 拒绝执行，用户必须先暂停当前环境才能显式关闭

### Requirement: 开发者详情必须跨 workspace 保持可见

设置中的“显示开发者详情”开关 SHALL 继续控制共享的当前环境原始日志面板，默认隐藏和持久化语义 SHALL 保持不变。该面板 MUST 位于 XHS/Facebook legacy workspace 与视频号 InteractionWorkspace 的互斥切换之外；开关启用后切换到 `wechat_channels` MUST 继续显示当前选中 `envKey` 的日志，MUST NOT 因 legacy workspace 隐藏而消失或展示其他环境日志。

#### Scenario: 视频号环境显示已启用的开发者详情
- **WHEN** 用户已启用“显示开发者详情”并从 XHS/Facebook 切换到视频号环境
- **THEN** InteractionWorkspace 与开发者详情同时可见，日志内容切换到当前视频号 envKey 的分桶；切回其他环境时同一面板继续显示对应环境日志

### Requirement: 互动 workspace 必须呈现真实队列与发送状态

InteractionWorkspace SHALL 提供横向 `待处理/评论/私信/已回复` 视图、分页列表、thread 详情、模板/AI 差异、风险、final text 与 ignore/escalate/regenerate/approve/send 动作。`queued`、`sending`、`ambiguous`、`sent`、`failed` MUST 有不同文案/视觉；只有 sent 可显示平台确认成功，ambiguous 必须显示待核验。

#### Scenario: HTTP accepted 不显示绿色成功
- **WHEN** send API 返回 job queued
- **THEN** UI 显示已进入发送队列/等待平台结果，MUST NOT 显示已回复成功

#### Scenario: 未配置模板仍继续显示收件箱
- **WHEN** 环境能同步但无有效 published reply config
- **THEN** 列表/详情可读并显示配置阻断卡，生成/发送禁用，MUST NOT 显示空成功态

### Requirement: 浏览器关闭是正常副状态而 reauth/challenge 是阻断

顶部状态 SHALL 区分 interaction auth 与 browser sidecar：auth active + browser closed 显示正常 API 同步；reauth_required/challenge_required 禁用写、保留历史并提供 reopen。网络/限流/schema disabled SHALL 各自使用可解释状态，MUST NOT 解析 Edge 日志猜测。

#### Scenario: API-only running 不告警
- **WHEN** auth active、最近同步成功且 browserState=closed
- **THEN** 标题显示互动托管/接口同步正常，辅助文字说明浏览器已关闭（正常）

#### Scenario: Challenge 保留历史并禁写
- **WHEN** auth status=challenge_required
- **THEN** 已同步 thread 仍可读，approve/send 禁用并提示在原浏览器处理

### Requirement: Renderer 必须经最小具名 IPC 访问 customer-auth API

renderer MUST NOT 持有 JWT/Cookie、访问平台接口、记录完整 DM 或获得任意 URL fetch。preload SHALL 只暴露冻结路径对应的具名 IPC；Electron main 校验 method/path/body，并复用现有 client auth session。Cloud 仍作最终 enabled user/env ownership/CAS 检查。

#### Scenario: Renderer 不能构造任意请求
- **WHEN** renderer 尝试传入任意 URL 或非冻结 method/path
- **THEN** preload/main 拒绝，MUST NOT 代发网络请求或泄漏 token

### Requirement: 环境删除必须显示 offboard 真态

视频号环境的显式删除/解绑 SHALL 先调用 customer-auth `DELETE /environments/:envKey`，再用 `GET /offboarding/:offboardId` 读取 Cloud/Edge 清理真态。`pending_edge|dispatched` MUST 显示“已撤权，等待本机/离线设备清理”，不能把本地 profile 删除、普通 logout、pause/close 或 HTTP 2xx 显示成凭证已删除。只有 `tombstoned|purged` 才可显示 Cloud 已完成对应阶段。

#### Scenario: Edge 离线时环境仍显示待清理
- **WHEN** 用户解绑环境而所属 Edge 离线
- **THEN** UI 立即停止该环境互动访问/写，保留 offboardId 与待清理状态，MUST NOT 显示“删除完成”或丢弃恢复入口

#### Scenario: 本地 profile 删除不冒充 offboard 完成
- **WHEN** 浏览器 profile 本地删除成功但 Cloud offboard 尚未收到 Edge cleared ack
- **THEN** UI 仍显示待凭证清理，MUST NOT 将本地动作映射为 tombstoned/purged

### Requirement: 互动 workspace 必须满足基线尺寸与无障碍

在 `820×720` SHALL 可完成列表选择、上下文查看、编辑、批准/发送/转人工；更窄窗口 SHALL 按基线折叠而不遮挡主动作。tabs、列表、编辑器和主要动作 MUST 键盘可达、focus 可见、状态不只靠颜色。

#### Scenario: 820×720 完成主流程
- **WHEN** 窗口为 820×720 且 thread 有待审草稿
- **THEN** 用户无需页面级横向滚动即可查看风险、编辑并执行主要动作

### Requirement: 单列互动布局必须提供主列整体滚动

当左侧环境栏使右侧 InteractionWorkspace 的 container 宽度进入单列布局时，Electron 客户端 SHALL 让右侧主列整体纵向滚动，MUST NOT 继续用宽屏固定高度加 `overflow:hidden` 裁掉列表下方的详情或共享开发者详情。是否折叠为单列 MUST 以右侧 workspace 的实际可用宽度为准；支持 container query 的客户端 MUST NOT 再被 viewport-only 断点提前覆盖。宽屏双列布局 MAY 保留列表/详情各自滚动，但任何布局都必须让当前 thread 详情可达。

#### Scenario: 820×720 环境栏展开后详情仍可达
- **WHEN** 窗口为 820×720、环境栏可见且 workspace container 宽度不超过 640px
- **THEN** 用户在右侧主列向下滚动可依次到达互动详情和开发者详情，MUST NOT 被只响应 viewport 宽度的断点裁切

#### Scenario: 窄 viewport 但右侧仍够宽时保持双栏
- **WHEN** viewport 不超过 700px，但 InteractionWorkspace 的实际可用宽度仍大于 640px
- **THEN** 收件箱保持列表/详情双栏，MUST NOT 因 viewport-only 兜底把消息列表拉成通栏；只有 workspace 自身进入单列阈值后才折叠

### Requirement: Video-channel workspace exposes truthful browser foreground controls
The Electron video-channel workspace SHALL show an environment-scoped browser control when authorization is active: `browserState=closed` SHALL expose “打开浏览器”, `browserState=open` SHALL expose “转入后台”, and transitional states SHALL show a disabled progress label. Reauthorization and customer logout controls MUST remain separate actions with distinct copy.

#### Scenario: Active browser is closed normally
- **WHEN** the selected video-channel environment reports `status=active` and `browserState=closed`
- **THEN** the workspace states that API background operation is active and exposes “打开浏览器” for that environment

#### Scenario: Active browser is visible
- **WHEN** the selected video-channel environment reports `status=active` and `browserState=open`
- **THEN** the workspace states that the browser is open and exposes “转入后台” without labeling the account as newly logged in

#### Scenario: Browser action is awaiting Edge truth
- **WHEN** the customer API accepts an open or close request but the target browser state has not yet arrived
- **THEN** the workspace displays a waiting-for-Edge message and MUST NOT claim the browser has opened or closed

#### Scenario: Authorization requires user action
- **WHEN** auth status is login required, reauthorization required, or challenge required
- **THEN** the workspace shows the existing login or challenge action instead of the ordinary foreground/background control

### Requirement: 云端、浏览器与人设状态 SHALL 正交呈现

Electron 客户端 SHALL 分别呈现 Cloud 会话、浏览器执行层和 `personaBound` 三态。浏览器排队、缺席或冷待机 MUST NOT 自动推导 Cloud 离线；Cloud transport 打开或握手响应异常 MUST NOT自动推导 Cloud 已连接；persona 未收到 MUST 保持未知。

#### Scenario: 浏览器排队但 Cloud 与人设已知
- **WHEN** 环境以 browser-absent 状态完成有效 Cloud welcome 并收到 `personaBound=true`
- **THEN** 客户端显示 Cloud 已连接、人设已设置、浏览器正在排队或待机
- **AND** MUST NOT 把整个环境显示为离线

#### Scenario: 有 socket 但 welcome 无效
- **WHEN** WebSocket 已打开但 hello 收到 error 或畸形 welcome
- **THEN** 客户端显示云端连接失败及可诊断原因
- **AND** MUST NOT 显示绿色“已连接云端”或用未知人设弹出未设置向导

#### Scenario: 引导不可用
- **WHEN** 控制面启动因未绑定、冲突、越权或存储不可用而不能建立 Cloud 会话
- **THEN** 客户端明确显示对应云端未连接原因与独立的浏览器排队状态
- **AND** MUST NOT 用泛化“离线”掩盖原因

### Requirement: 启动数量与失败原因 SHALL 可核对

客户端 SHALL 如实展示生效浏览器并发、正在运行数、排队数以及每个未启动环境的具体状态。单个 AdsPower 环境被占用或启动失败 MUST 释放启动闩并继续处理后续队列项，MUST NOT 使剩余任务无回复。

#### Scenario: 第五个环境被其它设备占用
- **WHEN** 浏览器并发上限为 5，而第 5 个被放行环境被 AdsPower 拒绝为“由其它设备使用”
- **THEN** 客户端将该环境标为具体启动失败、归还其槽位并继续放行下一队列项
- **AND** 运行数、排队数与失败数之和可与已请求启动数核对

### Requirement: 小红书环境首页与旧平台首页 SHALL 严格互斥

Edge SHALL 仅从当前权威环境平台派生首页模式。小红书模式 SHALL 显示完整价值首页并抑制重复的旧运行正文；Facebook、视频号和未知平台 SHALL 保留既有环境正文并完全隐藏小红书价值首页。环境切换后的迟到请求 MUST NOT 回写当前页面。

#### Scenario: 从小红书切换到 Facebook
- **WHEN** 小红书价值首页仍有内容请求在途且客户切换到 Facebook 环境
- **THEN** 客户端立即隐藏小红书价值首页、恢复 Facebook 既有环境正文，并丢弃随后到达的小红书响应

#### Scenario: 环境级阻塞证据仍可见
- **WHEN** 当前小红书环境存在登录提示、重复账号警告或真实 Edge 异常
- **THEN** 对应环境级提示仍显示在价值首页之上，不因旧运行正文被抑制而丢失

### Requirement: 首次启动引导 SHALL 作用于价值首页可见动作

首个真实小红书环境完成创建并进入权威花名册后，若当前环境动作明确为 start，客户端 SHALL 在价值首页可见的真实启动代理按钮旁显示一次性说明和有限光环。该按钮 SHALL 委托共享生命周期动作；引导 MUST NOT 指向隐藏控件、模拟成功或阻断离线内容读取。

#### Scenario: 新用户从价值首页启动
- **WHEN** 新用户选择首个未启动的小红书环境并点击价值首页引导中的启动动作
- **THEN** 引导立即结束，客户端走正常保存与启动链并等待真实回执

### Requirement: 空闲工作面板与账号排期 SHALL 保持主次层级

环境未启动或当前无任务时，桌面工作面板含 padding 与边框 MUST NOT 超过 168px，并 SHALL 仍展示启动/查看灵感动作、不会自动发布的边界以及任务开始后会出现的“计划与判断、生成与调整、检查与确认”过程预告。过程预告 SHALL 使用紧凑横向说明，MUST NOT 用大面积居中空白把精选灵感推出首屏。有真实任务的展开态 SHALL 保持 240px 稳定高度。账号排期 SHALL 保持为低干扰入口行，其视觉高度、阴影和强调度 MUST NOT 超过工作面板或精选灵感链路。

#### Scenario: 有灵感但环境未启动
- **WHEN** 当前账号已有精选灵感而环境未启动
- **THEN** 工作面板以不超过 168px 的紧凑态明确提供启动动作并展示后续过程预告，首屏可看到精选灵感分区入口，排期入口不遮蔽或替代二者

### Requirement: 价值首页排版与客户端默认窗口 SHALL 保持设计比例

已登录客户端主窗口 SHALL 默认以 1080px 宽度启动，登录窗口 SHALL 保持其独立的 900px 宽度。价值标题中的动态灵感数量短语 SHALL 使用设计蓝强调，周围句子保持深色；“收起”和“查看全部灵感 →” SHALL 使用显式且稳定的客户可读字号。空闲过程说明 SHALL 紧接过程标题出现，不得垂直居中形成大块上方留白。真实笔记图片与装饰性封面兜底 SHALL 使用同一克制阴影层级。

#### Scenario: 已收集灵感但尚无草稿
- **WHEN** 首页显示“已收集 2 条精选灵感，等待发起创作”
- **THEN** 仅“2 条精选灵感”使用蓝色强调，收起与查看全部入口保持设计稿字号，空闲过程说明靠近标题且封面与卡片背景有轻微层次

#### Scenario: 已登录客户端首次打开
- **WHEN** Electron 创建已登录主窗口
- **THEN** 主窗口默认宽度为 1080px，最小宽度和登录窗口尺寸保持原有安全边界

### Requirement: Facebook mode and primary surface are independent client choices

For a selected Facebook environment, the Edge client SHALL present operation mode as one mutually exclusive four-option choice (`persona`, `slow_start`, `rule`, `consumption`) and primary browse surface as one independent Feed/Reels choice. Creation and existing-environment editing SHALL use the same concepts. The client MUST render and confirm Cloud write-after-read truth rather than treating a local selection as persisted success.

#### Scenario: Existing environment changes operation mode

- **WHEN** the user selects one of the four operation modes
- **THEN** exactly one mode is selected and the current primary surface remains unchanged

#### Scenario: Existing environment changes primary surface

- **WHEN** the user switches the primary surface between Feed and Reels
- **THEN** the current operation mode remains unchanged
- **AND** the confirmed Cloud projection becomes the displayed selection

#### Scenario: Creation defaults to Reels

- **WHEN** the Facebook creation form opens or resets
- **THEN** its operation mode and primary-surface controls are separate
- **AND** Reels is selected as the primary surface

### Requirement: 环境主页排期入口 SHALL 绑定当前小红书环境

Edge SHALL 在选中小红书环境的 `legacy-workspace` 中、实时工作说明之后与今日进展之前渲染紧凑排期入口。Renderer SHALL 仅调用具名 `environment-schedule:get(envId)` IPC；main SHALL 由本地 envId 解析 profileId 并调用固定 env-scoped customer-auth 路径，Renderer MUST NOT 传 URL、token、envKey 或 accountId。

#### Scenario: 小红书环境加载入口
- **WHEN** 当前选中环境平台明确为小红书且 main 暴露排期 IPC
- **THEN** Edge 读取当前环境排期，并在环境主页渲染今天时段数与当前/下一时段

#### Scenario: 缺少平台或 IPC
- **WHEN** 当前平台未知、不是小红书或 main 未暴露排期 IPC
- **THEN** 入口保持隐藏且 Renderer 不发任何排期请求

### Requirement: 环境排期详情 SHALL 复用现有环境状态与控制

排期详情 SHALL 作为环境主页二级页展示，不得进入或改变内容工作区导航。详情中的启动、浏览器与实时过程入口 SHALL 委托现有当前环境生命周期和状态源；环境启动、关闭、切换及今日用量变化 SHALL 同步反映，排期页面 MUST NOT 自行假定操作成功。

#### Scenario: 从未启动环境查看排期
- **WHEN** 客户打开一个未启动小红书环境的排期详情
- **THEN** 周排期仍可查看，页面展示真实“启动当前环境”动作并复用现有启动按钮逻辑

#### Scenario: 内容工作区保持独立
- **WHEN** 客户打开或关闭环境排期详情
- **THEN** 内容工作区的内容首页、灵感库、我的内容及其状态均不被改写

### Requirement: 排期 UI SHALL 保持紧凑、响应式与可访问

环境主页入口高度 SHALL 控制在 64–72px 范围内。详情在正常宽度以日期条、时间段列表和今日结果区呈现，在窄窗口改为单列且不得造成文档横向溢出。当前、待开始、已结束、未启动和错误状态 MUST 同时使用文字与非颜色线索；动效 MUST 支持 reduced-motion。

#### Scenario: 窄窗口查看排期
- **WHEN** 客户在窄窗口打开环境主页或排期详情
- **THEN** 入口文案可收敛、日期条可在自身容器滚动、详情转为单列，页面主体不横向溢出

#### Scenario: 减少动态效果
- **WHEN** 系统启用 reduced-motion
- **THEN** 当前时段的呼吸或流光动画停止，但文字状态和边框标识仍完整可辨

### Requirement: Environment rail separates selection from exclusive browser recall

Clicking an environment's rail entry SHALL select that environment and highlight it with a distinct selected color; a single click MUST NOT show or re-park any browser. Double-clicking an environment avatar that is not the shown target SHALL select that environment if necessary and request an exclusive browser recall: every other currently controllable environment browser SHALL be sent to its own configured parking position, then the target environment's fixed-size driven browser SHALL be centered on the AIDCP companion's current outer window bounds and the companion SHALL be restored above it. Double-clicking the avatar of the environment already shown behind AIDCP SHALL restore that exact browser to its configured parking position. The shown target MUST be visually distinguishable from a merely selected environment. Nickname editing, persona controls, guided login, and explicit browser recovery MUST NOT be reinterpreted as this avatar gesture.

Exclusive recall and shown-target restore SHALL use stable environment routing, one latest-request-wins operation queue, and bounded completion receipts. A failed target show MUST NOT advance the shown target. A failed or timed-out restore MUST NOT clear the shown target. A superseded request MUST NOT overwrite a later request or display a stale failure. If the target is shown but one or more other controllable browsers fail to park, the client SHALL expose that incomplete parking result and MUST NOT claim that exclusivity was fully established.

#### Scenario: Single click only selects

- **WHEN** the operator single-clicks an environment rail entry
- **THEN** that environment becomes selected and highlighted
- **AND** no browser show or park command is sent, whether or not the environment was already selected

#### Scenario: Double-clicking another avatar performs one complete switch

- **WHEN** environment A is shown behind AIDCP and the operator double-clicks environment B's avatar
- **THEN** environment B becomes selected, environment A and every other controllable non-target browser are sent to their configured parking positions, and B is placed behind AIDCP
- **AND** B becomes the only shown target in renderer state

#### Scenario: Repeated target double-click restores the shown browser

- **WHEN** the operator double-clicks the avatar of the environment already shown behind AIDCP
- **THEN** the companion sends that exact environment to its configured parking position with a bounded completion receipt
- **AND** it clears the shown target only after parking succeeds while leaving the environment selected

#### Scenario: Shown-target restore failure remains visible

- **WHEN** the operator double-clicks the shown environment but its configured parking action fails or times out
- **THEN** the client keeps that environment represented as shown and exposes the restore failure
- **AND** it MUST NOT claim that the browser was restored from command acceptance alone

#### Scenario: Latest rapid double-click determines the final target

- **WHEN** the operator double-clicks environment A and then environment B before A's placement completes
- **THEN** the operations cannot complete out of order with A as the final shown target
- **AND** B is the final browser placed behind AIDCP while the superseded result remains silent

#### Scenario: Partial non-target parking failure is honest

- **WHEN** the target browser is shown successfully but one or more other controllable browsers fail or time out while parking
- **THEN** the client identifies the incomplete parking result without claiming full exclusivity
- **AND** the target remains represented as shown

#### Scenario: Guided login still focuses the browser

- **WHEN** the operator uses guided login or explicit recovery because direct browser interaction is required
- **THEN** the companion MAY leave that driven browser in the foreground
- **AND** the avatar-specific exclusive recall policy does not change that action

### Requirement: 慢启动曲线表 SHALL 只呈现云端下发的当前生效曲线

客户端展示的慢启动曲线表 SHALL 全部来自云端该环境慢启动读的曲线字段：行数取回包曲线的行数，每格数字取回包对应值。客户端 MUST NOT 内置任何曲线数字，MUST NOT 假定总天数为 7，也 MUST NOT 按天数、账号或平台在本地推算任何一格。

曲线表 SHALL 只呈现回包曲线里出现的动作项。客户端 MUST NOT 为回包中不存在的动作自造列或补零——该平台结构上做不了的动作，云端本就不会下发，客户端补出来的是一份系统永远不会执行的计划。

云端未下发曲线时，客户端 SHALL 就地如实说明当前读不到曲线，并 MUST NOT 渲染任何曲线数字。**MUST NOT 回落到上一次读到的曲线、内置默认曲线或另一环境的曲线**：运营正是照这张表判断新号当天还能做多少，把「读不到」渲染成一张看起来确定的表，比不显示更危险。

曲线表随附的说明文案 SHALL 按回包的权威总天数表述，MUST NOT 写死天数。

#### Scenario: 后台改过曲线后客户端跟随

- **WHEN** 运营在管理后台把总天数改为 10 天并调整了若干天的上限，客户端随后读取该 Facebook 环境的慢启动状态
- **THEN** 曲线表显示 10 行，且每格数字等于云端回包的值
- **AND** 说明文案按 10 天表述

#### Scenario: 云端未下发曲线时不显示旧数字

- **WHEN** 云端回包不含曲线字段
- **THEN** 客户端就地说明当前读不到曲线
- **AND** MUST NOT 显示任何曲线数字，包括上一次读到的与内置默认的

#### Scenario: 切换环境不得沿用上一环境的曲线

- **WHEN** 用户从一个已读到曲线的环境切到另一个尚未读到曲线的环境
- **THEN** 客户端不显示任何曲线数字，直到当前环境自己的回包到达
- **AND** MUST NOT 沿用上一环境的行数、数字或天数表述

#### Scenario: 只呈现回包里的动作项

- **WHEN** 云端下发的曲线每行只含浏览、点赞、评论、关注、发布、搜索、加组
- **THEN** 曲线表恰好呈现这些项
- **AND** MUST NOT 出现收藏、评论点赞、私信回复等回包中不存在的项，也 MUST NOT 以 0 补齐

