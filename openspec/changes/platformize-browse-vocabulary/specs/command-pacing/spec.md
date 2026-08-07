## MODIFIED Requirements

### Requirement: 决策指令携带可选时间指令

云端 → 边缘的决策指令 SHALL 支持可选的时间字段：`navigation.back` / `{platform}.note.close` 携带
`dwellMs`（离开当前页前应达到的总停留时间），`interaction.like` / `interaction.collect` /
`interaction.follow` / `{platform}.note.open` 携带 `thinkMs`（执行动作前的犹豫 / 感知时间）。时间字段
全部可选，缺失视为合法，边缘按内置默认兜底。云端 MUST NOT 在 `session.budget` 下发整套时间
系数要求边缘自行套公式计算内容相关时长。

#### Scenario: 返回指令带停留时长

- **WHEN** 云端评估某详情页后决定 `navigation.back`
- **THEN** 该 `navigation.back` 指令携带 `dwellMs`，其值由云端依据已上报内容与风控状态算出

#### Scenario: 旧边缘忽略未知时间字段

- **WHEN** 边缘版本早于本 change、收到带 `dwellMs` / `thinkMs` 的指令
- **THEN** 边缘忽略该字段、按内置默认兜底运行，行为不劣化（向后兼容）

### Requirement: 详情页返回兜底，杜绝秒退

边缘在**离开一条内容前** SHALL 确保该内容实际停留 ≥ `jitter(dwellMs ?? builtinFloor)`。「离开一条内容」既包括从详情页执行 `navigation.back` 返回，也包括在信息流就地读完一条后发出的**下一条 `{platform}.feed.scroll`**。无论指令是否携带 `dwellMs`，内容页 MUST NOT 出现快到不像人能完成感知判断的瞬时离开（零延迟秒退）。

#### Scenario: 带时长的无价值详情页不秒退

- **WHEN** 云端判无价值并下发带 `dwellMs` 的 `navigation.back`
- **THEN** 边缘把返回推迟到实际停留 ≥ `jitter(dwellMs)` 之后才执行

#### Scenario: 缺时长仍不秒退

- **WHEN** `navigation.back` 未携带 `dwellMs`（旧云端 / 断连）
- **THEN** 边缘仍用内置 `builtinFloor` 保证详情页非零停留后才返回

#### Scenario: feed 内联读完不秒滚离开

- **WHEN** 边缘在信息流就地读完一条内容，随后要发出 `{platform}.feed.scroll` 离开它
- **THEN** 边缘保证从内联读开始时刻起实际停留 ≥ 抖动后的本地 read floor 才滚动
- **AND** 不因就地读比进详情页快而出现零延迟秒滚

### Requirement: 缺时间指令时的安全降级

边缘在未收到时间字段（旧云端 / 断连 / 自主动作）时 SHALL 回退到内置默认下限，MUST NOT 退化为零延迟。兜底默认经 `welcome` 握手响应的可选 `pacing` 快照下发（`tempo?` 标量 + 每类操作 floor 区间 `opFloorsMs?`）供边缘最小间隔 gating、详情页停留兜底与断连兜底使用；该快照 MUST NOT 包含 read / pause / fatigue 系数（这些收口在云端，随决策指令以 `dwellMs` / `thinkMs` 下发）。快照缺失或某字段缺失时边缘 SHALL 逐字段回落内置非零默认，MUST NOT 回落零。

边缘在缺 `dwellMs` 而回落内置详情页停留兜底（从 `dwellFloorTiming` 采样）时 SHALL 对采样中心值叠加**当前生效的 `tempo` 档位**放大（与云端计算 `dwellMs` 同向：风控越差、兜底停留越长），但 MUST NOT 对云端**已下发的 `dwellMs`** 再叠 `tempo`（云端 `computeDwellMs` 已烘入 `tempo`，二次叠会 double-count）。

`session.budget.pacing` 通道 SHALL 从协议中移除（删除 `PacingDefaultsPayload` 类型与 `SessionBudgetPayload.pacing` 字段）：边缘从不请求 `session.budget`、也从不消费其 `pacing` 字段，云端 MUST NOT 再以该通道下发任何兜底默认；兜底默认的唯一下发路径为 `welcome` 快照。`session.budget` 消息其余字段（预算 + `viewOnly`）不受影响。

