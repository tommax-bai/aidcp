## MODIFIED Requirements

### Requirement: feed「到底」判据是懒加载感知的、绝不在还有内容时误判换批

边缘在一条 feed 滚动命令内 SHALL 有界续滚寻找**未见过的新卡**；判定「feed 到底」（回执 `feed_exhausted`，云端据此换批）SHALL 是懒加载感知的，并且只能走两类证据之一：① canonical 首页近底部可见的本地化“没有更多内容”标记，在同一页面世代内连续稳定出现且没有新卡；或 ② 本轮 0 新卡、内容总高 `scrollHeight` 在完整确认窗口内**不再增长**、已**接近底部**（`scrollHeight − scrollY − innerHeight` 小于约一屏余量），并且该结构状态**连续确认 ≥2 轮**。只要页面仍在增长、loading、出现新卡、离开 canonical 首页或尚未接近底部，边缘 MUST 重置到底候选并继续下滚，MUST NOT 判到底。

续滚 SHALL 有硬上限（`FEED_SCROLL_MAX_ROUNDS`，默认 8，配合单命令兜底超时约束在预算内）。轮次耗尽不是终止证据：全程未扫到任何卡时 SHALL 按 loading/页面事实回 `feed_still_loading` 或 `no_target`；扫到过卡但一直无新卡且未形成到底证据时 SHALL 回 `feed_continuation_unconfirmed`。Cloud 收到该非终态原因后 SHALL 通过现有配额、暂停、评论支线、节奏和会话闸再下发普通续滚，MUST NOT 据此授权 Reels。红线：只上报**真抽的未见过新卡**，MUST NOT 把回收重现的旧卡当新内容重复上报。

此判据使**浏览深度阈值**（云端按已浏览不重复卡数换批，默认 60）成为换批主路，`feed_exhausted → Reels` 仅在真实终止证据成立时兜底，消除提前换列表和后续空闲看门狗停顿。

#### Scenario: 懒加载还在长内容 / 未到底 → 续滚不判到底
- **WHEN** 本轮 0 新卡，但确认窗口内 `scrollHeight` 增长、仍有 loading 或尚未接近底部
- **THEN** 边缘继续下滚寻找下沉的新卡，MUST NOT 回 `feed_exhausted`；后续轮次出现新卡即上报

#### Scenario: 明确终止标记稳定出现 → 诚实 feed_exhausted
- **WHEN** canonical 首页近底部的可见本地化终止标记连续稳定出现且没有新卡
- **THEN** 边缘诚实回 `feed_exhausted`，但 MUST NOT 把该标记扩张成首页从未有卡的 `explicitEmpty`

#### Scenario: 高度稳定且接近底部、连续无新卡 → 诚实 feed_exhausted
- **WHEN** 连续 ≥2 轮「完整确认窗口内 `scrollHeight` 不再增长 + 接近底部 + 0 新卡」
- **THEN** 边缘诚实回 `feed_exhausted`（云端据此换批），MUST NOT 上报陈旧卡

#### Scenario: 轮次耗尽但未确认到底 → 继续而非换批
- **WHEN** 有界续滚曾扫到卡但轮次耗尽时仍无稳定终止标记或结构性到底证据
- **THEN** 边缘回 `feed_continuation_unconfirmed`，Cloud 经现有浏览闸下发普通续滚，且 MUST NOT 授权 Reels

#### Scenario: 全程未扫到任何卡 → no_target 而非 feed_exhausted
- **WHEN** 有界续滚全程 settle 都为空（loading / 无 feed 容器）
- **THEN** 边缘回可重试的 `feed_still_loading` 或 `no_target`，MUST NOT 误报 `feed_exhausted`
