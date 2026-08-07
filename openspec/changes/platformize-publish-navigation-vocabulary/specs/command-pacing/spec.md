## MODIFIED Requirements

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
