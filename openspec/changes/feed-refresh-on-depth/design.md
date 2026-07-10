## Context

小红书 explore feed 浏览闭环是事件驱动接力（`feed.entered` 起步 → 边缘上报 `page.cards` → 云端评估 → 找不到可开笔记则 `content.no_valuable` → `FeedScroller` 发 `feed.scrolled` → 翻译成 `scroll`→`page.scroll` → 边缘真实滚轮）。

现状约束（已由代码梳理坐实）：
- **无「已浏览卡片数」计数、无 feed 深度上限**：找不到可开笔记就一直向下滚，只靠会话时长 / 动作数 / idle 看门狗收口。
- `SessionContext` 已有 `_consecutiveScrolls`（连续滚动数，达 5 转搜索）、`_lastFeedNoteIds`（仅上一批，用于 diff 出「本批新卡数」`feedBatchNewCount`）；本批新卡数当前只用于停留节奏 floor、算完即弃、从不累加。
- **协议无 refresh / 回顶 / 回到顶部 任何命令**。新增 cloud→edge 命令须走「四处同步 + 执行端主动命令白名单」（白名单 typecheck 抓不到，漏则静默丢弃——notification-monitor 活锁前车之鉴）。
- 边缘已有成熟「点击 + 后置校验」模板（点赞 / 收藏）：定位元素中心 → 验证码复检 → 拟人贝塞尔点击 → 轮询确认 DOM 真变化 → 诚实回执。

真机探针（tom 号「工程师大白」，宽 1800px + 窄 600×900 各一次）已确认：feed 右下角固定悬浮容器 `div.floating-btn-sets` 滚动后浮出、**宽窄布局结构完全一致**；内含上「回到顶部」`div.back-top`（`svg use #arrow_top`）、下「刷新」`div.reload`（`svg use #reload`）。点 `div.reload` → 滚动归零 + 首批卡全换（前 6 卡 0 重叠），满足「从新从第一条开始刷」。

## Goals / Non-Goals

**Goals:**
- 会话内累计浏览到阈值张 feed 卡后，改点右下「刷新」回到顶部换新批，代替继续向下盲滚；计数归零后周期性重复。
- 阈值与开关 env 可调；默认约 60 张、默认开启、env kill-switch 兜底。
- 全程诚实：按钮不存在 / 非 feed 页 / 点了没真换新批，都如实失败回执，绝不静默假成功；刷新失败浏览闭环不死锁。

**Non-Goals:**
- 不改「每 5 次空滚转搜索」阈值与逻辑（刷新是叠加在其之上的更粗粒度深度闸，优先级更高）。
- 不接入真实平台封号 / 限流信号（状态迁移仍是既有缺口，不在本 change）。
- 不做抖动框架 / 可插拔策略：只有「一个阈值数 + 一个开关」两个旋钮（YAGNI）。
- 不改 `PROTOCOL_VERSION`（仍为 2，仅新增一个消息类型）。

## Decisions

### D1. 新增独立消息类型 `feed.refresh`（不复用 `page.scroll`）
- **选择**：新 cloud→edge 消息 `feed.refresh`，payload `{ reason?: string; thinkMs?: number }`。
- **理由**：`page.scroll` 是「就地增量滚轮」（后置条件：scrollY 增长、卡片追加，几乎不会失败）；`feed.refresh` 是「定点点按钮」（后置条件：scrollY 归零、首卡 noteId 翻新），是**完全不同的边缘代码路径与失败模式**（按钮不存在 / 非 feed 页 vs 滚轮基本不失败）。
- **否决**：用 `page.scroll` 的 `reason==='refresh'` 魔法字符串分流——会把一整条新代码路径藏在字符串里，绕过 `Record<MessageType>` 穷举校验与执行端白名单（正是 notification-monitor 那类静默丢弃 bug 的温床）。独立类型让 switch / 白名单 / typecheck / `action.completed` 遥测都显式。代价仅一个消息类型 + 两字段 payload。

