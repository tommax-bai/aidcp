## Context

命令评论（`/comment`）的搜索链在 `aidcp-edge` 与 `aidcp-cloud` 之间协作：

- 边端 `browse-session.ts` 的 `search.execute` 分支调用 `executeSearch()`（`search-handler.ts`）驱动搜索，然后**无条件** `waitForCards → waitForSearchResultNoteIds → reportVisibleCards()`。
- `executeSearch()` 目前返回 `void`：导航未确认时只打一行「未确认导航到搜索结果页」日志，静默 fall through。
- 云端 `edge-steps.ts` 的 `searchAndHarvest()` 用 `page.cards.arrived`（`() => true` 匹配任意到达）等 28s，拿到什么卡就当搜索结果。
- 采卡后 `comment-scheduler.ts` 的 `runSearchComment()` 由 picker 选中 `selected`，再复检 → `readNote`；复检找不到 → `read_failed`，`outcomeToReceipt()` 把原因硬编码为「（边端超时或离线）」。

现状约束（塑造方案）：
- 边端**已有**权威 URL 分类器：`SEARCH_LIST_RE`（`browse-session.ts:286`）、`isSearchListUrl()`（:1006）、`evalUrl()`（:998）——边端完全知道自己在哪一页。
- `reportVisibleCards()` 被**合法的自治 feed 上报共用**（:792/833/1084/1136/1143/1153/2128），诚实闸绝不能塞进它，只能落在 `search.execute` 分支内。
- `action.completed{action:'search', reason}` 是**已接线**的协议消息，云端动作并集已含 `search`（`role-dispatcher.ts:261`），且 Facebook 评论流（`facebook-edge-steps.ts:117-153`）**已经在竞速** `page.cards.arrived` vs `action.completed{action:'search'}`——即诚实回执有现成、已验证的消费范式，**零协议改动**即可复用。

## Goals / Non-Goals

**Goals:**
- 边端在**确认到达搜索结果页之前绝不上报卡片**；未到达时诚实回 `search ok:false{reason:not_on_search_page}`、不采不报、跳过错误页筛选重试。
- 云端**消费**该诚实回执，把「未导航到结果页」映射为**独立、真实**的结论，消除「（超时/边端离线）」误标与 maxTerms×28s 空转。
- 云端 `read_failed` 回执带**真实原因**。
- 全程**零协议 / 热点文件改动**。

**Non-Goals:**
- 不修 XHS AI 搜索提交/导航本身的 flakiness（真机后续）。
- 不给 `page.cards` 加页面来源协议字段（Option B，热点文件四处同步，YAGNI）。
- 不引入「按 noteId 直开候选」绕过复检（盲滚活锁风险，见 memory `note-open-miss-livelock`）。
- 不重构 `sendAndAwait` 返回类型。

## Decisions

### 决策 1：Option A（边端诚实闸）而非 Option B（协议页面来源字段）
- **选 A**：改 `search-handler.ts` + `browse-session.ts` 两个非热点文件即可闭环，无 4 处同步、无 `AC-PROTO-*` 暴露、可即时落地。根子是「别在源头撒谎」——边端已知自身 URL，本就该在确认结果页后再采。
- **弃 B（暂）**：给 `page.cards` 加 `pageType`/`sourcePage` 需改 `protocol.ts`（§2/§7 单写者热点、四处同步），其唯一独占价值（区分「搜索无结果」vs「从未导航」）已由决策 3 的 `action.completed` 消费零协议实现。仅当「feed 被误当详情页」类事故真复现，再单独起序列化协议 change。

### 决策 2：诚实闸以**实时 URL 判定为唯一依据**，不与 `executeSearch` 布尔取 AND
- `search.execute` 分支：`onSearch = this.isSearchListUrl(await this.evalUrl())`。
- **不用** `navigated && isSearchListUrl(url)` 的 AND 形式——`executeSearch` 的布尔可能滞后（导航稍慢但其实已到结果页），AND 会把这种「其实成功」误杀成不上报，制造**新的静默不上报回归**。以采卡时刻的实时 URL 为准最稳。
- `executeSearch` 仍改成返回 `Promise<boolean>`（confirmed nav），供其内部决定是否点提交兜底、并供日志/测试；但**不作为 gate 的判据**。
- `executeSearch` 抛错（现 catch 于 `browse-session.ts:1234`）也必须路由到失败分支，绝不 fall through 去报 feed。

### 决策 3：云端竞速消费诚实回执，独立真实归因（**必需，非可选**）
- 对抗评审结论：只做边端①②，边端诚实了，但云端仍会把「无卡到达」二次误标成「（超时/边端离线）」并空转 maxTerms×28s。故 `searchAndHarvest` **必须**同时竞速 `page.cards.arrived` 与 `action.completed{action:'search'}`（照抄 Facebook 流已验证范式），`ok:false` 立即返回空候选，且日志/回执用「搜索未导航到结果页（nav 未确认）」这一**独立结论**，不沿用「超时/边端离线」、不折叠进「无匹配笔记」。
- `read_failed` 回执（`outcomeToReceipt:1025`）带上被丢弃的 `r.reason`（对齐 `post_failed:1027`）。

### 决策 4：复检脆弱性不动（YAGNI）
- pick 后「再搜一次复找再开」链对 AI 搜索页脆弱，但一旦幻影候选被决策 1/3 挡掉，`read_failed('target unavailable during prepare')` 就不再由本事故成因触发。不引入 noteId 直开（活锁风险）。仅靠决策 3 把真实 reason 带出即可，复检链保持现状。

## Risks / Trade-offs

- [自治搜索并非「零影响」] `search.approved`（`role-dispatcher.ts:1549-1569`）与命令评论**共用** `search.execute` 分支，nav-fail 时也会发 `action.completed{search,ok:false}`——它不在 `noRecoverScroll` 集内，会触发一次恢复滚动。→ 缓解：该路径无活锁（搜索预算已在下发时消耗）、且这其实是**附带修复**（自治搜索原来也会把 feed 当结果）；补一条测试断言恢复滚动路径与无幻影。
- [空上报若无回执本身即「静默假成功」] 未到结果页时「不报卡」只有**配上显式 `action.completed{ok:false,reason}`** 才诚实；缺回执的空上报本身违红线。→ 缓解：①②③捆绑落地，回执必发、云端必消费。
- [热点文件并行冲突] `search.execute` 分支属 `comment-search-command` 血缘，若并行 session 在改需按单写者串行。→ 缓解：land 前 fetch+rebase，标记该分支单写。
- [根源未修] 本 change 后 nav 仍可能频繁失败，评论产出偏少——但会**正确报失败**而非幻影。→ 缓解：真机核实提交机制，登记 backlog 后续修。

## Migration Plan

1. 边端改 `search-handler.ts` + `browse-session.ts`，`cd ../aidcp-edge && npm run typecheck && npm test`（含新回归）。
2. 云端改 `edge-steps.ts` + `comment-scheduler.ts`，`cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck`。
3. 无协议改动，`AC-PROTO-*` 应原样通过；核对 `AC-*` 全绿。
4. 部署：edge 本地跑连 dev；cloud 走安全序列部署 dev（备份→rsync→restart→healthcheck）。
5. 回滚：两仓独立改动，各自 revert 即可；无 schema/协议迁移。

## Open Questions

- XHS AI 搜索真实提交机制与结果页 URL 形态（`search_result_ai` vs 裸 `/search`）未经真机确认——`SEARCH_LIST_RE` 是否需按真 URL 收紧待真机核。此为真机验收项，不阻塞本 change 的诚实性修复落地。
