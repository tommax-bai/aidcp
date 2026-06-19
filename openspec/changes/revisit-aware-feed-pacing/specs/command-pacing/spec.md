## MODIFIED Requirements

### Requirement: 决策指令携带可选时间指令

云端 → 边缘的决策指令 SHALL 支持可选的时间字段：`navigation.back` / `note.close` 携带
`dwellMs`（离开当前页前应达到的总停留时间），`interaction.like` / `interaction.collect` /
`interaction.follow` / `note.open` 携带 `thinkMs`（执行动作前的犹豫 / 感知时间），**feed 滚动
`page.scroll`（`reason: feed_scroll`）携带可选 `thinkMs`（滚动前的扫读 / 感知时间）**。时间字段
全部可选，缺失视为合法，边缘按内置默认兜底。云端 MUST NOT 在 `session.budget` 下发整套时间
系数要求边缘自行套公式计算内容相关时长。

携带 `thinkMs` 的 `page.scroll` 指令在云端 → 边缘的动作↔消息映射中 MUST 完整透传 `thinkMs`
（不得在 bridge 处静默丢弃 `params`）。

#### Scenario: 返回指令带停留时长

- **WHEN** 云端评估某详情页后决定 `navigation.back`
- **THEN** 该 `navigation.back` 指令携带 `dwellMs`，其值由云端依据已上报内容与风控状态算出

#### Scenario: feed 滚动指令的 thinkMs 透传到边缘

- **WHEN** 云端给 `feed.scrolled` 产出的 `scroll` 指令挂上 `thinkMs`
- **THEN** 该 `thinkMs` 经 bridge 完整映射进 `page.scroll` 消息送达边缘，MUST NOT 在 bridge 处被丢弃

#### Scenario: 旧边缘忽略未知时间字段

- **WHEN** 边缘版本早于本 change、收到带 `dwellMs` / `thinkMs` 的指令
- **THEN** 边缘忽略该字段、按内置默认兜底运行，行为不劣化（向后兼容）

## ADDED Requirements

### Requirement: 重访 feed 的节奏感知（已看过的卡片更快扫过）

云端 SHALL 在会话内维护**卡片级 seen 集合**（区别于「打开过的笔记」集合），每次 `page.cards`
上报时标记其可见卡片。产出 feed 滚动指令时，云端 SHALL 依据「即将划走的可见卡片中已看过的比例」
把 `page.scroll` 的 `thinkMs` 中心值**单调调小**（已看过比例越高、思考时间越短），且 MUST 保留
一个非零下限（floor）；当可见卡片**全为新出现**时，按全量 `thinkMs`。边缘对该 `thinkMs` 仅叠
lognormal 抖动消费（不自行计算内容相关中心值）。该机制 MUST NOT 影响详情页的 `dwellMs`（刚读过
的笔记停留不被缩减）。

#### Scenario: 返回到已看过的 feed 页扫得更快

- **WHEN** 边缘从详情页返回 feed，可见卡片与打开前为同一批（已看过比例高）
- **THEN** 云端给后续 feed `scroll` 指令下发**显著更小**的 `thinkMs` 中心值，边缘据此更快滚过

#### Scenario: 全新 feed 页保持全量节奏

- **WHEN** 当前可见卡片均为本会话首次出现（已看过比例为 0）
- **THEN** feed `scroll` 指令的 `thinkMs` 中心值为全量值，不被缩减

#### Scenario: 重访提速不波及刚读笔记停留

- **WHEN** 重访感知对 feed 滚动生效的同时，云端为刚读过的笔记下发 `navigation.back` 的 `dwellMs`
- **THEN** 该 `dwellMs`（read 量级停留）不因重访感知而被缩减，详情页仍不秒退

### Requirement: 已满足停留的返回手势不重复全量犹豫

边缘执行 `back_to_feed` 返回时 SHALL 仅使用一段**轻量、非零**的手势停顿（带抖动）即 `history.back`：若该详情页停留下限已由 `dwellMs` 兜底（`ensureDetailDwell`）治理达标，则返回手势本身 MUST NOT 再叠加一段**全量**的动作级犹豫（避免与停留治理重复计费），既不秒退也不冗余拖慢。

#### Scenario: 读够后快速返回

- **WHEN** 详情页停留已达 `jitter(dwellMs)`、边缘随后执行 `back_to_feed`
- **THEN** 返回手势仅用轻量手势停顿（非零、带抖动）即 `history.back`，不再叠加全量动作级犹豫

#### Scenario: 返回手势仍非零

- **WHEN** 边缘执行任意 `back_to_feed` 返回
- **THEN** 返回前仍存在一段非零的手势停顿（不出现零延迟的瞬时返回）
