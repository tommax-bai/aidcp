## Context

Facebook 浏览闭环的执行端在 `aidcp-edge/src/facebook/`。现状（坐实到 `文件:行`）：

- **回归**：`facebook-session.ts:574` 的 `scrollFeed()` 在滚动前调 `feedReader.ensureFeed(activeFeedUrl)`，而 `feed-reader.ts:180` 的 `ensureFeed()` **首句就是无条件 `Page.navigate`**。于是每条滚动命令 = 整页重载 + 只滚 650px（`feed-reader.ts:244` `scrollNext`），深度攒不起来。回归由 edge `7b9b37e`（2026-07-13）引入。
- **每屏 1 卡**：两道 existence gate 串联——`feed-reader.ts:147-153` `FEED_READY_JS` 只要 1 篇文章有作者链接即判就绪；`facebook-session.ts:637-647` `scanFeedCardsWithHydrationRetry` 第一次扫到 ≥1 张就返回。FB feed 虚拟化，刚加载只有顶部 1 篇真、其余空壳（`feed-reader.ts:221` 正确跳过空壳，守绝不假成功红线）。
- **split-brain**：`backToFeed()`（`facebook-session.ts:614-625`）与 `navigateFeedBestEffort()`（`:755-761`）都用会话初始 `this.feedUrl` 回首页，而非当前 `this.activeFeedUrl`。从搜索结果开帖后返回被带回首页、搜索结果丢失。
- **refresh 空占位**：`feed.refresh` 落在 `facebook-session.ts:399-411` 的 `reportUnsupportedCommand` 筐，回 `refresh:capability_unsupported`。而云端 `feed-scroller.ts` 在深度达阈值时确实会下发它。

现成可复用：`probes/page-structure.ts:60` `classifyFacebookSurface(href)` 返回 `home|search|group|page|page_post|group_post|login|checkpoint|unknown`；`viewport-scroll.ts:53` `scrollFacebookViewport`；`overlay-monitor` 的 `probeNow()` fail-closed 复检；`consent` 拟人接受。协议消息 `feed.refresh` 已存在（XHS 已实装），FB 只补处理器。

## Goals / Non-Goals

**Goals:**
- 滚动命令保住滚动位置：已在目标列表面（首页/搜索页）且无 dialog 就不再重新导航（消回归）。
- 详情返回落回发起浏览的当前列表面（修 split-brain）。
- feed 卡片按 loading-aware 累积判稳后上报，替换而非叠加两道 existence gate。
- `feed.refresh` 在 FB 上实装为顶栏首页图标页内点击换批、诚实后置校验、`Page.reload` 兜底受限。
- 全程 edge-only、不改协议、可 jsdom/桩测。

**Non-Goals:**
- 不做 click-to-open 浏览改造（点卡出 dialog）——留给后续独立 change（已实机验证可行、但风险集中需真机门槛）。
- 不改群加入（本就是页内 `element.click`）、不改评论（价值低、撞 keep-open）、不做 click-driven search（flaky、价值低）。
- 不改结构性 URL 跳转本身（`note.open` 仍整页导航到 permalink）——只消掉「滚动前的多余重载」。
- 云端刷新阈值调整（FB 60 偏浅）为可选、跨仓，非本 change 必须项。

## Decisions

### D1. `ensureFeed` 拆成「探面 + 按需导航」，两条路径都跑 fail-closed 门
把 `ensureFeed(url)` 改为：先 `probeSurface()` 探一次 `{ href, surface, hasFeed, hydratedArticles, dialogOpen }`；当 `classifyFacebookSurface(href)` 等于目标 URL 的 surface、且属列表面（home/search/group）、`hasFeed` 为真、无 dialog 时——**直接进入前置门校验后返回 ok，不 `Page.navigate`**；否则才导航。**关键红线**：consent 预清理 + `blockingReason()` 登录/验证码复检在**两条路径都必须跑**（现搭在导航步骤里，不能因省导航而漏）。
- 为什么不用「会话内布尔 flag 记住已在 feed」：外部导航/详情跳转会让 flag 陈旧，探测当前页才是真相源。
- 为什么复用 `classifyFacebookSurface` 而非写死首页：`ensureFeed` 同时被搜索支线调用（`facebook-session.ts:600`），写死首页会把搜索页误判为要导航、把用户带离搜索结果。

### D2. loading-aware 累积判稳，MERGE 替换两道 gate
在 `feed-reader.ts` 新增 `settleCards(opts)`：循环每轮约 450–600ms 调**同一个** `scanCards()`（不另起抽取口径），比对相邻两轮真卡的 noteId 集合；同时满足 ① 真卡数 ≥ `minCards`(默认1) ② 两轮集合相等 ③ feed 区域无 loading 信号（仅按 `role="progressbar"` / `aria-busy="true"`，**绝不认骨架屏 CSS 类名**）时返回 `{ cards, degraded:false }`。loading 信号是单向「继续等」否决票：集合已稳但仍 loading 则继续等。硬 wall-clock 上限（导航后~6s、滚动后~3.5s）；到点：有 ≥1 真卡→返回 `{cards, degraded:true}`（degraded 只进边缘日志、**不进 PageCardsPayload 契约**）；0 卡+loading→`feed_still_loading`；0 卡+无 loading→`no_feed`。
- `ensureFeed` 的 14×900ms 水合循环删掉——`ensureFeed` 只留「导航（按需）+ 前置门」，把**所有等水合的耗时收进 `settleCards` 这一个循环**；`facebook-session.ts` 的 `scanFeedCardsWithHydrationRetry`（6×700ms）被 `settleCards` 取代。三段合一，避免 ~23s 逼近 90s 命令超时。
- 判稳循环内保留有界的 `blockingReason()` 复检，等待期间弹验证码也 fail-closed。

