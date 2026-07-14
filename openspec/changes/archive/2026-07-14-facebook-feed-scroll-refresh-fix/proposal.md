## Why

本地 Facebook 首页浏览「看一两条就整页刷新、永远滚不下去、每屏只报 1 张卡」。实机 CDP 只读探针实测：44 秒内整页重载 5 次、`scrollY` 每次归零，云端却以为在往深处走。根因已坐实到 `文件:行`，且修法已在 Dennis 环境实机验证。本 change 只收口这条回归 + 把「刷新」从空占位实装成真动作，**edge-only、不动协议、可桩测/jsdom 验证**；点卡出 dialog 的浏览改造留给后续独立 change。

## What Changes

- **幂等 surface 检查（Q4）**：把「断言在 feed 上」从「无条件重置到 feed（整页 `Page.navigate`）」改成「先探一次、已在目标列表面（首页或搜索页）且无 dialog 就直接放行、不导航」。这一条消掉回归 edge `7b9b37e`（`scrollFeed()` 滚前调 `ensureFeed()`、而 `ensureFeed()` 首句就是无条件导航）。红线：不导航的路径**仍必须**跑登录/验证码复检 + consent 预清理（现搭在导航步骤里，不得因省导航而漏、破坏 fail-closed）。
- **修 split-brain（Q4 附带真 bug）**：从搜索结果开帖后返回，`backToFeed` / `navigateFeedBestEffort` 用会话初始 `feedUrl` 回首页而非当前 `activeFeedUrl` 的搜索页，导致搜索结果丢失、下次从头重搜。改用 `activeFeedUrl`。
- **loading-aware 累积判稳（Q1）**：用「已水合帖子集合稳定 + 无 loading 信号 + wall-clock 兜底」三条件判稳后再上报，**MERGE 替换**现有两道 existence gate（就绪判据只要 1 篇水合即就绪 + 扫卡第一次 ≥1 张就返回），而非叠加（叠加会堆到 ~23s 逼近 90s 命令超时）。FB feed 虚拟化下空壳仍被正确拒绝（守绝不假成功红线，要修的是多等真水合、不是放宽过滤）。顺带修因 1 卡批而瘪掉的 dwell floor。
- **`feed.refresh` 实装（Q3）**：把 Facebook 的 `feed.refresh` 从 `capability_unsupported` 筐挪到真处理器——结构性定位顶栏首页图标（`[role=banner] a[href="/"]`，绝不按「Home/首页」文案）做**页内 `element.click()`**（实机证实是 SPA 换批、零整页重载），刷新后显式带回顶。后置校验判据 = **首卡 permalink 变了且非空**（实机证实「滚动归零」不可靠、不能作判据）；`Page.reload` 仅作带频率下限（≥3min）的兜底档。协议消息 `feed.refresh` 已存在（XHS 已实装），FB 补处理器**不改协议**。

## Capabilities

### New Capabilities
- `facebook-feed-continuity`: Facebook feed 浏览的连续性——滚动命令保住滚动位置（幂等 surface 断言，已在目标列表面就绝不重新导航）、feed 卡片只在 loading-aware 累积判稳后上报、详情返回落回正确的列表面（搜索页 vs 首页）。含 fail-closed 复检不得因省导航而漏、绝不假成功、绝不臆造空壳卡三条红线。

### Modified Capabilities
- `feed-depth-refresh`: 新增 Facebook 专属的刷新**执行**要求——经顶栏首页图标页内点击换批（区别于小红书右下「刷新」按钮），后置校验判据为「首卡 permalink 变更且非空」而非「滚动回顶」，并带 `Page.reload` 频率下限兜底档；不改动既有小红书刷新执行要求，也不改云端深度计数/阈值/复位要求（协议消息 `feed.refresh` 复用现有、不新增）。

## Impact

- **aidcp-edge（主体）**：`src/facebook/feed-reader.ts`（`ensureFeed` 拆分为探面+按需导航、settle 判稳合并两道 gate）、`src/facebook/facebook-session.ts`（`scrollFeed` / `backToFeed` / `navigateFeedBestEffort` 的 surface 与 `activeFeedUrl` 修正、`feed.refresh` 处理器落地、dwell floor）。均可 jsdom/桩测。热点文件 `feed-reader.ts` / `facebook-session.ts` 为单写者，实装期须认领防撞。
- **aidcp-cloud（可选、跨仓、单独标注）**：`src/agents/feed-scroller.ts` 可加 FB 专属刷新阈值默认（FB 60 张偏浅、约 120 更合适），非本 change 必须项。
- **协议**：无改动（`feed.refresh` 消息既存）。
- **部署**：edge-only，本地桩测/jsdom 验证即可，默认 dev。真机深度浏览验收登记 backlog（共享真机环境簇）。
