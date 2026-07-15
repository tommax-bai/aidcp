## ADDED Requirements

### Requirement: 云端开笔记步 MUST 竞速消费开笔记失败信号、不干等满超时、失败如实归因

云端按需评论的「开笔记 / 读正文」步在等待目标笔记详情时，MUST **同时**监听「成功」与「失败」两类信号并竞速取先到者，MUST NOT 只监听 `note.detail.arrived` 而对失败信号充耳不闻、干等满单步超时：

- **成功**：`note.detail.arrived` 且 noteId 与目标一致 → 照常读正文 / 采现场评论。
- **失败（边缘诚实回执）**：`action.completed{action:'open_note', ok:false}`（弹层不弹 / 抽取失败 / 墙钟预算耗尽 / 无 noteId 找不到卡等）→ MUST 立即以失败返回，携带边缘上报的真实 `reason`。
- **失败（目标卡已不在当前页）**：边缘重报的 `page.cards.arrived`（带 noteId 的目标卡被虚拟列表回收、有界滚回仍找不到时，边缘重报当前卡片）→ MUST 立即以失败返回（reason 表意为「目标不在当前页」）。

任一失败信号先到即快速失败，MUST NOT 继续干等满单步超时（消除每次开笔记失败白等约一个单步预算）。三类信号都未到（真超时 / 无送达）时才按超时失败，且措辞 MUST 中性（如「无回执（超时/结果未就绪）」），MUST NOT 把**边缘在线的诚实失败**冒充「（超时/边端离线）」（假归因红线，与搜索导航失败归因同口径）。

此要求为既有「云端 MUST 消费搜索导航失败回执并真实归因失败原因」的开笔记侧对称件；两步都 MUST 竞速消费诚实失败、快速失败、如实归因。

#### Scenario: 边缘诚实回开笔记失败 → 立即失败带真实原因
- **WHEN** 云端开笔记步在等详情时收到 `action.completed{action:'open_note', ok:false, reason}`
- **THEN** MUST 立即以失败返回（不再等详情），日志/回执归因 MUST 呈现真实 `reason`，MUST NOT 说「（超时/边端离线）」

#### Scenario: 目标卡已被回收、边缘重报卡片 → 立即失败
- **WHEN** 云端开笔记步在等详情时收到边缘重报的 `page.cards.arrived`（而非目标 `note.detail`）
- **THEN** MUST 立即以失败返回（reason 表意「目标不在当前页」），MUST NOT 干等满单步超时

#### Scenario: 三路皆未到（真超时）→ 中性措辞
- **WHEN** 单步预算内既无匹配 `note.detail`、也无 `open_note` 失败回执、也无重报 `page.cards`
- **THEN** MUST 按超时失败，措辞中性（不断言「边端离线」）
