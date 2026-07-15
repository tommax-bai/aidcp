# Tasks — bounded-search-excursion

> landed aidcp-cloud `151462c`（rebase 后 sha，origin/master tip）；deployed dev 2026-07-15。

## 1. aidcp-cloud — 首页→搜索触发阈值 5→20（#1）
- [x] 1.1 `src/agents/feed-scroller.ts`：`SEARCH_THRESHOLD` 5→20，加 env 旋钮 `AIDCP_FEED_SEARCH_THRESHOLD`（默认 20，非法回落 20）
<!-- aidcp-cloud 151462c -->

## 2. aidcp-cloud — 修页型自指 bug（#2）
- [x] 2.1 `src/orchestrator/role-dispatcher.ts` `search.approved` 处理器：在**实际 `sendCommand({action:'search'})` 之后**把 `sessionContext.setSourcePageType('search')`（被 budget/限频闸拦下的分支绝不标）
- [x] 2.2 确认 feed 分支行为不变（`sourcePageType==='feed'` 时仍累计 feed 深度、评估传 `'feed'`）；搜索卡不再计入 feed 深度
<!-- aidcp-cloud 151462c -->

## 3. aidcp-cloud — 搜索行程有界退出：累计 20 张卡回首页（#3）
- [x] 3.1 `src/agents/session-context.ts`：新增 `_searchCardsBrowsed` + `_lastSearchNoteIds` + `searchBatchNewCount()` + getter/`addSearchCardsBrowsed()`/`resetSearchCardsBrowsed()`；`reset()` 清两者
- [x] 3.2 `src/agents/search-scroller.ts`：导出 `SEARCH_HOME_RETURN_AFTER`（env `AIDCP_SEARCH_HOME_RETURN_AFTER`，默认 20）
- [x] 3.3 `src/orchestrator/role-dispatcher.ts` `page.cards.arrived` 处理器：`sourcePageType==='search'` 分支累计 `searchBatchNewCount`；达阈值且 `canRefresh()`+`sessionActive` → `setSourcePageType('feed')` + reset 计数 + `sendCommand({action:'refresh', reason:'search_home_return'})` + return（跳过 evaluate）
- [x] 3.4 回首页时一并 `resetSearchCardsBrowsed()` / `resetScrolls()` / `resetFeedCardsBrowsed()`
<!-- aidcp-cloud 151462c -->

## 4. aidcp-cloud — 测试与回归
- [x] 4.1 单测：下发搜索后累计满阈值张搜索卡回首页（间接证明下发后 `sourcePageType==='search'`）；未下发时 feed 卡不触发回首页闸（`test/integration/bounded-search-excursion.test.ts`）
- [x] 4.2 单测：搜索页累计到阈值发出一次 `refresh(search_home_return)` 并复位为 `feed`；未达阈值不发
- [x] 4.3 单测：搜索页「一篇都点不开」的空转场景，累计卡数照样到阈值回首页（不卡死）
- [x] 4.4 `npm run test:acceptance`（52）+ `npm test`（2151）+ `npm run typecheck` 全过；`role-dispatcher.test 路径B` 改用 `SEARCH_THRESHOLD` 常量
<!-- aidcp-cloud 151462c -->

## 5. 部署与验收
- [x] 5.1 部署 dev（备份 `cloud.bak.20260715-173834.tar.gz` → rsync src/ → restart → healthcheck：active/8787/PG select 1/飞书长连接 全绿）
- [ ] 5.2 真机观测项登记 backlog（FB 账号搜索行程有界、到 20 卡回首页、feed 更耐心）→ 见 `docs/real-machine-acceptance-backlog.md`
<!-- 2026-07-15 deployed -->