### D3. `feed.refresh` 实装为顶栏首页图标页内点击
`facebook-session.ts` 把 `feed.refresh` 从 unsupported 筐移到 `runBrowseCommand('refresh', () => this.refreshFeed())`。`refreshFeed()`：
1. 确认在 explore feed（surface=home）——否则 `wrong_context`。
2. `settleCards` 取点击前首卡 permalink 作基线。
3. 结构性定位 `[role="banner"] a[href="/"]`（**绝不按「Home/首页」文案**）→ 页内 `element.click()`；定位不到回 `no_home_link`。
4. 显式 `window.scrollTo(0,0)`（实机证实换批不自动回顶）。
5. `settleCards` 重扫，**后置校验 = 首卡 permalink 非空且 ≠ 基线**；成立→回 `type=cards`（新批，单一终态）；否则 `not_refreshed`。
6. 前置验证码/consent 复检不过→`blocked_by_captcha`/`blocked_by_consent`，不点击。
- **`Page.reload` 兜底**：仅在页内点击换批不可用时、且带频率下限（同会话两次 reload ≥3min，用 `lastReloadAt` 时戳）；只在 `refreshFeed` 内可达，恢复/滚动路径不可达（不碰 `noRecoverScroll`）。
- **单一终态**：成功只回 `cards`（既推进云端循环又是成功信号），不另发 `ok`；失败回 `action ok:false + reason`。

### D4. split-brain：回列表面用 `activeFeedUrl`
`backToFeed()` 改用 `this.activeFeedUrl`（删掉 `this.activeFeedUrl = this.feedUrl` 复位）；`navigateFeedBestEffort()` 改用 `this.activeFeedUrl`（`closeNote` 经它关 dialog 也随之落回正确列表面；`session.end` 走它无副作用）。

### D5. 桩测优先
`probeSurface` / `settleCards` / `refreshFeed` 全部走 `BrowseCdp` 的 `send` 桩：注入可脚本化的 `Runtime.evaluate` 返回序列（先 loading、后水合、首卡 permalink 变更）即可断言判稳、幂等跳导航、刷新后置校验。断言：连续 `page.scroll` 后无 `Page.navigate`；从搜索开帖 `navigation.back` 落回搜索 URL；刷新首卡未变→`not_refreshed` 不报卡。

## Risks / Trade-offs

- **[省导航漏了 fail-closed 复检]** → D1 显式要求两条路径都跑 consent + blockingReason；桩测加「在首页但验证码浮层在→scroll 回 blocked_by_captcha 且不滚」用例。
- **[settle 把命令拖到超时]** → 三段合一 + 硬 wall-clock（滚动后 3.5s、导航后 6s）远低于 90s；degraded 早退保证有卡就报。
- **[loading 信号误认骨架屏 → 永等到超时]** → 只按 `role=progressbar`/`aria-busy` 匹配，绝不认 CSS 类名；且 wall-clock 兜底早退。
- **[refresh 后置校验误判]** → 判据用「首卡 permalink 变更且非空」而非「滚动回顶」（实机证实回顶不可靠）；未变即 `not_refreshed` 诚实失败、不报陈旧卡。
- **[reload 兜底又变整页重载放大器]** → 频率下限 ≥3min + 仅 refresh 路径可达；恢复/滚动路径永不触发。
- **[真机行为未覆盖]** → 桩测只证逻辑；FB 真机深度浏览（连续滚不重载、搜索返回不丢、点首页图标真换批）登记 real-machine backlog。

## Migration Plan

1. edge 改 `feed-reader.ts`（`probeSurface` + `settleCards`，删 `ensureFeed` 水合循环）、`facebook-session.ts`（`scrollFeed`/`backToFeed`/`navigateFeedBestEffort` 用 `activeFeedUrl` + surface 幂等、`feed.refresh` 处理器、`scanFeedCardsWithHydrationRetry`→`settleCards`）。
2. 补/改桩测 + `npm run test:acceptance` + `npm test` + `npm run typecheck`。
3. commit / push edge `master`；默认部署 dev（edge 本地跑、连 dev 云端）。真机验收登记 backlog。
4. 回滚：edge revert 单 commit 即恢复原 `ensureFeed`；无协议/DB 变更，零迁移。

## Open Questions

- 云端 FB 刷新阈值（`feed-scroller.ts:22-25` 默认 60，FB 偏浅）是否本批一并调？倾向**否**（跨仓、可选、单独 change 更干净）；本 change 先只让 FB 刷新真能执行。
