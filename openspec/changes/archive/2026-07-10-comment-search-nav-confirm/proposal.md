## Why

按需评论（`/comment`）的搜索采卡在**导航未真正到达搜索结果页时也照采当前页**：小红书 AI 搜索框回车常只换行不提交、兜底点提交按钮偶发失败，此时页面仍停在首页 feed，边端却把 feed 卡当搜索结果上报。云端据此选中一张与搜索词毫不相关的 feed 笔记作「幻影候选」，随后稳定性复检自然找不到它 → `read_failed`，对运营弹出误导性的「已选中，但开笔记/读正文失败（边端超时或离线）」——边端其实全程在线。这直接违反「MUST NOT 静默假成功 / 假归因」红线。

实证事故（2026-07-10，dev，账号 Tmax）：`/comment` 搜索词「Claude Code实测」首次搜索「未确认导航到搜索结果页」，边端把当时 feed 的 8 张卡上报，云端选中其中的《GPT5.6上线，智能大溢出时代》（@Gino_Pro，与搜索词无关），复检失败并把原因误写成「边端超时或离线」。

## What Changes

- **边端搜索采卡前 MUST 确认已到达搜索结果页**（以实时 URL 判定为准）。未确认到达时：**不上报任何卡片**、发一条诚实的 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}`、并跳过对错误页的原生筛选重试（省无谓等待）。绝不把 feed 当搜索结果上报。
- **云端命令评论搜索步 MUST 消费这条诚实回执**：等结果时同时竞速 `page.cards.arrived` 与 `action.completed{action:'search'}`；收到 `ok:false` 立即以**独立、真实的结论**（「搜索未导航到结果页」）快速失败，MUST NOT 沿用「（超时/边端离线）」措辞、MUST NOT 折叠进「无匹配笔记」，并**消除 maxTerms×28s 空转**。
- **云端 `read_failed` 回执 MUST 带真实原因**（对齐 `post_failed` 的写法），不再一律硬编码「（边端超时或离线）」。
- **作用域**：改动落在边端 `search.execute` 分支与两个云端评论步文件；**不改 `protocol.ts` 等协议热点文件**（`action.completed`/`search` 通道已接线）。自治搜索（与命令评论共用同一 `search.execute` 分支）一并获得同一诚实闸，属附带修复。
- **非目标（明确不做）**：不给 `page.cards` 加页面来源协议字段（YAGNI + 热点文件四处同步，另行序列化 change 才做）；不引入「按 noteId 直开候选」绕过路径（有盲滚活锁风险）；不重构 `sendAndAwait` 返回类型（竞速消费已达成诚实归因）。修 XHS AI 搜索提交/导航本身的 flakiness 属另一条真机后续。

## Capabilities

### New Capabilities
<!-- 无新增能力：本 change 只强化既有命令评论能力的搜索采卡诚实性契约。 -->

### Modified Capabilities
- `comment-search-command`: 新增「搜索采卡前须确认已到达搜索结果页、未到诚实回失败且不得把 feed 当结果」的要求，并新增「云端诚实消费搜索导航失败回执、失败归因真实（区分未导航 / 无结果 / 真离线）」的要求；强化既有「诚实贯穿」不变量。

## Impact

- **aidcp-edge**：`src/browse/search-handler.ts`（`executeSearch` 返回确认导航布尔）、`src/browse/browse-session.ts`（`search.execute` 分支的实时 URL 诚实闸 + 失败回执）。
- **aidcp-cloud**：`src/comment-agent/edge-steps.ts`（`searchAndHarvest` 竞速消费 `action.completed{search}`、真实归因）、`src/comment-agent/comment-scheduler.ts`（`outcomeToReceipt` 的 `read_failed` 带真实 reason；「未导航」独立回执）。
- **无协议 / 热点文件改动**，无 4 处同步，`AC-PROTO-*` 不受影响。
- **真机遗留**：本 change 让失败变诚实但不修 XHS AI 搜索提交本身；需在 tom 分组 headful 真机核实 AI 搜索是否真跳 `search_result_ai`、真实提交机制与结果页 URL 形态，登记 `docs/real-machine-acceptance-backlog.md`。
