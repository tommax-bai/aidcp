## ADDED Requirements

### Requirement: feed 翻页携带按新卡数计的可选停留时长

云端 → 边缘的 feed 翻页指令（`page.scroll`）SHALL 支持可选的 `dwellMs` 字段，表示"看完本次翻页冒出的新卡片"应达到的停留时长。该值由云端依据**本次翻页新出现的卡片数**算出。当本次翻页**没有新卡**（返回未刷新、同一批卡）时，云端 MUST NOT 在 `page.scroll` 上携带 `dwellMs`，边缘据此不叠加任何额外延迟。字段可选，缺失视为合法。

#### Scenario: 出新卡的翻页带停留时长

- **WHEN** 云端处理一次 feed 卡片上报，发现其中含若干**未见过**的卡片，随后决定继续翻页
- **THEN** 该 `page.scroll` 指令携带 `dwellMs`，其值与新卡片数正相关

#### Scenario: 返回未刷新的翻页不带停留时长

- **WHEN** 从详情页返回 feed 后收到的卡片与上一批**完全相同**（新卡数为 0），云端随后决定翻页
- **THEN** 该 `page.scroll` 指令**不携带** `dwellMs`，边缘翻页不叠加任何额外延迟

#### Scenario: 旧边缘忽略未知停留字段

- **WHEN** 边缘版本早于本 change、收到带 `dwellMs` 的 `page.scroll`
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

边缘收到带 `dwellMs` 的 `page.scroll` SHALL 叠加一层 lognormal 抖动后，保证从**本次新卡到达时刻**起的停留不小于抖动后的值（未达标则补足等待后再翻页）；已过去的时间（如云端评估卡片的往返耗时）MUST 被计入、只补足**差额**，模型评估较慢时边缘 MAY 不再额外等待。收到无 `dwellMs` / `dwellMs ≤ 0` 的 `page.scroll` 时边缘 MUST 立即翻页、不叠加额外延迟。feed 停留 MUST 独立于详情页停留：两者锚点（新卡到达 vs 打开笔记）与触发命令（`page.scroll` vs `navigation.back`/`note.close`）不同，MUST NOT 相互叠加或重复计时。

#### Scenario: 评估耗时被吸收进停留

- **WHEN** 云端评估本批新卡花费的时间已超过抖动后的 feed 停留目标，随后下发带 `dwellMs` 的 `page.scroll`
- **THEN** 边缘立即翻页、不再额外等待（停留目标已被评估耗时满足，无双重延迟）

#### Scenario: 无停留字段立即翻页

- **WHEN** `page.scroll` 未携带 `dwellMs`（返回未刷新 / 旧云端 / 断连）
- **THEN** 边缘立即翻页、不叠加任何额外停留

#### Scenario: feed 停留与详情页停留互不叠加

- **WHEN** 边缘在 feed 上因新卡叠了停留，随后打开一条笔记再返回
- **THEN** 详情页返回停留只由 `navigation.back` 的 `dwellMs` 决定，与之前的 feed 停留互不影响、不重复计时
