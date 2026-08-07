# command-pacing

## Purpose

指令级节奏（Command Pacing）：云端基于**已上报内容** + 风控状态算出"停留 / 思考"时长中心值，
随决策指令（`navigation.back`/`{platform}.note.close` 带 `dwellMs`，`interaction.*`/`{platform}.note.open` 带 `thinkMs`）
下发；边缘叠 lognormal 抖动、保证详情页实际停留达标（治"无价值秒退"）、并对缺失情况兜底。
内容相关的时间系数收口在云端一处，不下发系数；`session.budget.pacing` 仅携带极薄兜底默认。
## Requirements
### Requirement: 决策指令携带可选时间指令

云端 → 边缘的决策指令 SHALL 支持可选的时间字段：`{platform}.navigation.back` 携带
`dwellMs`（离开当前页前应达到的总停留时间），`{platform}.note.like` / `xiaohongshu.note.collect` /
`{platform}.user.follow` / `{platform}.note.open` 携带 `thinkMs`（执行动作前的犹豫 / 感知时间）。时间字段
全部可选，缺失视为合法，边缘按内置默认兜底。云端 MUST NOT 在 `session.budget` 下发整套时间
系数要求边缘自行套公式计算内容相关时长。

#### Scenario: 返回指令带停留时长

- **WHEN** 云端评估某详情页后决定 `{platform}.navigation.back`
- **THEN** 该 `{platform}.navigation.back` 指令携带 `dwellMs`，其值由云端依据已上报内容与风控状态算出

#### Scenario: 旧边缘忽略未知时间字段

- **WHEN** 边缘版本早于本 change、收到带 `dwellMs` / `thinkMs` 的指令
- **THEN** 边缘忽略该字段、按内置默认兜底运行，行为不劣化（向后兼容）

### Requirement: 云端基于已上报内容与风控状态计算时长

云端 SHALL 在产出决策时，基于**已通过 `note.detail` 上报的正文长度与图片 / 计数** + 风控状态
`tempo` 乘子（`normal / warned / restricted` 单调放慢）+ 会话进度疲劳因子，计算 `dwellMs` /
`thinkMs` 的中心值；§3 时间系数收口在云端一处，不下发给边缘。计算 MUST NOT 引入额外的
请求 / 响应往返（时间字段挂在云端本就要下发的决策指令上）。

#### Scenario: 停留时长随内容量缩放

- **WHEN** 云端先后评估一条短笔记与一条长图文笔记并均决定返回
- **THEN** 长图文笔记 `{platform}.navigation.back` 的 `dwellMs` 显著大于短笔记（时长与上报内容量正相关）

#### Scenario: 风控降级整体放慢

- **WHEN** 账号风控状态由 `normal` 迁移至 `warned`
- **THEN** 同等内容下指令携带的 `dwellMs` / `thinkMs` 中心值显著增大（`tempo` 放大）

### Requirement: 边缘对时间指令叠加抖动并保证达标

边缘收到 `dwellMs` SHALL 叠加一层 lognormal 抖动后，保证当前页**实际停留**不小于抖动后的值
（未达标则补足等待后再执行）；收到 `thinkMs` SHALL 在执行该动作**前**等待抖动后的时长。边缘
MUST 对相同的云端中心值产生**带随机性**的实际时序（避免确定性指纹）。子动作的运动时序
（逐帧滚动 / 鼠标轨迹 / 逐键输入）由边缘执行层自带，不受时间指令字段影响。

#### Scenario: 同一中心值不产生相同时序

- **WHEN** 边缘两次收到相同 `dwellMs` 的返回指令
- **THEN** 两次实际停留时长不同（各自叠加了 lognormal 抖动）

#### Scenario: 有价值阅读不叠加下限

- **WHEN** 边缘在详情页的真实阅读停留已超过 `jitter(dwellMs)` 后收到返回指令
- **THEN** 返回不再额外等待（下限让位于真实阅读时间，无双重延迟）

### Requirement: 详情页返回兜底，杜绝秒退

