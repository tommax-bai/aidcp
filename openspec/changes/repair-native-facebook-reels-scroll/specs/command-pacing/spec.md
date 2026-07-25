## MODIFIED Requirements

### Requirement: 边缘保证 feed 翻页停留达标且不与详情页停留双算

边缘收到带 `dwellMs` 的 `page.scroll` SHALL 叠加一层 lognormal 抖动后，保证从**本次新卡到达时刻**起的停留不小于抖动后的值（未达标则补足等待后再翻页）；已过去的时间（如云端评估卡片的往返耗时）MUST 被计入、只补足**差额**，模型评估较慢时边缘 MAY 不再额外等待。该要求 MUST 同等适用于 Native-only Facebook Feed 与 Reels 路径；Native 命令映射或执行层 MUST NOT 接收字段后静默丢弃。收到无 `dwellMs` / `dwellMs ≤ 0` 的 `page.scroll` 时边缘 MUST 立即翻页、不叠加额外延迟。feed 停留 MUST 独立于详情页停留：两者锚点（新卡到达 vs 打开笔记）与触发命令（`page.scroll` vs `navigation.back`/`note.close`）不同，MUST NOT 相互叠加或重复计时。当本条内容是信息流就地读时，停留还引入第三锚点（内联读开始时刻 `inlineReadStartedAt` 起的边缘本地 read floor）；三个锚点（新卡到达、详情页打开、内联读开始）之间 MUST 取 max、MUST NOT 相加。

#### Scenario: 评估耗时被吸收进停留

- **WHEN** 云端评估本批新卡花费的时间已超过抖动后的 feed 停留目标，随后下发带 `dwellMs` 的 `page.scroll`
- **THEN** 边缘立即翻页、不再额外等待（停留目标已被评估耗时满足，无双重延迟）

#### Scenario: Native Facebook Reels 消费停留字段

- **WHEN** Native-only Facebook Reels 在新卡到达后很快收到带 `dwellMs` 的 `page.scroll`
- **THEN** 边缘只补足抖动后目标与已用时间的正差额，再执行可信 Reels 翻页输入

#### Scenario: 无停留字段立即翻页

- **WHEN** `page.scroll` 未携带 `dwellMs`（返回未刷新 / 旧云端 / 断连）
- **THEN** 边缘立即翻页、不叠加任何额外停留

#### Scenario: feed 停留与详情页停留互不叠加

- **WHEN** 边缘在 feed 上因新卡叠了停留，随后打开一条笔记再返回
- **THEN** 详情页返回停留只由 `navigation.back` 的 `dwellMs` 决定，与之前的 feed 停留互不影响、不重复计时

#### Scenario: 内联读停留与翻页停留取 max 不相加

- **WHEN** 边缘在信息流就地读完一条（`inlineReadStartedAt` 起的本地 read floor 未达），随后收到带 `dwellMs` 的 `page.scroll`
- **THEN** 边缘按内联读 read floor 与新卡停留目标的较大者保证停留，二者 MUST NOT 相加
