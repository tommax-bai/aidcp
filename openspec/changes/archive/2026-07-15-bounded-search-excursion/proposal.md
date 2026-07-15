## Why

浏览闭环会把账号带到 **Facebook 全站搜索结果页**（概念池搜索触发），然后**把它钉在那里没有有界出口**。三个具体缺口叠在一起（真机实测，FB 账号 `61591753702668` 在搜索结果页反复「读一篇→pass→滚→换词再搜」几十分钟不回首页）：

1. **从首页发起搜索太急**：首页连续 5 屏无收获就转搜索（`SEARCH_THRESHOLD=5`）。用户希望更耐心地留在首页浏览。
2. **云端「当前在哪页」状态自指恒等、永远停在 `feed`**：唯一写入者是「决定要看某张卡」时回写的来源页型，而来源页型又等于会话上下文里的当前值——写回=读出、永不改变（`role-dispatcher.ts:2124` ↔ `content-evaluator.ts:151` ↔ `note-opener.ts:33`）。后果：搜索结果页被当成 feed 处理，搜索翻页角色 `SearchScroller` 已注册却永不触发，搜索结果卡还被错误计入 feed 浏览深度。
3. **搜索结果页没有「离开」的出口**：一旦进搜索页就留着。今天唯一能回首页的路径，是 feed 深度到 60 张卡触发的「刷新回顶」——而这条路径**正是因为缺口 2 把搜索卡误计入 feed 深度才偶然生效**；缺口 2 一修，这条偶然出口消失，账号会被 `SearchScroller` 死死留在搜索页（换词再搜到预算耗尽后仍空滚）。

## What Changes

**核心是给搜索行程装上「有界进入 + 正确页型 + 有界退出」三段闸，全部落在云端一处，不碰协议/边缘/角色注册。**

1. **首页→搜索触发阈值 5 → 20**（`SEARCH_THRESHOLD`，加 env 旋钮 `AIDCP_FEED_SEARCH_THRESHOLD` 默认 20）：首页连续 20 屏无收获才转搜索，更耐心。已核实 FB 每屏约 1–3 张卡，20 屏≈20–60 张卡、落在 60 张刷新阈值之内，所以 FB 上搜索仍会触发（不被刷新抢先）。
2. **修页型自指 bug**：在**真正下发搜索指令那一刻**把当前页型标为 `search`（不在被闸拦下/未下发的搜索上标），回首页时标回 `feed`。于是搜索结果页由 `SearchScroller` 正确驱动，搜索卡不再计入 feed 深度。**唯一权威写入点 = 实际导航到搜索页的那一处**，避开「被限频拦下的搜索仍误标 search」的假翻转。
3. **搜索行程有界退出**：在搜索结果页**累计划过 20 张不重复卡片**后，回首页（复用既有的 `refresh`→回顶换首页 指令，不新增协议）。计数用与 feed 深度同样的「不重复新卡差分」，天然也覆盖「搜索页一篇都点不开」的空转场景——空滚照样累计卡数，到 20 即回首页，绝不卡死。阈值 env 可调 `AIDCP_SEARCH_HOME_RETURN_AFTER`（默认 20）。

**已核实不需要做的**（避免过度设计）：不新增事件类型、不新增角色、不改 `SearchScroller`（缺口 2 修好后它自动被正确路由激活）、不改边缘、不改协议、不改主动命令白名单——回首页复用 `refresh` 指令（`reason` 是自由字符串，边缘既有 `refreshFeed` 已把浏览器带回首页并复位 `activeFeedUrl`）。`sourcePageType` 的权威写入放在「实际下发搜索」而非泛化的 `feed.entered` 订阅，正是为避开搜索被限频拦下时 `SearchExecutor` 仍无条件 emit `feed.entered('search')` 造成的误翻转。

## Capabilities

### Modified Capabilities
- `concept-pool-search`: 首页→搜索触发阈值为 20；浏览闭环必须据「真实下发搜索」而非自指默认值追踪当前在 feed 还是 search 页；一次搜索行程累计浏览到有界卡数后必须回到首页。

## Impact

- **仅 `aidcp-cloud`**。
- 文件：`src/agents/feed-scroller.ts`（阈值 + env）、`src/agents/session-context.ts`（搜索卡计数器 + 差分基准 + reset）、`src/orchestrator/role-dispatcher.ts`（下发搜索时标 `search`、`page.cards` 处理器里搜索卡累计 + 到阈值回首页）、`src/agents/search-scroller.ts`（仅导出 `SEARCH_HOME_RETURN_AFTER` 常量供 dispatcher 引用）。
- **协议不变、消息类型数不变、主动命令白名单不变、`RoleName` 穷举不变**（`AC-PROTO-*` 不动）。回首页复用既有 `refresh` 指令。
- **边缘零改动**。
- **向后兼容 / 平台影响**：`sourcePageType` 修复只让搜索页被正确处理（feed 行为逐字节不变）。回首页闸 `canRefresh()` 门控——平台不支持刷新时不回首页（诚实降级，非卡死加剧）。**小红书副作用**：XHS 每屏约 10 张卡，20 屏≈200 张卡 > 60 张刷新阈值，故 XHS 上「首页自动搜索」会变得很稀（刷新先触发）；FB 是本次目标，若要 XHS 保持原节奏可后续把阈值做成 per-platform。两个阈值均 env 可秒回滚。
