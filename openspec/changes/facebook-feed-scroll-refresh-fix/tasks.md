## 1. aidcp-edge — 幂等 surface 检查 + 修 split-brain（Q4）

- [x] 1.1 `feed-reader.ts`：新增 `probeSurface()`，一次 `Runtime.evaluate` 返回 `{ href, hasFeed, hydratedArticles, dialogOpen }`；`surface` 在 Node 侧用 `classifyFacebookSurface(href)` 归类 <!-- aidcp-edge adf10f8 -->
- [x] 1.2 `feed-reader.ts`：把 `ensureFeed(url)` 改为「探面→按需导航」——当 `classifyFacebookSurface(href)===classifyFacebookSurface(url)` 且属列表面(home/search/group) 且 `hasFeed` 且无 dialog 时直接进前置门、不 `Page.navigate` <!-- aidcp-edge adf10f8 -->
- [x] 1.3 `feed-reader.ts`：红线——consent 预清理 + `blockingReason()` 登录/验证码复检在**不导航路径也必须跑**（fail-closed 不得因省导航而漏） <!-- aidcp-edge adf10f8 桩测 ensureFeed 红线 -->
- [x] 1.4 `facebook-session.ts`：`backToFeed()` 用 `this.activeFeedUrl`（删 `activeFeedUrl=feedUrl` 复位）；`navigateFeedBestEffort()` 用 `this.activeFeedUrl` <!-- aidcp-edge adf10f8 -->
- [x] 1.5 桩测：连续 `page.scroll` 后不 `Page.navigate`（feed-reader 幂等桩证 navs=[]）；从搜索开帖后 `navigation.back` 落回搜索 URL 非首页；在首页但验证码浮层在→`blocked_by_captcha` 且不导航 <!-- aidcp-edge adf10f8 -->

## 2. aidcp-edge — loading-aware 累积判稳（Q1，MERGE 替换两道 gate）

- [x] 2.1 `feed-reader.ts`：新增 `settleCards({ minCards, wallClockMs, roundMs })`——循环每轮调同一 `scanCards()`，比对相邻两轮真卡 noteId 集合；三条件(≥minCards / 集合相等 / 无 loading 信号)全满足才返回 <!-- aidcp-edge adf10f8 -->
- [x] 2.2 `feed-reader.ts`：loading 信号仅按 `role="progressbar"`/`aria-busy="true"` 识别（绝不认骨架屏 CSS 类名），作单向「继续等」否决票；wall-clock 到点分三态返回 `{cards,degraded}` / `feed_still_loading` / `no_feed` <!-- aidcp-edge adf10f8 -->
- [x] 2.3 `feed-reader.ts`：删掉 `ensureFeed` 的 14×900ms 水合循环（`FEED_READY_JS`/`feedReady` 已退役），等水合耗时全收进 `settleCards`；判稳循环内保留有界 `blockingReason()` 复检 <!-- aidcp-edge adf10f8 -->
- [x] 2.4 `facebook-session.ts`：`scanFeedCardsWithHydrationRetry`(6×700ms) 由 `settleCards` 取代；`degraded` 只进边缘日志、**不进 `PageCardsPayload`** <!-- aidcp-edge adf10f8 -->
- [x] 2.5 桩测：脚本化 evaluate 序列断言判稳只在集合稳且无 loading 时上报；到 wall-clock 有卡→照实报+degraded；0 卡+loading→`feed_still_loading`；空壳绝不上报 <!-- aidcp-edge adf10f8 feed-reader.test.ts 4 例 -->
- [x] 2.6 核对 dwell floor：确认边缘无按批数计的 dwell 地板（`dwellFloorMs` 是详情页固定区间 2500-5000ms，与 `feedBatchNewCount` 无关）；`feedBatchNewCount~1` 瘪缩为**云端**概念，随 Q1 多卡批自然缓解，edge-only 范围内无需改 <!-- aidcp-edge adf10f8 grep 证无边缘批数地板 -->

## 3. aidcp-edge — `feed.refresh` 实装为页内点首页图标（Q3）

- [x] 3.1 `facebook-session.ts`：把 `feed.refresh` 从 `reportUnsupportedCommand` 筐移到 `runBrowseCommand('refresh', () => this.refreshFeed())` <!-- aidcp-edge adf10f8 -->
- [x] 3.2 `facebook-session.ts`/`feed-reader.ts`：`refreshFeed()`——`ensureFeed` 幂等确认在 feed→取点击前首卡 permalink 基线→`clickHomeAndScrollTop()` 结构性定位 `[role="banner"] a[href="/"]` 页内 `element.click()`(定位不到 `no_home_link`)→显式 `scrollTo(0,0)` <!-- aidcp-edge adf10f8 -->
- [x] 3.3 后置校验 = 刷新后 `settleCards` 首卡 permalink 非空且 ≠ 基线：成立→回 `type=cards`(单一终态)；否则 `type=action ok:false reason='not_refreshed'`，绝不报陈旧卡 <!-- aidcp-edge adf10f8 -->
- [x] 3.4 前置门经 `ensureFeed` 复检（验证码/consent 不过→对应 reason 不点击）；`Page.reload` 兜底仅页内换批不可用时且频率下限 ≥3min(`refreshReloadAllowed` 纯函数 + `lastReloadAt`)、仅 refresh 路径可达、不碰 `noRecoverScroll` <!-- aidcp-edge adf10f8 -->
- [x] 3.5 桩测：首页图标存在且首卡变更→回 cards（无 action.completed）；首卡未变→`not_refreshed` 不报卡；无首页锚点且 reload 失败→`no_home_link`；`refreshReloadAllowed` 首次/下限内/超下限三态 <!-- aidcp-edge adf10f8 -->

## 4. 验证与部署（edge-only）

- [x] 4.1 `npm run test:acceptance`（AC-PROTO / AC-PUB 全过，AC-E2E gated） <!-- aidcp-edge adf10f8 19/19 -->
- [x] 4.2 `npm test` 全量（1191 pass 0 fail）+ `npm run typecheck`（clean） <!-- aidcp-edge adf10f8 -->
- [x] 4.3 commit + push edge `master`（origin/master=adf10f8）；edge 为本地桌面客户端、无 ECS cloud 改动，运行时连 dev 云端即生效 <!-- aidcp-edge adf10f8 pushed -->
- [x] 4.4 真机深度浏览验收（连续滚不重载 / 搜索返回不丢 / 点首页图标真换批不重载 / 每屏多卡 / fail-closed）登记 `docs/real-machine-acceptance-backlog.md` 簇 72（72.1-72.5） <!-- 2026-07-14 registered -->


## 5. （可选、跨仓 cloud，非本 change 必须）FB 刷新阈值

- [ ] 5.1 （可选，**本 change 不做**）`aidcp-cloud/src/agents/feed-scroller.ts:22-25`：加 `AIDCP_FEED_REFRESH_AFTER_FB` 默认~120（FB 60 偏浅）；纳入则须走 cloud ECS 部署序列，留独立 change
