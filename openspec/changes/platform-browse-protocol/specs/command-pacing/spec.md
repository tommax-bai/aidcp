## MODIFIED Requirements

### Requirement: 详情页返回兜底，杜绝秒退

边缘在**离开一条内容前** SHALL 确保该内容实际停留 ≥ `jitter(dwellMs ?? builtinFloor)`。「离开一条内容」既包括从详情页执行 `navigation.back` 返回，也包括在信息流就地读完一条后发出的**下一条 `page.scroll`**。无论指令是否携带 `dwellMs`，内容页 MUST NOT 出现快到不像人能完成感知判断的瞬时离开（零延迟秒退）。

#### Scenario: 带时长的无价值详情页不秒退

- **WHEN** 云端判无价值并下发带 `dwellMs` 的 `navigation.back`
- **THEN** 边缘把返回推迟到实际停留 ≥ `jitter(dwellMs)` 之后才执行

#### Scenario: 缺时长仍不秒退

- **WHEN** `navigation.back` 未携带 `dwellMs`（旧云端 / 断连）
- **THEN** 边缘仍用内置 `builtinFloor` 保证详情页非零停留后才返回

#### Scenario: feed 内联读完不秒滚离开

- **WHEN** 边缘在信息流就地读完一条内容，随后要发出 `page.scroll` 离开它
- **THEN** 边缘保证从内联读开始时刻起实际停留 ≥ 抖动后的本地 read floor 才滚动
- **AND** 不因就地读比进详情页快而出现零延迟秒滚

### Requirement: 边缘保证 feed 翻页停留达标且不与详情页停留双算

边缘收到带 `dwellMs` 的 `page.scroll` SHALL 叠加一层 lognormal 抖动后，保证从**本次新卡到达时刻**起的停留不小于抖动后的值（未达标则补足等待后再翻页）；已过去的时间（如云端评估卡片的往返耗时）MUST 被计入、只补足**差额**，模型评估较慢时边缘 MAY 不再额外等待。收到无 `dwellMs` / `dwellMs ≤ 0` 的 `page.scroll` 时边缘 MUST 立即翻页、不叠加额外延迟。feed 停留 MUST 独立于详情页停留：两者锚点（新卡到达 vs 打开笔记）与触发命令（`page.scroll` vs `navigation.back`/`note.close`）不同，MUST NOT 相互叠加或重复计时。当本条内容是信息流就地读时，停留还引入第三锚点（内联读开始时刻 `inlineReadStartedAt` 起的边缘本地 read floor）；三个锚点（新卡到达、详情页打开、内联读开始）之间 MUST 取 max、MUST NOT 相加。

#### Scenario: 评估耗时被吸收进停留

- **WHEN** 云端评估本批新卡花费的时间已超过抖动后的 feed 停留目标，随后下发带 `dwellMs` 的 `page.scroll`
- **THEN** 边缘立即翻页、不再额外等待（停留目标已被评估耗时满足，无双重延迟）

#### Scenario: 无停留字段立即翻页

- **WHEN** `page.scroll` 未携带 `dwellMs`（返回未刷新 / 旧云端 / 断连）
- **THEN** 边缘立即翻页、不叠加任何额外停留

#### Scenario: feed 停留与详情页停留互不叠加

- **WHEN** 边缘在 feed 上因新卡叠了停留，随后打开一条笔记再返回
- **THEN** 详情页返回停留只由 `navigation.back` 的 `dwellMs` 决定，与之前的 feed 停留互不影响、不重复计时

#### Scenario: 内联读停留与翻页停留取 max 不相加

- **WHEN** 边缘在信息流就地读完一条（`inlineReadStartedAt` 起的本地 read floor 未达），随后收到带 `dwellMs` 的 `page.scroll`
- **THEN** 边缘按内联读 read floor 与新卡停留目标的较大者保证停留，二者 MUST NOT 相加