#### Scenario: 断连仍非零延迟

- **WHEN** 边缘在没有任何时间指令、且无 `welcome` pacing 快照的情况下运行
- **THEN** 各决策节点与详情页返回仍使用边缘内置非零默认下限，不出现零延迟秒退

#### Scenario: 握手快照仅含兜底参数

- **WHEN** 云端在 `welcome` 下发 `pacing` 快照
- **THEN** 该对象仅含 `tempo` 与每类操作 floor 区间等兜底字段，不含内容相关的 read / pause / fatigue 系数

#### Scenario: 兜底停留随档位放慢

- **WHEN** 边缘在缺 `dwellMs` 时回落内置详情页停留兜底，且当前生效 `tempo` 为 `warned` / `restricted` 档（>1）
- **THEN** 采样得到的兜底停留中心值按 `tempo` 放大（风控越差停留越长），仍叠 lognormal 抖动与非零下限

#### Scenario: 云端已下发 dwellMs 不再叠 tempo

- **WHEN** 云端下发带 `dwellMs` 的 `navigation.back` / `{platform}.note.close`（该值已含云端烘入的 `tempo`）
- **THEN** 边缘以该 `dwellMs` 为中心值、只叠抖动，MUST NOT 再乘 `this.tempo`（避免风控放慢被计两次）

#### Scenario: 不经废弃通道下发

- **WHEN** 云端需要向边缘提供兜底默认
- **THEN** 经 `welcome` 快照下发；协议中不再存在 `session.budget.pacing` 字段，边缘不请求也不消费 `session.budget` 的节奏字段

### Requirement: feed 翻页携带按新卡数计的可选停留时长

云端 → 边缘的 feed 翻页指令（`{platform}.feed.scroll`）SHALL 支持可选的 `dwellMs` 字段，表示"看完本次翻页冒出的新卡片"应达到的停留时长。该值由云端依据**本次翻页新出现的卡片数**算出。当本次翻页**没有新卡**（返回未刷新、同一批卡）时，云端 MUST NOT 在 `{platform}.feed.scroll` 上携带 `dwellMs`，边缘据此不叠加任何额外延迟。字段可选，缺失视为合法。

#### Scenario: 出新卡的翻页带停留时长

- **WHEN** 云端处理一次 feed 卡片上报，发现其中含若干**未见过**的卡片，随后决定继续翻页
- **THEN** 该 `{platform}.feed.scroll` 指令携带 `dwellMs`，其值与新卡片数正相关

#### Scenario: 返回未刷新的翻页不带停留时长

- **WHEN** 从详情页返回 feed 后收到的卡片与上一批**完全相同**（新卡数为 0），云端随后决定翻页
- **THEN** 该 `{platform}.feed.scroll` 指令**不携带** `dwellMs`，边缘翻页不叠加任何额外延迟

#### Scenario: 旧边缘忽略未知停留字段

- **WHEN** 边缘版本早于本 change、收到带 `dwellMs` 的 `{platform}.feed.scroll`
- **THEN** 边缘忽略该字段、按原有行为翻页，不劣化（向后兼容）

### Requirement: 边缘保证 feed 翻页停留达标且不与详情页停留双算

边缘收到带 `dwellMs` 的 `{platform}.feed.scroll` / `facebook.reels.scroll` SHALL 叠加一层 lognormal 抖动后，保证从**本次新卡到达时刻**起的停留不小于抖动后的值（未达标则补足等待后再翻页）；已过去的时间（如云端评估卡片的往返耗时）MUST 被计入、只补足**差额**，模型评估较慢时边缘 MAY 不再额外等待。该要求 MUST 同等适用于 Native-only Facebook Feed 与 Reels 路径；Native 命令映射或执行层 MUST NOT 接收字段后静默丢弃。收到无 `dwellMs` / `dwellMs ≤ 0` 的 `{platform}.feed.scroll` / `facebook.reels.scroll` 时边缘 MUST 立即翻页、不叠加额外延迟。feed 停留 MUST 独立于详情页停留：两者锚点（新卡到达 vs 打开笔记）与触发命令（`{platform}.feed.scroll` vs `navigation.back`/`{platform}.note.close`）不同，MUST NOT 相互叠加或重复计时。当本条内容是信息流就地读时，停留还引入第三锚点（内联读开始时刻 `inlineReadStartedAt` 起的边缘本地 read floor）；三个锚点（新卡到达、详情页打开、内联读开始）之间 MUST 取 max、MUST NOT 相加。

