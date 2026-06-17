## ADDED Requirements

### Requirement: 多图浏览判定与执行

系统 SHALL 在详情页质量粗筛通过（`quality.pass`）后，由 `DeepReader` 角色基于当前笔记内容（图片数量、正文长度）与人设决策是否浏览多图及浏览张数；决策为"看"时 MUST 下发 `browse_images` 指令并在边缘执行后凭 `action.completed` 推进，决策为"不看"时 MUST 直接推进至评论阶段。`DeepReader` MUST NOT 再硬编码 `imagesBrowsed=0` 或在不发任何指令的情况下直通。

#### Scenario: 多图笔记决定浏览图片
- **WHEN** `quality.pass` 到达且当前笔记含多张图片、`DeepReader` 决策为浏览
- **THEN** 系统下发 `browse_images` 指令（含 `noteId`、张数、`dwellMs`），边缘执行翻图后回 `action.completed`，随后系统 emit `reading.images_done` 进入评论阶段

#### Scenario: 决定不看图直接推进
- **WHEN** `DeepReader` 决策本次不浏览图片
- **THEN** 系统不下发 `browse_images`，直接 emit `reading.images_done`

#### Scenario: 浏览图片动作失败仍推进
- **WHEN** `browse_images` 执行失败或回报 `no_target`
- **THEN** 系统按动作失败兜底推进（不卡死），仍 emit `reading.images_done`

### Requirement: 评论浏览判定与执行

系统 SHALL 由独立角色 `comment_reviewer`（须实例化并注册到 `RoleDispatcher`，不得仅作为类型联合中的名字）在多图阶段完成（`reading.images_done`）后，用 LLM 判定本次是否浏览评论及浏览程度；决策为"看"时 MUST 下发 `scroll_comments` 指令并凭 `action.completed` 推进，决策为"不看"时 MUST 直接推进。两种情形最终 MUST emit `reading.done` 作为进入互动阶段的唯一出口。本能力只做浏览评论，MUST NOT 发表评论。

#### Scenario: 决定浏览评论区
- **WHEN** `reading.images_done` 到达且 `comment_reviewer` 判定值得看评论
- **THEN** 系统下发 `scroll_comments` 指令（含 `noteId`、`dwellMs`），边缘滚动评论区后回 `action.completed`，随后系统 emit `reading.done`

#### Scenario: 决定不看评论直接推进
- **WHEN** `comment_reviewer` 判定本次不看评论
- **THEN** 系统不下发 `scroll_comments`，直接 emit `reading.done`

#### Scenario: 无评论或滚动失败仍推进
- **WHEN** 评论区为空或 `scroll_comments` 回报失败/`no_target`
- **THEN** 系统按兜底推进，仍 emit `reading.done`

### Requirement: 深读取舍的拟人化多样性

系统 SHALL 使"是否看图""是否看评论"的决策带概率多样性，体现真人取舍（有时看图不看文、有时翻评论、有时直接过）；下发 `browse_images`/`scroll_comments` 时 MUST 携带按内容计算的 `dwellMs` 中心值，边缘叠加抖动后停留。本能力 MUST 复用既有 `dwellMs`/`thinkMs` 节奏字段，不新增节奏协议字段。

#### Scenario: 同类笔记的浏览取舍不恒定
- **WHEN** 连续多篇相似的多图笔记进入深读
- **THEN** 系统对"看图/看评论"的选择呈现概率多样性，而非每篇都执行相同子动作

### Requirement: 边缘深读动作如实回报

边缘执行 `browse_images`/`scroll_comments` 时 SHALL 使用与真实小红书详情页一致的选择器，`action.completed` MUST 如实反映执行结果（翻图张数/滚动屏数/无评论/未命中目标）。边缘 MUST NOT 在未命中目标时仍回报 `ok=true`（消除 `count||1` 之类恒成功兜底）。

#### Scenario: 未命中图片轮播控件
- **WHEN** 边缘在详情页找不到图片轮播/翻页元素
- **THEN** `action.completed` 回报 `ok=false` 且 `reason` 标明 `no_target`，而非假报成功

#### Scenario: 真实翻图成功
- **WHEN** 边缘成功翻看 N 张图片
- **THEN** `action.completed` 回报 `ok=true` 且反映实际浏览张数
