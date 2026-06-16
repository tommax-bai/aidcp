# command-pacing

## Purpose

指令级节奏（Command Pacing）：云端基于**已上报内容** + 风控状态算出"停留 / 思考"时长中心值，
随决策指令（`navigation.back`/`note.close` 带 `dwellMs`，`interaction.*`/`note.open` 带 `thinkMs`）
下发；边缘叠 lognormal 抖动、保证详情页实际停留达标（治"无价值秒退"）、并对缺失情况兜底。
内容相关的时间系数收口在云端一处，不下发系数；`session.budget.pacing` 仅携带极薄兜底默认。

## Requirements

### Requirement: 决策指令携带可选时间指令

云端 → 边缘的决策指令 SHALL 支持可选的时间字段：`navigation.back` / `note.close` 携带
`dwellMs`（离开当前页前应达到的总停留时间），`interaction.like` / `interaction.collect` /
`interaction.follow` / `note.open` 携带 `thinkMs`（执行动作前的犹豫 / 感知时间）。时间字段
全部可选，缺失视为合法，边缘按内置默认兜底。云端 MUST NOT 在 `session.budget` 下发整套时间
系数要求边缘自行套公式计算内容相关时长。

#### Scenario: 返回指令带停留时长

- **WHEN** 云端评估某详情页后决定 `navigation.back`
- **THEN** 该 `navigation.back` 指令携带 `dwellMs`，其值由云端依据已上报内容与风控状态算出

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
- **THEN** 长图文笔记 `navigation.back` 的 `dwellMs` 显著大于短笔记（时长与上报内容量正相关）

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

边缘执行 `navigation.back`（从详情页返回）前 SHALL 确保该详情页实际停留 ≥
`jitter(dwellMs ?? builtinFloor)`。无论指令是否携带 `dwellMs`，详情页 MUST NOT 出现快到不像
人能完成感知判断的瞬时返回（零延迟秒退）。

#### Scenario: 带时长的无价值详情页不秒退

- **WHEN** 云端判无价值并下发带 `dwellMs` 的 `navigation.back`
- **THEN** 边缘把返回推迟到实际停留 ≥ `jitter(dwellMs)` 之后才执行

#### Scenario: 缺时长仍不秒退

- **WHEN** `navigation.back` 未携带 `dwellMs`（旧云端 / 断连）
- **THEN** 边缘仍用内置 `builtinFloor` 保证详情页非零停留后才返回

### Requirement: 缺时间指令时的安全降级

边缘在未收到时间字段（旧云端 / 断连 / 自主动作）时 SHALL 回退到内置默认下限，
MUST NOT 退化为零延迟。`session.budget` 可选携带极薄的 `pacing` 默认块
（`tempo?` / `dwellFloorMs?`）供边缘自主动作与断连兜底使用；该默认块 MUST NOT 包含
read / pause / fatigue 系数（这些收口在云端）。

#### Scenario: 断连仍非零延迟

- **WHEN** 边缘在没有任何时间指令、且无 `session.budget.pacing` 的情况下运行
- **THEN** 各决策节点与详情页返回仍使用边缘内置默认下限，不出现零延迟秒退

#### Scenario: 会话默认仅含兜底参数

- **WHEN** 云端下发 `session.budget.pacing`
- **THEN** 该对象仅含 `tempo` / `dwellFloorMs` 等兜底字段，不含内容相关的 read / pause / fatigue 系数
