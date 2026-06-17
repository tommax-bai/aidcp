## ADDED Requirements

### Requirement: 返回列表页须按来源页型(sourcePageType)返回正确的列表

`back_to_feed` 返回 MUST 回到笔记**来源的列表页**：来自 explore feed 的会话回 explore，来自搜索结果的会话回**搜索结果**。云端 SHALL 把会话的 `sourcePageType` 经决策指令的 `targetPage` 透传到边缘；边缘据 `targetPage` 选择返回目标，MUST NOT 把搜索来源的会话一律拽回 explore。

#### Scenario: 搜索来源会话返回搜索结果
- **WHEN** 一条笔记经搜索结果打开、深读后云端决定 `back_to_feed`，且会话 `sourcePageType==='search'`
- **THEN** 云端下发的 `navigation.back` 携带 `targetPage='search'`，边缘返回到搜索结果列表（而非 explore feed）

#### Scenario: feed 来源会话返回 explore
- **WHEN** 会话 `sourcePageType==='feed'`（或缺省）时决定 `back_to_feed`
- **THEN** 边缘返回到 explore feed

### Requirement: 返回后须对 404/坏页健壮、健康校验通过再上报

边缘返回列表页时，若 `history.back()` 落到失效/过期/404 页面（如搜索来源笔记 `xsec_token` 过期导致"笔记不见了"），MUST 自动导航到已知良好的列表页兜底，并在**确认落在健康列表页（有可见卡片、非坏页）后**再上报 `page.cards`；MUST NOT 在坏页/0 卡时静默不上报而陷入边-云互等。

#### Scenario: history.back 落到过期笔记 404 → 兜底导航
- **WHEN** 返回时 `history.back()` 落到 token 过期的笔记详情页（404/坏页）
- **THEN** 边缘探测到非健康列表页（坏页标记或 0 卡）即 `Page.navigate` 到良好列表页（explore 或重新发起搜索），并轮询确认出现可见卡片后再上报 `page.cards`

#### Scenario: 坏页不静默
- **WHEN** 返回后页面无可见卡片且疑似坏页
- **THEN** 边缘不静默返回，而是导航兜底 + 健康校验；仍不可恢复时显式记录，避免循环停滞