#### Scenario: 评估耗时被吸收进停留

- **WHEN** 云端评估本批新卡花费的时间已超过抖动后的 feed 停留目标，随后下发带 `dwellMs` 的 `{platform}.feed.scroll`
- **THEN** 边缘立即翻页、不再额外等待（停留目标已被评估耗时满足，无双重延迟）

#### Scenario: Native Facebook Reels 消费停留字段

- **WHEN** Native-only Facebook Reels 在新卡到达后很快收到带 `dwellMs` 的 `facebook.reels.scroll`
- **THEN** 边缘只补足抖动后目标与已用时间的正差额，再执行可信 Reels 翻页输入

#### Scenario: 无停留字段立即翻页

- **WHEN** `{platform}.feed.scroll` 未携带 `dwellMs`（返回未刷新 / 旧云端 / 断连）
- **THEN** 边缘立即翻页、不叠加任何额外停留

#### Scenario: feed 停留与详情页停留互不叠加

- **WHEN** 边缘在 feed 上因新卡叠了停留，随后打开一条笔记再返回
- **THEN** 详情页返回停留只由 `navigation.back` 的 `dwellMs` 决定，与之前的 feed 停留互不影响、不重复计时

#### Scenario: 内联读停留与翻页停留取 max 不相加

- **WHEN** 边缘在信息流就地读完一条（`inlineReadStartedAt` 起的本地 read floor 未达），随后收到带 `dwellMs` 的 `{platform}.feed.scroll`
- **THEN** 边缘按内联读 read floor 与新卡停留目标的较大者保证停留，二者 MUST NOT 相加

### Requirement: 操作间隔按最小间隔 gating，等待与兜底不累加

边缘在执行「操作类」命令（`{platform}.note.open` / `xiaohongshu.profile.open` / `interaction.*` / `xiaohongshu.note.browse_images` / `xiaohongshu.note.scroll_comments`）前 SHALL 采用**最小间隔**语义而非无条件附加固定等待：维护**单一锚点**记录上次操作完成时刻（`lastActionEndAt`，取自**单调时钟**），收到下一个操作时计算 `elapsed = monoNow() − lastActionEndAt`、`remaining = max(0, floor − elapsed)`，仅补足 `remaining` 后执行。云端决策/网络往返耗时 MUST 计入 `elapsed`——已达兜底则立即执行、**MUST NOT** 在其之上再叠加兜底（不累加）。动作前犹豫 `thinkMs`（若下发）与最小间隔测同一「now→执行本动作」跨度，两者取 `max`、**MUST NOT** 相加。锚点在进程启动 / 断连重连 / CDP 重连时重置为空（首操作跳过间隔，由会话起点扫描延迟兜底）。详情页停留（`ensureDetailDwell`）与 feed 停留（`ensureFeedDwell`）测另一跨度，保留各自锚点，MUST NOT 与操作间隔叠闸（防双计）。

#### Scenario: 云端返回慢则立即执行、不再叠加

- **WHEN** 上次操作完成后，云端决策 + 往返耗时已达到本次操作的兜底 floor（`elapsed ≥ floor`）
- **THEN** 边缘立即执行本操作，不再额外等待（往返耗时被吸收，等待与兜底不累加）

#### Scenario: 云端返回快则只补差额

- **WHEN** 距上次操作完成的 `elapsed` 小于本次操作的兜底 floor
- **THEN** 边缘仅等待 `floor − elapsed` 补足差额后执行，实际间隔恰达 floor 而非 `elapsed + floor`

#### Scenario: 首操作与重连后无锚点跳过间隔

