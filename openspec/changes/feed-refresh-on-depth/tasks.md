# Tasks — feed-refresh-on-depth

> 协议改动：热点文件（两份 `protocol.ts`、cloud `command-bridge.ts` 动作映射、`role-dispatcher.ts` `EdgeCommand.action` 并集）单写者串行、勿与并发 session 同时碰。
> 回归纪律：两仓改完先 `npm run test:acceptance`（`AC-PROTO-*` 不漂移）→ 全量 `npm test` → `npm run typecheck`；两份 `protocol.ts` 逐字一致、消息类型计数 71。
> 落定：cloud master `c4545f0`、edge master `60088d7`；cloud 已部署 dev（2026-07-10）。archive 待真机验收（簇 33）。

## 1. 协议消息类型（四处同步之一：两端 protocol.ts 逐字一致）

- [x] 1.1 aidcp-cloud `src/comm/protocol.ts`：`MessageType` 并集在 `'page.scroll'` 之后加 `| 'feed.refresh'` <!-- cloud c4545f0 -->
- [x] 1.2 aidcp-cloud `src/comm/protocol.ts`：`PageScrollPayload` 之后加 `export interface FeedRefreshPayload { reason?: string; thinkMs?: number }` <!-- cloud c4545f0 -->
- [x] 1.3 aidcp-cloud `src/comm/protocol.ts`：`PayloadMap` 在 `'page.scroll'` 后加 `'feed.refresh': FeedRefreshPayload;` <!-- cloud c4545f0 -->
- [x] 1.4 aidcp-edge `src/comm/protocol.ts`：与 1.1/1.2/1.3 **逐字一致**镜像（同位置、同注释风格） <!-- edge 60088d7 逐字一致，仅行号偏移 -->
- [x] 1.5 两仓 `npm run typecheck` 确认 `Record<MessageType,true>` 穷举通过、两份 protocol.ts 不漂移 <!-- cloud c4545f0 / edge 60088d7 typecheck 绿 -->

## 2. aidcp-cloud — 计数器 / 触发 / 翻译 / 兜底

- [x] 2.1 `src/agents/session-context.ts`：加 `private _feedCardsBrowsed = 0`；getter `feedCardsBrowsed`、`addFeedCardsBrowsed(n)`（`n<=0` 忽略）、`resetFeedCardsBrowsed()`；`reset()` 内把 `_feedCardsBrowsed` 归零（与 `_consecutiveScrolls` 并列，per-session） <!-- cloud c4545f0 -->
- [x] 2.2 `src/orchestrator/role-dispatcher.ts`：`page.cards.arrived` 处理里、既有 `sourcePageType==='feed'` 分支内、拿到 `feedBatchNewCount` 增量后调用 `sessionContext.addFeedCardsBrowsed(newCount)`（搜索批不计） <!-- cloud c4545f0 -->
- [x] 2.3 `src/event-bus/types.ts`：加 `FeedRefreshNeededPayload { cardsBrowsed: number; currentPageType: 'feed'; ts: number }` 与 `RoleEventMap['feed.refresh.needed']`（内部事件，非协议消息、不计入 MessageType） <!-- cloud c4545f0 -->
- [x] 2.4 `src/agents/feed-scroller.ts`：加 env 读取（`AIDCP_FEED_REFRESH` 默认开、仅 `==='false'` 关；`AIDCP_FEED_REFRESH_AFTER` 默认 60、非法回落 60）+ 可选第 3 构造参数供测试注入；`scrollOrSearch()` 顶部（滚/搜分支之前）：`enabled && ctx.feedCardsBrowsed >= threshold` → `resetFeedCardsBrowsed()` + `resetScrolls()` + emit `feed.refresh.needed` 并 return <!-- cloud c4545f0 -->
- [x] 2.5 `src/orchestrator/role-dispatcher.ts`：`EdgeCommand.action` 并集加 `'refresh'` <!-- cloud c4545f0 -->
- [x] 2.6 `src/orchestrator/role-dispatcher.ts` `setupCommandTranslation`：订阅 `feed.refresh.needed` → `sendCommand({ action:'refresh', reason:'feed_refresh', params:{ thinkMs: this.thinkNow() } })` <!-- cloud c4545f0 -->
- [x] 2.7 `src/comm/command-bridge.ts`（四处同步之二）：`case 'refresh': return createEnvelope('feed.refresh', { reason: command.reason, ...command.params });` <!-- cloud c4545f0 -->
- [x] 2.8 `src/orchestrator/role-dispatcher.ts`：确认 `refresh` **不在** `noRecoverScroll` 集内（失败动作兜底会对 `action.completed{refresh, ok:false}` 发一次 `recover_after_refresh_failed` 滚动）；确认 `refresh` 不进互动配额/风控闸 <!-- cloud c4545f0 已确认：noRecoverScroll 仅 follow/browse_images/scroll_comments/comment/comment_like/like/collect -->

