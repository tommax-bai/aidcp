## 1. aidcp-edge — 搜索采卡诚实闸（根因）

- [x] 1.1 `src/browse/search-handler.ts`：`executeSearch` 返回类型 `Promise<void>` → `Promise<boolean>`（`true` = 已确认到达搜索结果页）；导航确认分支返回 `true`，「未确认导航」分支保留诚实日志、返回 `false`；同步更新 `@returns` 注释 <!-- aidcp-edge 0274cf2 -->
- [x] 1.2 `src/browse/browse-session.ts` `case 'search.execute'`：以**实时 URL** 判定 `onSearch = this.isSearchListUrl(await this.evalUrl())`；**不**与 `executeSearch` 布尔取 AND。`!onSearch` 时发 `action.completed{action:'search', ok:false, reason:'not_on_search_page'}`、不采不报、跳过 `applySearchFilters`/`waitForCards`/`waitForSearchResultNoteIds`/`reportVisibleCards` <!-- aidcp-edge 0274cf2 附带放宽 SEARCH_LIST_RE 覆盖 search_result_ai（原正则漏 AI 搜索页、否则诚实闸会漏报真结果；顺带修 ensureExplore 把 AI 搜索页误导航走） -->
- [x] 1.3 `browse-session.ts`：`executeSearch` 抛错也路由到失败分支，绝不 fall through 去上报当前页卡片 <!-- aidcp-edge 0274cf2 catch 内 onSearch=false -->
- [ ] 1.4 （可选，纵深防御，**本次未做**）`search-handler.ts:waitForSearchNavigation`：收紧 `href.includes('search')` → `search_result`。权威闸是 browse-session 的实时 URL 复检、`executeSearch` 布尔不参与 gate，故此项低价值、跳过 <!-- 对抗评审判为 deferrable；未做 -->
- [x] 1.5 边端测试：① `executeSearch` 在 `search_result_ai` 返 `true`、恒 `/explore` 返 `false`；② **核心回归** search.execute 恒 `/explore` + feed 卡 → 无搜索 `page.cards` 上报 + `action.completed{search,ok:false,not_on_search_page}`；③ happy-path（现有 654/677 断言）；④ 现有用例全绿证自治 feed 上报未破 <!-- aidcp-edge 0274cf2 test 863 pass -->
- [x] 1.6 `cd ../aidcp-edge && npm run typecheck && npm test` <!-- aidcp-edge 0274cf2 typecheck 0 + test 863/863 pass -->

## 2. aidcp-cloud — 诚实消费 + 真实归因

- [x] 2.1 `src/comment-agent/edge-steps.ts` `searchAndHarvest`：加 `sendAndRace` 竞速 `page.cards.arrived` 与 `action.completed{action:'search'}`（照抄 `facebook-edge-steps.ts:117-153`）；收 `ok:false` 立即返回空候选（消除 maxTerms×28s 空转） <!-- aidcp-cloud 8a35cbe -->
- [x] 2.2 `edge-steps.ts`：「未导航到结果页」映射为独立真实日志（「搜索未导航到结果页（nav 未确认）」），不沿用「（超时/边端离线）」、不折叠进「无匹配笔记」 <!-- aidcp-cloud 8a35cbe -->
- [x] 2.3 `comment-scheduler.ts` `outcomeToReceipt` `read_failed`：带真实 `r.reason`（对齐 `post_failed`/`targetedOutcomeToReceipt`），不再硬编码「（边端超时或离线）」；并把复检失败 reason 改成运营可读「复检时目标已不在搜索结果中（页面重排/未导航到结果页）」 <!-- aidcp-cloud 8a35cbe -->
- [x] 2.4 云端测试：① `edge-steps` 收 `action.completed{search,ok:false}` → 快速返回空 + 独立真实 reason（含 <1s 快速失败断言）；② `comment-scheduler` read_failed 回执呈现真实 reason、不含「边端超时或离线」 <!-- aidcp-cloud 8a35cbe -->
- [x] 2.5 `cd ../aidcp-cloud && npm run test:acceptance && npm test && npm run typecheck` <!-- aidcp-cloud 8a35cbe acceptance 47 + test 1745 + typecheck 0，AC-PROTO-* 原样过（无协议改动） -->

## 3. 集成 / 部署

- [x] 3.1 两仓 land 到 master（land-change：rebase 最新默认分支 + 重跑 acceptance/test/typecheck + ff 推送 + 同步主 checkout） <!-- aidcp-edge 0274cf2 / aidcp-cloud 8a35cbe -->
- [x] 3.2 部署 dev：cloud 外科式部署 2 文件（先备份 `cloud.bak.20260710-170353.tar.gz` → scp → 移入 → `systemctl restart` → healthcheck：active/NRestarts=0/8787/飞书长连接/面板 8090/概念池载入/浏览闭环正常）。**edge = edge-only 无 ECS 部署**，已在 master `0274cf2`，运营机 pull/重建后生效 <!-- aidcp-cloud 8a35cbe 2026-07-10 deployed dev；探测确认 deployed=master−本改动、外科部署仅前移不覆盖并发方 -->
- [x] 3.3 回写本 tasks.md 勾选 + sha 标注（本提交） <!-- 走 main 临时 worktree 提交（当前主 checkout 在他分支） -->

## 4. 真机验收 backlog

- [x] 4.1 登记 `docs/real-machine-acceptance-backlog.md` 簇 34：tom 分组 headful 真机跑 `/comment`，核实 AI 搜索是否真跳 `search_result_ai`、真实提交机制/选择器、结果页 URL 形态是否被 `SEARCH_LIST_RE` 覆盖；本 change 只保证失败诚实、不修提交 flakiness <!-- 簇 34 已登记 -->

## 5. 收尾

- [x] 5.1 `openspec validate comment-search-nav-confirm --strict` 通过
- [x] 5.2 全部 task 完成 + 真机项已登记 → `openspec archive comment-search-nav-confirm`