边缘在**离开一条内容前** SHALL 确保该内容实际停留 ≥ `jitter(dwellMs ?? builtinFloor)`。「离开一条内容」既包括从详情页执行 `{platform}.navigation.back` 返回，也包括在信息流就地读完一条后发出的**下一条 `{platform}.feed.scroll`**。无论指令是否携带 `dwellMs`，内容页 MUST NOT 出现快到不像人能完成感知判断的瞬时离开（零延迟秒退）。

#### Scenario: 带时长的无价值详情页不秒退

- **WHEN** 云端判无价值并下发带 `dwellMs` 的 `{platform}.navigation.back`
- **THEN** 边缘把返回推迟到实际停留 ≥ `jitter(dwellMs)` 之后才执行

#### Scenario: 缺时长仍不秒退

- **WHEN** `{platform}.navigation.back` 未携带 `dwellMs`（旧云端 / 断连）
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

- **WHEN** 云端下发带 `dwellMs` 的 `{platform}.navigation.back`（该值已含云端烘入的 `tempo`）
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

### Requirement: 云端按新卡片数计算 feed 停留中心值

云端 SHALL 在产出 feed 翻页决策时，基于**本次翻页新出现的卡片数** + 风控状态 `tempo` 乘子 + 会话进度疲劳因子，计算 feed 停留 `dwellMs` 的中心值；该计算 MUST 复用与详情页停留 / 思考同一套 `tempo` 与疲劳系数（收口云端，不下发系数）。新卡数为 0 时中心值 MUST 为 0。中心值 MUST 有上限封顶（整屏换新不至于产生过长停留）。计算 MUST NOT 引入额外请求 / 响应往返（时间字段挂在本就要下发的翻页指令上）。

#### Scenario: 停留时长随新卡片数缩放

- **WHEN** 一次翻页冒出 3–4 张新卡，另一次整屏下拉冒出 10+ 张新卡
- **THEN** 后者的 `dwellMs` 中心值显著大于前者，且不超过封顶上限

#### Scenario: 风控降级整体放慢

- **WHEN** 账号风控状态由 `normal` 迁移至 `warned`
- **THEN** 同等新卡数下 feed 翻页 `dwellMs` 中心值显著增大（`tempo` 放大）

#### Scenario: 无新卡则中心值为零

- **WHEN** 本次翻页的新卡数为 0
- **THEN** 云端算得的 feed 停留中心值为 0（不下发 `dwellMs`）

### Requirement: 新卡识别按卡片身份差分且仅限 feed 来源

云端 SHALL 通过比对本次上报卡片的稳定身份（`noteId`）与"上一批 feed 卡"的身份集合，得出本次的**新卡数**（不在集合中的数量），并随后用本次卡片身份刷新该集合。新卡识别与集合刷新 MUST 仅在**来源为 feed** 的卡片上报上进行，MUST NOT 因搜索结果页的卡片上报而写入或消费 feed 集合。缺失 `noteId` 的卡片 MUST 计为"非新卡"（不计入新卡数）——此偏差方向只会**少加**停留，绝不产生零延迟秒滑或伪造计数。

#### Scenario: 部分重叠只计真正的新卡

- **WHEN** 一次翻页后的卡片与上一批部分重叠（含旧卡 + 新卡）
- **THEN** 新卡数只计入身份不在上一批集合中的那部分，`dwellMs` 与其成正比

#### Scenario: 搜索页不污染 feed 集合

- **WHEN** 系统在搜索结果页收到卡片上报
- **THEN** 该上报不写入也不消费 feed 的"上一批卡"集合，不影响后续 feed 翻页的新卡判定

#### Scenario: 无身份卡片按非新卡处理

- **WHEN** 本次上报中若干卡片缺少可解析的 `noteId`
- **THEN** 这些卡片不计入新卡数（宁可少加停留），且不会使"返回未刷新"被误判为出新卡

### Requirement: 边缘保证 feed 翻页停留达标且不与详情页停留双算