### D2. 计数器落 `SessionContext`，按「本批新卡数」累加，只在 feed 页计
- **选择**：`SessionContext` 新增 `_feedCardsBrowsed`（getter + `addFeedCardsBrowsed(n>0)` + `resetFeedCardsBrowsed()`）；在云端 `page.cards.arrived` 处理里、既有 `sourcePageType==='feed'` 分支内、拿到 `feedBatchNewCount` 增量后顺手累加。
- **理由**：「盲滚深度」= 会话内见过的**不重复 feed 卡**数；该增量已为节奏 floor 算好、算完即弃，累加它零新增 DOM 探测、天然去重。搜索结果批（`sourcePageType==='search'`）不计——用户要的是「feed 卡片」。
- **否决**：计打开的笔记数（远达不到阈值、且量的是互动不是滚动深度）；计 `page.cards` 原始批次数（重复出现的卡会重复计）。

### D3. 触发点在 `FeedScroller.scrollOrSearch` 顶部
- **选择**：`scrollOrSearch()` 一进来、在「滚 vs 转搜索」分支之前判：`enabled && ctx.feedCardsBrowsed >= threshold` → `resetFeedCardsBrowsed()` + `resetScrolls()` + 发内部事件 `feed.refresh.needed` 并 return（本轮不滚不搜）。
- **理由**：`scrollOrSearch` 是**唯一的「即将在 feed 上向下滚」决策点**（只在 feed 的 `content.no_valuable` / `search.skipped` 到达）。本功能字面就是「到点了别滚、改刷新」，分支就该落在这个决策点；`FeedScroller` 已持有 `SessionContext` 并管着姊妹计数 `consecutiveScrolls`。
- **否决**：放调度器翻译层（那层只是薄的事件→命令映射，把阈值策略搁那会把滚动决策劈成两个文件）；放 `page.cards.arrived`（正常有价值浏览时也会触发，会在正互动时误刷新）。

### D4. 复位语义：乐观复位（emit 时即归零），per-session
- **选择**：在 `FeedScroller` 决策处**即刻**复位 `_feedCardsBrowsed` 与 `_consecutiveScrolls`（不等回执）；`SessionContext.reset()` 里也把 `_feedCardsBrowsed` 归零（与 `_consecutiveScrolls` 一致，per-session、重连即重置）。跨「开笔记→互动→返回」在同一会话内累计。
- **理由**：乐观复位是**去抖**——即便点击失败也不会紧接着再触发，避免「刷新→失败→滚→又到阈值→再刷新」的锤击。计数归零 + 新顶批重新累加 = 自然实现「每 N 张重复」，无需额外 modulo。
- **否决**：只在确认 `ok:true` 才复位（点击反复失败会锤击）；像 `visitedNoteIds` 那样跨 `reset()` 存活（会把深度泄漏到下一逻辑会话，与 per-session 语义矛盾）。
- **权衡**：见 R2（软暂停丢命令 → 本轮刷新静默跳过、预算已花）。

### D5. 节奏复用 `action` 档；计入动作数、不耗互动配额
- **选择**：云端随命令带 `thinkMs`（`thinkNow()`）；边缘经 `gateBeforeAction('action', thinkMs)`（最小间隔 + lognormal 抖动）。**不**新增 PACING_OP。边缘成功 / 失败都发 `action.completed{action:'refresh', ok}`；计入 `SessionMonitor.actionCount`（真发生了一个导航动作、且稀有可忽略），**不**是 `RiskAction`、不消耗互动配额、无 `canInteract` 闸。经统一命令出口下发 → 软暂停期间自动被抑制（正确：不在暂停中刷新）。
- **否决**：新增 `refresh` PACING_OP（过度设计）；当互动动作烧配额（风控语义错）。

### D6. 刷新后闭环续驱：成功单次 `page.cards`、失败走既有兜底滚动
- **选择**：`ok:true` 时边缘额外 `reportVisibleCards()`（新顶批）→ 一次 `page.cards` 驱动闭环；`ok:false` 时只回 `action.completed` → 命中调度器既有「失败动作兜底」发一次恢复滚动（reason `recover_after_refresh_failed`），`refresh` **不**加进 `noRecoverScroll` 集。两条出口各恰好一次驱动。
- **否决**：失败也 `reportVisibleCards`（会把陈旧卡当新批误报）；`refresh` 加进 `noRecoverScroll`（失败即死等 idle 看门狗 ~2min 才 nudge）。

