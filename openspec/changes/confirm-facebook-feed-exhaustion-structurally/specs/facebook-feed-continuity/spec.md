## MODIFIED Requirements

### Requirement: feed「到底」判据是懒加载感知的、绝不在还有内容时误判换批

边缘在一条 feed 滚动命令内 SHALL 有界续滚寻找**未见过的新卡**。对于命令列表上下文从首页开始、且本命令已经在同一首页文档观察到真实 canonical 帖子的 canonical 首页，判定「feed 到底」（回执 `feed_exhausted`，云端据此授权 Reels）SHALL 使用固定五样本结构确认：进入确认的探针是 `t=0`，后续样本位于 `t=5s / 7.5s / 10s / 12.5s`。`scrollHeight − scrollY − scrollViewportHeight` 不大于实际滚动容器的一个视口即属于**近底部**，足以进入并维持确认，不要求滚动条精确贴住数学底部；嵌套 feed scroller MUST 使用其 `clientHeight`，不得误用浏览器窗口高度。

五个样本 MUST 始终处于同一 URL、同一非零 `document_time_origin_ms` 文档 epoch、同一 document generation 和 canonical 首页面，`document_age_ms` 相对紧邻前一样本不得倒退，均无 loading、均保持近底部，相对初始样本的 `scrollHeight` 增长不得超过既有 100px 重排噪声阈值（`>100px` 即失效），canonical 卡身份有序向量不得出现变化。只有第五个样本仍满足全部结构证据时才 SHALL 返回 `feed_exhausted`；前四个样本 MUST NOT 提前成功。可见本地化 `explicit_end` 标记 MAY 继续用于有界诊断、判稳键和独立首页空态证据，但其缺失或抖动 MUST NOT 阻止一个此前非空且五样本结构稳定的 canonical 首页返回 `feed_exhausted`。

只要页面增长超过 100px、loading、canonical 卡身份有序向量变化、离开实际滚动容器的一屏近底范围、发生 URL / document epoch / generation / 列表面变化，`document_age_ms` 相对紧邻样本倒退，命令列表上下文并非从首页开始，或本命令从未在同一首页 URL 与 document epoch 上观察到真实 canonical 帖子，边缘 MUST NOT 从该 marker-free 确认返回 `feed_exhausted`。搜索与小组列表面的近底结构稳定，以及搜索/小组命令中途跳到首页，MUST NOT 通过本条 marker-free 规则授权首页 Reels fallback；它们保留各自既有续滚与恢复语义。

续滚 SHALL 有硬上限（`FEED_SCROLL_MAX_ROUNDS`，默认 8，配合单命令兜底超时约束在预算内）。尚未形成完整五样本结构终态的轮次仍在上限内继续；轮次耗尽本身不是终止证据。全程未扫到任何卡时 SHALL 按 loading/页面事实回 `feed_still_loading`、`no_target` 或既有零卡观察；扫到过卡但结构确认失效或未完成时 SHALL 回 `feed_continuation_unconfirmed`。Cloud 收到该非终态原因后 SHALL 通过现有配额、暂停、评论支线、节奏和会话闸再下发普通续滚，MUST NOT 据此授权 Reels。红线：只上报**真抽的未见过新卡**，MUST NOT 把回收重现的旧卡当新内容重复上报。

此判据保留**浏览深度阈值**（云端按已浏览不重复卡数换批，默认 60）作为换批主路，`feed_exhausted → Reels` 只在此前非空的 canonical 首页完成完整结构确认后兜底。

#### Scenario: 懒加载还在长内容或离开近底部时继续 Feed

- **WHEN** 本轮没有新 canonical 卡，但任一样本出现 loading、`scrollHeight` 相对初始样本增长 `>100px` 或剩余距离超过一个视口
- **THEN** 边缘 MUST NOT 回 `feed_exhausted`，并继续有界寻找下沉的新卡或返回 continuation-unconfirmed

#### Scenario: 五次近底结构稳定且没有结束标记也确认耗尽

- **WHEN** 一条列表上下文从首页开始的命令此前在同一首页 URL 与 document epoch 上观察到真实 canonical 帖子，且该 canonical 首页在 `t=0 / 5 / 7.5 / 10 / 12.5s` 始终同 URL、同非零 document epoch、同 generation、相邻样本 `document_age_ms` 不倒退、非 loading、处于实际滚动容器的一屏近底范围、增高不超过 100px 且 canonical 卡身份有序向量不变
- **AND WHEN** `explicit_end` 在一个或全部样本中缺失
- **THEN** 边缘只在第五个样本后回 `feed_exhausted`
- **AND THEN** Cloud MAY 经既有授权闸切换 Reels

#### Scenario: 页面跳转或刷新使确认失效

- **WHEN** 五样本窗口内 URL、非零 document time origin、document generation 或列表面发生变化，或 `document_age_ms` 相对紧邻样本倒退
- **THEN** 边缘立即使本轮确认失效，MUST NOT 从旧页面证据回 `feed_exhausted`

#### Scenario: 搜索或小组近底稳定不触发首页 marker-free fallback

- **WHEN** 搜索结果页或小组列表面在五个样本中保持近底、无 loading、无显著增高且无新 canonical 帖子，但没有其既有终止证据
- **THEN** 边缘 MUST NOT 仅凭本条首页结构规则授权 Reels，并保留非首页列表面的既有续滚或恢复结果

#### Scenario: 非首页命令中途跳到首页不继承 marker-free 授权

- **WHEN** 一条从搜索或小组列表上下文开始的滚动命令在进入 `t=0` 前跳到首页，并在首页形成五次 marker-free 结构稳定样本
- **THEN** 边缘 MUST NOT 从该命令返回 marker-free `feed_exhausted`

#### Scenario: 全程未扫到任何真实卡时走零卡证据阶梯

- **WHEN** 有界续滚和五样本候选均未观察到任何真实 canonical 帖子
- **THEN** 边缘按既有 loading、明确空态、present-unreportable 或 `no_target` 证据分类，MUST NOT 把页面静止误报为 `feed_exhausted`