## 3. aidcp-edge — 白名单 / switch / 处理器

- [x] 3.1 `src/client/edge-client.ts`（四处同步之三 · **typecheck 抓不到**）：onMessage 主动命令 OR 链加 `env.type === 'feed.refresh'` 放行到 browseHandler；加注释标明「独立主动命令，漏加即静默丢弃（notification-monitor 活锁前车）」 <!-- edge 60088d7 -->
- [x] 3.2 `src/browse/browse-session.ts` `executeCommand` switch：加 `case 'feed.refresh': await this.refreshFeed((env.payload as FeedRefreshPayload).thinkMs); break;` <!-- edge 60088d7 -->
- [x] 3.3 `src/browse/browse-session.ts`：实现 `refreshFeed(thinkMs?)`（URL 闸 → 定位 reload → gate → 验证码复检 → 点前抓 pre-state → 拟人点击 → 后置校验「具体非空新首卡 + scrollY<100」 → 成功报卡+ok:true / 失败诚实回执不报卡） <!-- edge 60088d7 含对抗评审两处硬化 -->
- [x] 3.4 `scripts/feed-refresh-button-probe.ts`：随本 change 提交（真机标定探针） <!-- edge 60088d7 -->

## 4. aidcp（本仓）— 协议文档（四处同步之四）

- [x] 4.1 `docs/protocol.md`：头部计数已由既有 change 修正为 70，本 change +1 到 71；§398/§180 同步；注明表为人工维护 <!-- aidcp main 本提交 -->
- [x] 4.2 `docs/protocol.md` §2.3 新增 `feed.refresh` 行 + §3.7 payload 示例 <!-- aidcp main 本提交 -->

## 5. 测试（克制：关键行为少数用例，真机项转 backlog）

- [x] 5.1 cloud `session-context`：`addFeedCardsBrowsed` 累加（忽略 `<=0`）、`resetFeedCardsBrowsed` 归零、`reset()` 归零 <!-- cloud c4545f0 test/agents/feed-refresh-depth.test.ts -->
- [x] 5.2 cloud `feed-scroller`：达阈值 → `feed.refresh.needed`（非 scroll/search）两计数归零；未达阈值 / disabled → 不变 <!-- cloud c4545f0 -->
- [x] 5.3 cloud command-bridge：`refresh` → `feed.refresh` envelope 带 `reason`+`thinkMs`（dispatcher 层重集成留真机/后续） <!-- cloud c4545f0；page.cards 计数 + 失败兜底为既有well-tested 路径，按克制不另加重 harness 集成用例 -->
- [x] 5.4 两仓 `protocol-contract.test.ts`：`ALL_MESSAGE_TYPES` 加 `'feed.refresh': true`，`AC-PROTO` 计数 70→71 <!-- cloud c4545f0 / edge 60088d7 -->
- [x] 5.5 edge `browse-session`（jsdom 桩）：reload 在 + 后置满足 → ok:true + page.cards；容器缺失 → no_floating_btn；非 feed → wrong_context；点了首卡为空/未变 → not_reloaded 且不报卡 <!-- edge 60088d7 test/browse/browse-session.test.ts -->
- [x] 5.6 两仓：`test:acceptance` → 全量 `test` → `typecheck` 全绿 <!-- cloud 1721 绿 / edge 864+16 绿 -->

## 6. 集成 / 部署 / 真机验收

- [x] 6.1 两仓 land（rebase 最新 master、跑闸）后合默认分支、push <!-- cloud c4545f0→origin/master / edge 60088d7→origin/master，land-change --yes -->
- [x] 6.2 本仓 docs（4.x）+ openspec change 提交、push（additive） <!-- aidcp main 本提交（临时 worktree，主 checkout 在并发分支） -->
- [x] 6.3 部署 dev（备份 → rsync 干净快照 → restart → healthcheck）；默认开启，`AIDCP_FEED_REFRESH=false` kill-switch <!-- 2026-07-10 deployed dev：backup cloud.bak.20260710-165419；service active + 8787/8090 listening + feed.refresh live + 飞书长连接已建立 -->
- [x] 6.4 真机验收项登记 `docs/real-machine-acceptance-backlog.md` 簇 33（端到端触发 / 阈值校准 / 诚实失败 / kill-switch / 宽窄双布局） <!-- aidcp main 本提交 -->
- [ ] 6.5 真机验收通过后：勾选簇 33 → `openspec validate --strict` → archive（archive 前确认无并发 spec 交织）

<!-- 说明：本 change 已实装 + 部署 dev + 登记真机 backlog；archive 待簇 33 真机核实（尤其阈值可达性 + 点刷新真换新批），与仓库「真机验收后再 archive」纪律一致。 -->
