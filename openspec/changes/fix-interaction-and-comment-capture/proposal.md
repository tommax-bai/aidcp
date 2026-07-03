## Why

两个不影响「发评论」本身、但降低互动质量的偶发缺陷，经代码复核定位（限流类节奏闸为**设计如此**、本 change 不动）：

**毛病 A — 给笔记点赞/收藏偶尔没点着。** 排除云端故意的节奏限流（动作冷却 like 2min / collect 5min、通知巡视软暂停）后，仍有两处真缺陷：
1. 执行端点赞/收藏定位互动栏用的选择器 `.interactions.engage-bar` **无 `.engage-bar` 兜底**（同文件发评论、读点赞数都有兜底），且**点击前不等互动栏渲染**（`note.open` 路径有等待、点赞这条没有）——AI 总结流式重排 / 卡片被回收的一瞬间就报 `btn_no-bar`。真机已观测到此失败（`comment-search-command/tasks.md:73`）。
2. 一旦执行端如实回报失败，云端**不重试**、直接发一条兜底滚动翻篇（会把详情页滚走），这一篇的点赞/收藏就永久漏掉。
3. （红线）点赞/收藏会话预算在**下发时**乐观扣减、失败不回滚，与 follow/comment「按真成功回执扣」的口径不一致（`budget 不漂移` 未满足）。

**毛病 B — 笔记里的现场评论没采到。** 现场评论唯一采集口是「滚评论区 + 抽取候选」：
1. 执行端找不到可滚容器（`no_target`）或滚不动（`no_scroll`，短评论区不产生溢出）时**在抽取之前直接返回**，一条不采——真机已观测（`tasks.md:73`）。
2. 就算滚到了，也只抽**最后一屏、最多 12 条、无渲染门**，滚过去的评论丢失。
3. 云端发评论采评论时把 `no_target` / `no_scroll` / 空 / 异常**一把抹平成「无评论」**（`edge-steps.ts` 的 `candidates ?? []`），掩盖抽取失败——红线「空数组当没评论」真正咬人处。

> 注：**限流/节奏闸（冷却、软暂停、点赞比例闸）为反检测设计，本 change 明确不动**。「打开笔记就沉淀全部现场评论做语料」是当前不存在的功能（评论仅在真给某条评论点赞成功时入库），也不在本 change 范围——本 change 只修「该采到却没采到 / 该点上却没点上」的执行与消费缺陷。

## What Changes

- **【edge · 点赞/收藏定位加固】** `executeLikeOrCollect` 定位互动栏前复用 `waitForEngageBar` 有界等待；定位与后置校验选择器加 `.engage-bar` 兜底（对齐同文件 `executeComment` 与 `note-extractor`）。找不到仍诚实 `no-bar`，不假成功。
- **【cloud · 点赞/收藏失败可重试】** 执行端回报可重试失败（`state_unchanged` / `btn_no-bar` / `btn_no-btn`）时，云端**原地有界重试一次**（从在途去重键回捞 noteId 重发），而非发兜底滚动把详情页滚走；`blocked_by_captcha` / `already_*` / `no_like_btn` 不重试。
- **【cloud · 预算按成功扣】** 点赞/收藏会话预算改在 `action.completed{ok:true}` 时扣减（对齐 follow/comment），下发时不再乐观扣、失败不再白烧预算。
- **【edge · 现场评论跨屏累计】** `scrollNoteComments` 在滚动过程中逐屏抽取候选、按锚点去重累计（不再只取终态一屏）；抽取前留一个短渲染门。
- **【edge · 滚不动也抓可见评论】** `no_target` / `no_scroll` 分支在返回前仍抽取当前可见评论并随回执带回（短评论区不再一条不采）；ok / reason 语义保持诚实。
- **【cloud · 失败与真无评论分开】** 发评论采评论时区分「采集失败（`ok:false`）」与「真无评论（`ok:true` 且空）」，不再静默抹平；采集屏数从 1 提到 2 以多覆盖一屏。

> 非 BREAKING：协议消息类型不变（`ActionCompletedPayload.candidates` 字段既有）；仅加固执行端定位/抽取与云端消费/重试/记账。限流行为完全不变。

## Capabilities

### New Capabilities
- `interaction-comment-capture-fidelity`: 点赞/收藏落地可靠性（互动栏有界等待 + 选择器兜底 + 失败有界重试 + 预算按真成功扣）与现场评论采集保真（跨屏累计去重 + 滚不动仍抓可见 + 云端消费不抹平失败），全程守「不静默假成功 / 不把采集失败当无数据 / 预算不漂移」红线。

## Impact

- **edge**：`aidcp-edge/src/browse/browse-session.ts`（`executeLikeOrCollect`、`scrollNoteComments`、`harvestCommentCandidates`）。
- **cloud**：`aidcp-cloud/src/orchestrator/role-dispatcher.ts`（`interaction.completed` / `action.completed` 两处处理，预算与重试）、`aidcp-cloud/src/comment-agent/edge-steps.ts`（采评论消费）。
- **协议**：无新增消息类型（复用既有 `action.completed{candidates}`），无四处同步负担。
- **真机遗留项**：评论行选择器 `[id^="comment-"]`、可滚容器种子选择器、互动栏是否存在「只带 `.engage-bar` 不带 `.interactions`」的布局变体——登记进真机验收 backlog，代码内先做防御性兜底。
