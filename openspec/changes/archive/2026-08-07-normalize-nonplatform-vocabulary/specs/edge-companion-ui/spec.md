## MODIFIED Requirements

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
- **WHEN** Facebook 就地身份读取（`identity.read_current_page`，不离开当前页）产生核心日志（词汇批 4 后 FB 会话结构上收不到任何作者主页命令，历史 `profile.open` 就地读形态由此取代）
- **THEN** 该核心日志 MUST NOT 命中中文兜底表中描述「顺路去作者主页看看」的跳转规则
- **AND** 客户端 MUST NOT 呈现任何声称已跳转作者主页的在场感文案

### Requirement: Electron Daily Summary Uses Account-Scoped Cloud Usage

The Electron companion SHALL prefer cloud-supplied account-scoped daily usage over locally accumulated log counters for the "today" summary when `ui.push_snapshot.dailyUsage` is available.

#### Scenario: Hello snapshot replaces local counters with account today totals

- **WHEN** cloud sends `ui.push_snapshot.dailyUsage` for the account bound to the edge
- **THEN** Electron renders the supplied account daily totals for exactly the actions the cloud supplied, instead of treating the local process's current-session deltas as authoritative
- **AND** it renders no metric for an action the cloud did not supply

#### Scenario: Local counters remain a fallback before cloud usage arrives

- **WHEN** Electron has not yet received `ui.push_snapshot.dailyUsage`
- **THEN** it MAY continue to show local log-derived deltas for available actions, and MUST NOT present quota caps or saturation as if they were authoritative

### Requirement: Electron Daily Summary Shows Current Daily Quota Saturation
The Electron companion SHALL show daily plan progress for each supplied action when cloud includes the current quota level's daily caps. Reaching a supplied cap SHALL be presented as completing that action's daily plan, distinct from global risk warnings, captcha restrictions, and execution failures.

#### Scenario: Action reaches the current level's daily plan

- **WHEN** `ui.push_snapshot.dailyUsage.saturated` includes an action, or the supplied total is greater than or equal to the supplied cap for that action
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

Cloud and edge SHALL keep `ui.push_snapshot.dailyUsage` optional and backward compatible with older peers.

#### Scenario: Old edge ignores the field

- **WHEN** an older edge receives `ui.push_snapshot` with unknown daily usage fields
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

- **WHEN** `ui.push_snapshot.dailyUsage.windows` includes `session`, `minute`, `hour`, and `day`
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

Cloud and edge SHALL preserve the existing `ui.push_snapshot.dailyUsage` daily aliases while adding optional windowed quota data.

#### Scenario: New cloud sends windowed usage to an old edge

- **WHEN** cloud includes `ui.push_snapshot.dailyUsage.windows`
- **THEN** the existing `dailyUsage.totals`, `dailyUsage.quotas`, and `dailyUsage.saturated` fields still describe the day window
- **AND** an older edge can ignore `windows` without losing the existing daily summary behavior

#### Scenario: New edge receives old daily-only usage

- **WHEN** Electron receives `ui.push_snapshot.dailyUsage` without `windows`
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

- **WHEN** Electron is in a running or resting session, the latest presence event is stale, and `ui.push_snapshot.dailyUsage.windows` shows a current session, minute, hour, or day window with at least one saturated capped action
- **THEN** the presence strip SHALL render a completion message naming the action or its user-facing activity
- **AND** it SHALL state that the platform is being given time to learn from the current activity
- **AND** it SHALL include the estimated remaining wait until `releaseAt` when that timestamp is available and in the future
- **AND** the presence strip MUST NOT animate as if the completed action is still happening
- **AND** it MUST NOT use red warning styling or claim that unrelated actions have stopped

#### Scenario: Pacing evidence is stale or incomplete

- **WHEN** the latest presence event is stale but the relevant quota window is expired, missing, or lacks capped saturated action evidence
- **THEN** Electron SHALL keep the existing stale-activity fallback instead of fabricating a plan-completion explanation

### Requirement: Daily Usage Windows Expose Refresh And Release Timing

Cloud SHALL include optional timing hints on `ui.push_snapshot.dailyUsage.windows`
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

- **WHEN** Electron receives `ui.push_snapshot.dailyUsage.windows` without `refreshAt` or `releaseAt`
- **THEN** it SHALL render the existing window state, totals, quotas, and stale fallback text as before

### Requirement: Cloud Refreshes Online Daily Usage Snapshots Best-Effort

After sending account-scoped daily usage to an online edge, cloud SHALL schedule
a best-effort daily-usage-only `ui.push_snapshot` refresh for that same account and
edge when a finite future `refreshAt` is available. The scheduled refresh MUST
be targeted to the same edge, MUST NOT broadcast to unrelated edges, and MUST
stop retrying when the edge is no longer online or the targeted push is not
delivered.

#### Scenario: Online edge receives a scheduled usage refresh

- **WHEN** cloud has sent daily usage with a future `refreshAt` to an online edge
- **THEN** cloud SHALL attempt a targeted `ui.push_snapshot` containing fresh `dailyUsage` at or after that time
- **AND** the refreshed snapshot MAY schedule the next refresh using its new timing metadata

#### Scenario: Offline edge does not cause retry storm

- **WHEN** a scheduled daily usage refresh push reaches no edge
- **THEN** cloud MUST stop that scheduled refresh chain for the account-edge pair
- **AND** it MUST NOT broadcast the snapshot to other edges for the account

### Requirement: 人设绑定态为三态，未知绝不等同未绑

The `personaBound` signal on the `ui.push_snapshot` stream SHALL carry three states: `true` (cloud confirms bound), `false` (cloud confirms unbound), and **absent** (unknown — the cloud has not said yet). Cloud is the single writer of persona state and therefore SHALL send both `true` and `false`. Edge MUST NOT treat "unknown" as "unbound": no timer, grace window, or timeout may promote unknown into unbound.

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

### Requirement: 慢启动状态与开关在今日进展卡内如实呈现

客户端 SHALL 在「今日进展」摘要卡内以常驻脚注行呈现当前选中环境的慢启动状态与开关。该行 MUST NOT 位于默认收起区或会因窗口无数据而整块隐藏的容器内；慢启动允许在账号登录前按环境预先设置。

该行 MUST NOT 置于自定义标题栏内。标题栏空间与窄窗约束不变，环境级配置也不需要挤入标题区域。

`ui.push_snapshot` 或 env-scoped 读取的慢启动字段 SHALL 为权威环境配置；字段整体缺省仍表示未知。客户端 MUST NOT 把未知渲染为“未开启”。当投影同时包含 `binding_unknown` 与明确 `state` 时，`state` 表达环境配置，`binding_unknown` 表达当前没有账号执行对象；两者 MUST NOT 互相覆盖或被压成一个禁用态。

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

### Requirement: 慢启动开关必须即时反馈提交过程并以云端真态收敛

客户端 SHALL 在用户拨动账号级慢启动开关后立即显示与目标动作一致的提交中样式，并在云端返回前明确说明正在等待确认。该临时态 MUST 只表达请求在途，MUST NOT 冒充慢启动已经生效，MUST NOT 本地推算天数、绑定状态或计划量。

写入在途期间，客户端 MUST 禁止同一环境重复提交，且 MUST NOT 让旧的 `ui.push_snapshot` 把目标开关或提交中样式拨回。临时态及错误 MUST 按环境隔离。

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

- **WHEN** 慢启动写入仍在途，客户端收到该环境写入前的旧 `ui.push_snapshot`
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