边缘收到带 `dwellMs` 的 `{platform}.feed.scroll` / `facebook.reels.scroll` SHALL 叠加一层 lognormal 抖动后，保证从**本次新卡到达时刻**起的停留不小于抖动后的值（未达标则补足等待后再翻页）；已过去的时间（如云端评估卡片的往返耗时）MUST 被计入、只补足**差额**，模型评估较慢时边缘 MAY 不再额外等待。该要求 MUST 同等适用于 Native-only Facebook Feed 与 Reels 路径；Native 命令映射或执行层 MUST NOT 接收字段后静默丢弃。收到无 `dwellMs` / `dwellMs ≤ 0` 的 `{platform}.feed.scroll` / `facebook.reels.scroll` 时边缘 MUST 立即翻页、不叠加额外延迟。feed 停留 MUST 独立于详情页停留：两者锚点（新卡到达 vs 打开笔记）与触发命令（`{platform}.feed.scroll` vs `{platform}.navigation.back`）不同，MUST NOT 相互叠加或重复计时。当本条内容是信息流就地读时，停留还引入第三锚点（内联读开始时刻 `inlineReadStartedAt` 起的边缘本地 read floor）；三个锚点（新卡到达、详情页打开、内联读开始）之间 MUST 取 max、MUST NOT 相加。

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
- **THEN** 详情页返回停留只由 `{platform}.navigation.back` 的 `dwellMs` 决定，与之前的 feed 停留互不影响、不重复计时

#### Scenario: 内联读停留与翻页停留取 max 不相加

- **WHEN** 边缘在信息流就地读完一条（`inlineReadStartedAt` 起的本地 read floor 未达），随后收到带 `dwellMs` 的 `{platform}.feed.scroll`
- **THEN** 边缘按内联读 read floor 与新卡停留目标的较大者保证停留，二者 MUST NOT 相加

### Requirement: 熟悉内容的思考时间按近期已评估折扣

云端计算动作 `thinkMs` 时 SHALL 引入"熟悉度"维度：当动作目标内容**近期已被评估过**（命中会话内**有界近期已评估集合**，约最近 30 个 `noteId`）时，`thinkMs` 中心值 SHALL 按固定折扣（约**常规的 1/3**）缩小，且 MUST 保留一个**非零下限**（不得退化为零延迟）。目标内容**未在近期已评估集合内**（全新）时，`thinkMs` 按全量中心值。该折扣 MUST NOT 影响 `dwellMs`（刚读笔记的停留不被缩减）。云端 SHALL 维护该有界近期已评估集合（评估某批卡片时标记其 `noteId`，超出容量淘汰最旧）。

二次评估行为保持不变：返回 feed 后云端仍对候选卡片正常评估（本要求只改"思考时长"，MUST NOT 借此跳过或复用评估）。

#### Scenario: 打开近期已评估过的卡片，思考时间约降至 1/3

- **WHEN** 云端对一张近期已评估过（命中近期已评估集合）的卡片下发 `open_note`
- **THEN** 该 `open_note` 的 `thinkMs` 中心值约为常规全量值的 1/3，且为非零

#### Scenario: 全新卡片思考时间为全量

- **WHEN** 云端对一张未在近期已评估集合内的新卡片下发带 `thinkMs` 的动作
- **THEN** `thinkMs` 为全量中心值（不折扣）

#### Scenario: 折扣不波及笔记停留 dwell

- **WHEN** 熟悉折扣对 `thinkMs` 生效的同时，云端为刚读过的笔记下发 `{platform}.navigation.back` 的 `dwellMs`
- **THEN** 该 `dwellMs`（read 量级停留）不被折扣，详情页仍不秒退

#### Scenario: 超出近期窗口不再享折扣

- **WHEN** 某 `noteId` 的评估记录已被挤出有界近期已评估集合（不在最近约 30 个内）
- **THEN** 再次对其下发动作时 `thinkMs` 按全量处理（不折扣）

### Requirement: 返回熟悉 feed 的手势与落地更快但不秒退

