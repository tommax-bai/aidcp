## ADDED Requirements

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

- **WHEN** 熟悉折扣对 `thinkMs` 生效的同时，云端为刚读过的笔记下发 `navigation.back` 的 `dwellMs`
- **THEN** 该 `dwellMs`（read 量级停留）不被折扣，详情页仍不秒退

#### Scenario: 超出近期窗口不再享折扣

- **WHEN** 某 `noteId` 的评估记录已被挤出有界近期已评估集合（不在最近约 30 个内）
- **THEN** 再次对其下发动作时 `thinkMs` 按全量处理（不折扣）

### Requirement: 返回熟悉 feed 的手势与落地更快但不秒退

边缘执行 `navigation.back` 且 `reason==='back_to_feed'`（必然返回到打开笔记前的同一批、刚刚看过的 feed）时，返回手势停顿与 `history.back` 之后的固定落地等待 SHALL 按折扣（约**常规的 1/3**）缩短，且 MUST 保留**非零下限**（仍带抖动、不出现零延迟瞬时返回）。该折扣 MUST NOT 缩减离开笔记前的停留下限（`ensureDetailDwell` / 笔记 `dwellMs` 不变），也 MUST NOT 削弱返回后的坏页 / 404 健康校验兜底。

#### Scenario: 返回熟悉 feed 手势更快

- **WHEN** 边缘执行 `navigation.back{reason:'back_to_feed'}`
- **THEN** 返回手势停顿与返回后固定落地等待约降至常规的 1/3（带非零下限），更快进入续刷

#### Scenario: 返回手势仍非零、不秒退

- **WHEN** 任意 `back_to_feed` 返回
- **THEN** 返回前仍存在非零的手势停顿，且离开笔记前的停留下限不被该折扣影响

#### Scenario: 非 back_to_feed 返回不受影响

- **WHEN** 边缘执行的返回不是 `back_to_feed`（如回到搜索结果）
- **THEN** 不应用该折扣，返回时序按现状
