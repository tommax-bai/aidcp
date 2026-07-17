## REMOVED Requirements

### Requirement: Cloud MUST NOT supply usage caps for actions the platform cannot perform

**Reason**: Superseded by "Cloud MUST NOT supply usage metrics for actions the platform cannot perform". The rule drew its line in the wrong place. It forbade the fabricated cap but explicitly preserved the fabricated total, on the reasoning that a total is an observation and only a promise can lie. That reasoning does not hold for an action the platform has no concept of: the total is not observed, it is materialised — a constant the projection invents for a key it is required to fill. "Collect 0" on Facebook reads as "none today" and implies "some tomorrow", when the truth is "never". It and the forever-empty progress bar are the same fabrication; the cap merely carried the denominator. Keeping the superseded rule alongside the new one would leave two contradictory laws in one capability, each citable.

**Migration**: The replacement carries every scenario of the removed requirement forward with the same force — the two-matrix determination, the no-numeric-encoding ban, the fail-open direction, the every-surface reach, and the withheld-cap-never-blocks-completion rule. Only the final paragraph is reversed: withholding a metric now withholds its row. No cap that was supplied before is supplied now, and no cap that was withheld before is restored.

## ADDED Requirements

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

## MODIFIED Requirements

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

### Requirement: Electron Daily Summary Uses Account-Scoped Cloud Usage

The Electron companion SHALL prefer cloud-supplied account-scoped daily usage over locally accumulated log counters for the "today" summary when `ui.snapshot.dailyUsage` is available.

#### Scenario: Hello snapshot replaces local counters with account today totals

- **WHEN** cloud sends `ui.snapshot.dailyUsage` for the account bound to the edge
- **THEN** Electron renders the supplied account daily totals for exactly the actions the cloud supplied, instead of treating the local process's current-session deltas as authoritative
- **AND** it renders no metric for an action the cloud did not supply

#### Scenario: Local counters remain a fallback before cloud usage arrives

- **WHEN** Electron has not yet received `ui.snapshot.dailyUsage`
- **THEN** it MAY continue to show local log-derived deltas for available actions, and MUST NOT present quota caps or saturation as if they were authoritative

### Requirement: Electron Daily Summary Shows Multi-Window Quota Status
The Electron companion SHALL show plan progress for each cloud-supplied quota window: current session, minute, hour, and day, while keeping the collapsed daily summary focused on today's account totals. User-facing labels SHALL translate those windows into round, current pace, stage, and daily plan concepts while expanded detail preserves exact supplied totals and caps.

#### Scenario: Daily card is collapsed by default

- **WHEN** Electron has received account-scoped daily usage with quota windows
- **THEN** the collapsed card renders the day-window totals for exactly the actions the cloud supplied for that account
- **AND** it does not render session, minute, or hour action details until the user expands the card

#### Scenario: User expands the daily progress card

- **WHEN** the user clicks the daily progress card or its disclosure control
- **THEN** Electron renders plan detail for each supplied window: current round, current pace, stage, and today
- **AND** each window detail lists as separate action rows exactly those actions for which that window supplies a total or a cap, and no others
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