边缘执行 `{platform}.navigation.back` 且 `reason==='back_to_feed'`（必然返回到打开笔记前的同一批、刚刚看过的 feed）时，返回手势停顿与 `history.back` 之后的固定落地等待 SHALL 按折扣（约**常规的 1/3**）缩短，且 MUST 保留**非零下限**（仍带抖动、不出现零延迟瞬时返回）。该折扣 MUST NOT 缩减离开笔记前的停留下限（`ensureDetailDwell` / 笔记 `dwellMs` 不变），也 MUST NOT 削弱返回后的坏页 / 404 健康校验兜底。

#### Scenario: 返回熟悉 feed 手势更快

- **WHEN** 边缘执行 `{platform}.navigation.back{reason:'back_to_feed'}`
- **THEN** 返回手势停顿与返回后固定落地等待约降至常规的 1/3（带非零下限），更快进入续刷

#### Scenario: 返回手势仍非零、不秒退

- **WHEN** 任意 `back_to_feed` 返回
- **THEN** 返回前仍存在非零的手势停顿，且离开笔记前的停留下限不被该折扣影响

#### Scenario: 非 back_to_feed 返回不受影响

- **WHEN** 边缘执行的返回不是 `back_to_feed`（如回到搜索结果）
- **THEN** 不应用该折扣，返回时序按现状

### Requirement: 操作间隔按最小间隔 gating，等待与兜底不累加

边缘在执行「操作类」命令（`{platform}.note.open` / `xiaohongshu.profile.open` / 互动写命令（`{platform}.note.like`、`facebook.video.like`、`xiaohongshu.note.collect`、`{platform}.user.follow`、`{platform}.note.comment`、`xiaohongshu.comment.like`）/ `xiaohongshu.note.browse_images` / `xiaohongshu.note.scroll_comments`）前 SHALL 采用**最小间隔**语义而非无条件附加固定等待：维护**单一锚点**记录上次操作完成时刻（`lastActionEndAt`，取自**单调时钟**），收到下一个操作时计算 `elapsed = monoNow() − lastActionEndAt`、`remaining = max(0, floor − elapsed)`，仅补足 `remaining` 后执行。云端决策/网络往返耗时 MUST 计入 `elapsed`——已达兜底则立即执行、**MUST NOT** 在其之上再叠加兜底（不累加）。动作前犹豫 `thinkMs`（若下发）与最小间隔测同一「now→执行本动作」跨度，两者取 `max`、**MUST NOT** 相加。锚点在进程启动 / 断连重连 / CDP 重连时重置为空（首操作跳过间隔，由会话起点扫描延迟兜底）。详情页停留（`ensureDetailDwell`）与 feed 停留（`ensureFeedDwell`）测另一跨度，保留各自锚点，MUST NOT 与操作间隔叠闸（防双计）。

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

### Requirement: 兜底 floor 全局后台可配置，经握手下发并热加载

系统 SHALL 支持在后台（console）编辑每类操作的兜底 floor 区间 `{minMs, maxMs}`，存于云端 PostgreSQL（`pacing_floor_config`，schema 启动自建、无迁移器），作用域为**全局一套**，覆盖四类操作 `action` / `scroll` / `card_gap` / `detail_dwell`。云端 SHALL 在 `welcome` 握手响应中携带可选 `pacing` 快照（`tempo` 标量 + 每类操作 floor 区间 `opFloorsMs`），供边缘最小间隔 gating 与详情页停留兜底取用。配置更新 SHALL 在各边缘**下次握手 / 重连**时生效（连接级热加载，无需重启云端）。表内无某 op 行时 SHALL 逐项回落内置非零默认（= 现役预设量级），保证零回归。边缘 SHALL 在**重连复用同一会话对象**时经 `applyPacingSnapshot` 重新注入新快照（MUST NOT 让连接级快照在重连路径退化成进程级）。

#### Scenario: 后台改值下次握手生效

- **WHEN** 运营在 console 把 `action` 的兜底区间调大并保存，随后某边缘重连握手
- **THEN** 该边缘取到新区间，其后续 `action` 类操作的最小间隔按新值 gating

#### Scenario: 配置缺某 op 逐项回落内置默认

- **WHEN** `pacing_floor_config` 表中缺 `scroll` 行、其余 op 有行
- **THEN** 边缘对 `scroll` 用内置非零默认、对其余 op 用下发值（逐字段回落、非全有全无）