- **WHEN** 会话首个操作，或断连/CDP 重连后清空锚点后的首个操作
- **THEN** 不施加操作间隔（`thinkMs` 仍守非零下限），由会话起点扫描延迟兜底

#### Scenario: 单调时钟防跳变

- **WHEN** 运行期系统墙钟发生 NTP 校正或改表（后跳/前跳）
- **THEN** `elapsed` 由单调时钟计得、不受影响，不会因墙钟回拨变负导致卡死、也不会因前跳暴增导致间隔失效

### Requirement: Facebook page-scroll pacing uses one slower bounded policy

Cloud SHALL use one Facebook platform page-scroll floor for the existing shared Facebook scroll outlet (`facebook.feed.scroll` / `facebook.search.scroll` / `facebook.reels.scroll`). At normal tempo, the floor's center SHALL be 11,000 milliseconds for both Feed and Reels; warned and restricted states SHALL continue to scale that center through the existing Cloud-owned `effectiveTempo`, and any larger existing card-derived floor SHALL still win. The shared outlet's existing scope, including Facebook search and recovery scrolls, SHALL remain unchanged rather than introducing a second list-surface state solely for pacing.

Edge SHALL apply the wider distribution only to Facebook scroll commands (`facebook.feed.scroll` / `facebook.search.scroll` / `facebook.reels.scroll`): a multiplicative lognormal sample with `sigma=0.30`, centered at the Cloud-provided `dwellMs`, reflected into `0.55x..1.90x` of that center and capped at 60,000 milliseconds. Reflection MUST be used instead of hard clipping, and non-Facebook scrolls (`xiaohongshu.feed.scroll` / `xiaohongshu.search.scroll`), detail dwell, think delays, action gating, and gesture physics MUST retain their existing timing behavior.

The Edge wait SHALL remain the positive difference between the sampled target and time already elapsed since the content-batch anchor. An inline-read remainder SHALL be combined by maximum, not addition. The pacing wait MUST remain abortable and outside the Native page-operation execution budget; this change MUST NOT enlarge the established 15-second Reel identity hydration, 18-second post-input reserve, 180-second `page_scroll` execution, 200/240-second idle recovery, 3,600-second session end, or 5-second quiesce windows.

#### Scenario: Feed and Reels share the 11-second normal center

- **WHEN** Cloud emits an admitted Facebook Feed or Reels scroll (`facebook.feed.scroll` / `facebook.reels.scroll`) at normal tempo and no larger card-derived floor applies
- **THEN** it supplies `dwellMs=11000` through the same shared scroll outlet

#### Scenario: Risk tempo scales before Edge jitter

- **WHEN** the same Facebook scroll is emitted under warned or restricted pacing
- **THEN** Cloud first increases the 11-second center with its existing `effectiveTempo`, and Edge jitters that already-scaled center without multiplying tempo again

#### Scenario: Facebook jitter is wider and bounded without wall clipping

- **WHEN** Edge receives a Facebook scroll command (`facebook.feed.scroll` / `facebook.search.scroll` / `facebook.reels.scroll`) with positive `dwellMs`
- **THEN** its sampled target uses `sigma=0.30`, reflects into `0.55x..1.90x` of the center, never exceeds 60 seconds, and does not accumulate samples at a hard-clipped boundary

#### Scenario: Existing elapsed time still satisfies the target

- **WHEN** Cloud evaluation and page observation have already consumed all or part of the sampled Facebook target
- **THEN** Edge waits only the remaining positive difference, combines any inline-read remainder by maximum, and waits zero when the target is already satisfied

#### Scenario: Other timing behavior is unchanged

- **WHEN** Edge handles a non-Facebook scroll, detail dwell, think delay, action gate, or scrolling gesture
- **THEN** it uses the pre-existing timing and motion rules rather than the Facebook page-scroll distribution

#### Scenario: Existing timeout budgets remain independent

- **WHEN** a bounded Facebook pacing wait precedes a Native Reel or Feed scroll
- **THEN** the wait remains abortable, the Native page-operation timeout begins independently afterward, and none of the established hydration, input-reserve, execution, idle, session-end, or quiesce windows is enlarged