### D7. 边缘 `refreshFeed` 诚实执行 + 硬化后置校验
- 顺序：① URL 闸 `EXPLORE_FEED_RE`，非 feed → `ok:false, reason:'wrong_context'`；② 定位 `.floating-btn-sets` 及其 reload 子节点（class 含 `reload` 且非 `back-top`，退路 `svg use[href="#reload"]`），缺失 → `ok:false, reason:'no_floating_btn'|'no_reload_btn'`；③ `gateBeforeAction('action', thinkMs)`；④ `captchaPresentFresh()` → 有则 `ok:false, reason:'blocked_by_captcha'`（fail-closed、不点）；⑤ **点击前一刻**单次 eval 抓 pre-state（scrollY + 首卡 noteId）；⑥ 拟人点击；⑦ `pollDomUntil`（~2000ms）**仅当出现具体新首卡**才通过：`typeof first?.noteId==='string' && first.noteId.length>0 && first.noteId!==preFirstNoteId && scrollY<100`；⑧ 通过 → `reportVisibleCards()` 后 `ok:true`；不通过 → `ok:false, reason:'not_reloaded'` 且**不**报卡；try/catch → `ok:false, reason:err.message`。
- **对抗评审两处硬化**（已并入上面）：
  - 后置校验必须要求**具体非空新首卡**——否则刷新后首卡瞬时为空 / 无 noteId 时 `undefined!==pre` 恒真，退化成「只看 scrollY 归零」，纯回到顶部就会冒充换新批（违反「绝不静默假成功」红线）。
  - pre-state 在 think-gate **之后、点击前一刻**抓——否则 think 停顿窗内 feed 异步重渲染会让陈旧 pre 值误判通过。

## Risks / Trade-offs

- **R1 阈值可达性** → 缓解：默认下调到约 60（对抗评审实证：10min / 60 动作会话 + 转搜索停计数下，200 常达不到、功能会形同虚设）；env 可调回 200。真机验收时记录「每会话实际浏览卡数」校准。
- **R2 软暂停丢刷新** → 缓解：乐观复位下，若 `feed.refresh` 在软暂停（`viewQuotaSleeping`/`browseSuspended`）被统一出口抑制，则本轮刷新静默跳过、计数已归零、要再过 N 张才重试。诚实（无假成功）、与滚动被抑制同构，可接受；在 spec / 失败模式里明记「软暂停 = 刷新本轮跳过、不重试」。
- **R3 按钮改版 / 布局漂移** → 缓解：定位用 class(`reload`) + `svg use(#reload)` 双信号 + 排除 `back-top`；缺失即诚实 `no_reload_btn`；探针脚本留仓便于复标定。宽窄已实证同构，不分双写。
- **R4 协议白名单漏接** → 缓解：tasks 显式列白名单为独立任务，land 前人工核对 + 边缘路由回归断言（typecheck 抓不到这处）。
- **R5 `docs/protocol.md` 计数已过期（61 vs 实际 70）** → 缓解：本 change 顺手修正到 71，并注明表滞后于计数。

## Migration Plan

- 部署：随 dev 默认部署上线、**默认开启**；env `AIDCP_FEED_REFRESH=false` 秒级关闭回滚，`AIDCP_FEED_REFRESH_AFTER` 调阈值无需改码。
- 回归纪律（协议改动）：两仓先 `npm run test:acceptance`（`AC-PROTO-*` 不漂移）再全量 `npm test`，再 `npm run typecheck`；两份 `protocol.ts` 逐字一致、计数 71。
- 真机验收：dev 上真机点刷新是否真「回顶 + 换全新一批」、误判是否退回滚动——登记到 `docs/real-machine-acceptance-backlog.md`；探针 `scripts/feed-refresh-button-probe.ts` 复用。

## Open Questions

- 阈值默认 60 是否需按真机实测的「每会话浏览卡数」进一步微调（等 dev 真机数据）。
- 长期是否让 feed-card 计数在「转搜索又回 feed」后继续累加（当前转搜索即停计），取决于运营是否观察到搜索占比过高稀释了刷新触发——暂不做（YAGNI），留观察。