#### Scenario: 重连重注入配置

- **WHEN** 边缘因身份翻转触发重连、复用同一会话对象，且期间云端配置已变更
- **THEN** 边缘经 `applyPacingSnapshot` 灌入新握手的 floors/tempo，新值在重连后立即生效

#### Scenario: 旧边缘忽略 pacing 快照

- **WHEN** 边缘版本早于本 change、收到带 `pacing` 的 `welcome`
- **THEN** 边缘忽略该字段、用内置非零默认运行，行为不劣化（向后兼容）

### Requirement: 绝不零延迟经三道夹逼保证，防指纹经反射采样

无论后台如何配置，系统 SHALL 保证有效兜底间隔恒大于每类操作的非零防呆下限——**配置只能抬高延迟、永远抬不穿非零下限**。该保证 SHALL 由三道夹逼共同实现：① facade 写入校验（`min/max` 非负整数、`min ≤ max`、`max ≥ min × 1.5` 最小展宽、`≤ CAP`，整块拒不部分落库）；② 云端读出口 `clamp(v, 防呆下限, CAP)`（权威夹点，即便有人绕过面板 psql 直插 0/负数/超界，离开云端进程前已夹成非零合法）；③ 边缘 `Math.max(防呆下限, ·)` 二次夹。CAP SHALL 为全局小常量（`CAP_MS = 15000`），结构上 MUST < 云端 idle 看门狗下限（`IDLE_NUDGE_MIN_MS = 200000`），并由不变量测试断言该常量关系。边缘每次现采样兜底目标，采样 SHALL 用**反射**而非硬裁（越界样本反弹回分布内），使被补齐的间隔散布成自然分布、MUST NOT 在固定 floor 值处堆积成尖峰（消除机器指纹左壁）。功能性 settle（等页面加载/编辑器出现/重渲染）与有界轮询/复检 MUST NOT 被折进最小间隔 gating（否则会打断真实前置条件 → 静默假成功）。

#### Scenario: 后台配零被夹回非零下限

- **WHEN** 运营（或直接 psql 写库）把某 op 的 `minMs` 设为 0 或负数
- **THEN** 经三道夹逼后边缘实测该 op 间隔仍 ≥ 其非零防呆下限，不出现零延迟

#### Scenario: 最小展宽校验拒绝零展宽

- **WHEN** 运营提交某 op 的 `min_ms == max_ms`（零展宽）
- **THEN** facade 拒绝该写入（`max_ms ≥ min_ms × 1.5` 不满足），不落库，防指纹分布不退化为单点

#### Scenario: 配大值不误触看门狗

- **WHEN** 运营把某 op 兜底配到很大
- **THEN** 经 `clamp(·, ·, CAP=15000)` 后有效间隔恒 ≤ 15s ≪ 200s，单次前台等待不触发 idle 看门狗杀会话

#### Scenario: 间隔分布不堆尖峰

- **WHEN** 大量操作因云端快回被补差额到兜底附近
- **THEN** 边缘反射采样使这批间隔散布成分布而非堆在同一固定值，无可识别的竖直左壁

### Requirement: 风控档位中途变化实时传播到边缘兜底

当账号在**一次稳定连接的会话中途**，因风控状态迁移（如 `normal → warned → restricted`）**或后台配额档调整**（`setQuotaLevel`，如 `normal → conservative`）导致**生效 tempo**（`effectiveTempo` = 风控状态 tempo 与配额档 tempo 取更慢者）变化时，云端 SHALL 主动把新的 `tempo` 推送给边缘（不依赖断连重连）；边缘 SHALL 据此更新其兜底节奏所用的 `tempo`，使最小间隔 gating 与内置停留兜底随之放慢。

该推送 MUST NOT 重置边缘的最小间隔锚点（`lastActionEndAt`）——中途档位刷新不等于重连，MUST NOT 借此跳过一次操作间隔。云端 SHALL 仅在 `tempo` 相对**上次已推送值**变化时推送（去抖，避免每命令冗余下发）；握手时边缘已由 `welcome` 快照取得初始 `tempo`，云端 MUST NOT 在无变化时重复推送。该推送为控制消息，MUST 经统一命令出口的原始下发通道直发，MUST NOT 消耗互动配额、MUST NOT 被软暂停闸抑制。该推送为向后兼容的可选消息：旧边缘忽略即可，行为不劣化。

#### Scenario: 中途升档实时放慢边缘兜底

- **WHEN** 会话稳定连接期间账号风控由 `normal` 迁移至 `warned`（`tempo` 1.0→1.3），且期间无断连重连
- **THEN** 云端把新 `tempo` 推送给边缘，边缘后续最小间隔 gating 与内置停留兜底按新 `tempo` 放大，无需等待一次重连

#### Scenario: 后台改配额档实时调速

- **WHEN** 运营在会话中途经后台把某账号配额档由 `normal` 改为 `conservative`（生效 tempo 1.0→1.3）
- **THEN** 云端在该账号下一次统一出口下发前推送 `pacing.update`，边缘当场按新 tempo 放慢——无需断连重连（此路径使 `pacing.update` 通道从 latent 转为日常可触发）

#### Scenario: 档位刷新不重置操作间隔锚点

- **WHEN** 边缘在两次操作之间收到中途 `tempo` 推送
- **THEN** 边缘更新 `tempo` 但保留 `lastActionEndAt` 锚点，不因此跳过或重置当前的最小间隔计时

#### Scenario: 无变化不冗余推送

- **WHEN** 账号生效 tempo 在会话中途保持不变（风控状态与配额档都未致 tempo 变化）
- **THEN** 云端不重复推送 `tempo`（仅在生效 tempo 实际变化时推送一次）

#### Scenario: 旧边缘忽略档位推送

- **WHEN** 边缘版本早于 change `pacing-fallback-hardening`、收到中途 `tempo` 推送消息
- **THEN** 边缘忽略该消息、继续用握手时的 `tempo`，行为不劣化（向后兼容）

### Requirement: 节奏 tempo 由风控状态与配额档共同取更慢者

云端计算节奏 tempo 时 SHALL 同时参考两个档位并取**更慢的一个**：`effectiveTempo(status, quotaLevel) = max(tempoForStatus(status), tempoForQuotaLevel(quotaLevel))`。其中配额档映射 `conservative` 放慢（与「被警告」同量级）、`normal` 与 `aggressive` 均不改变 tempo（`aggressive` 只放行更多配额、MUST NOT 提速到人类节奏基线以下——提速会削弱抗检测头寸）。

`effectiveTempo` MUST 作为所有 tempo 消费处的统一口径：决策中心值（`dwellMs`/`thinkMs`/feed 停留）、`welcome` 兜底快照、以及会话中途 `pacing.update` 推送与其去抖基线。两个因子 MUST 均为 ≥ 1.0 的放慢因子，故 `effectiveTempo` **只会更慢、绝不更快**（保守放慢、激进不提速）。默认账号 `quotaLevel=normal` 时 `effectiveTempo` 退化为 `tempoForStatus`（未配保守的账号行为零回归）。

#### Scenario: 保守账号即便风控正常也整体放慢

- **WHEN** 某账号风控状态为 `normal`（tempo 1.0）但配额档被后台配为 `conservative`
- **THEN** 其生效 tempo 为 1.3（保守放慢透出），决策中心值与兜底停留 / 最小间隔据此放大——保守 = 又少又慢

#### Scenario: 激进账号只多做、不提速

- **WHEN** 某账号配额档为 `aggressive`、风控 `normal`
- **THEN** 其生效 tempo 为 1.0（与 `normal` 账号相同）——激进只放行更多配额，动作停顿不压到人类基线以下

#### Scenario: 风控更差时盖过配额档

- **WHEN** 某 `conservative` 账号风控迁移到 `restricted`（status-tempo 1.6 > quota-tempo 1.3）
- **THEN** 生效 tempo 取更慢的 1.6（status 主导），配额档不再额外叠加

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

