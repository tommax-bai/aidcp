## Why

2026-06-17 的 5 分钟真机全流程验收里，深读链路单篇闭环（note.open → browse_images → scroll_comments → collect → profile.open 抓粉丝数 → follow）全部正常，但 `navigation.back(back_to_feed)` 之后整个浏览循环**死锁** ~4 分钟直到外部 SIGTERM——5 分钟只跑完 1 篇笔记。根因是边-云互等：cloud 下发的 `navigation.back` 不带 `targetPage`，edge 因此走未轮询的 `else` 分支（裸 `history.back()` + 固定 `sleep(2000)`），feed 未水合即扫到 0 卡，`reportVisibleCards` 静默 `return` 不发 `page.cards`，edge 阻塞在 `waitForCommand()`；而 cloud 只靠 `page.cards.arrived` 推进、对 `action.completed{back,ok:true}` 无续刷动作、且 orchestration 内无任何 wall-clock 看门狗。这是已知「空扫→死锁」修复（`0a78363`/`3bffc50`）的**未覆盖孪生路径**——修复只落在 `targetPage==='feed'` 分支与初始路径，而生产实际走的是 `else` 分支，测试又全用 `targetPage:'feed'` 把它掩盖了。验收同时暴露两个抽取质量问题（长文正文抽空、点赞数口径不一致）。这些缺陷使自动浏览实际只能跑 1 篇就停摆，必须修复才能让 deepread 链路在真机上持续运转。

## What Changes

- **[BLOCKER] edge `navigateBack` 覆盖默认 back_to_feed 路径**：`targetPage===undefined` 与 `'feed'` 同等处理，走 `waitForVisibleCards(8000)` 轮询 + `Page.navigate(exploreUrl)` 兜底，取代裸 `sleep(2000)` + 瞬时扫描。
- **[BLOCKER] edge `reportVisibleCards` 不再静默吞 0 卡**：空扫时先重轮询一次，仍为空则显式上报空 `page.cards`（而非 `return`），让 cloud 决策环始终能被触发。
- **[纵深] cloud `back` 自驱动续刷**：`action.completed{action:'back', ok:true}` 触发一次 `scroll`（`reason=rescan_after_back`），使续刷不依赖 edge 主动重报。
- **[纵深] cloud idle 看门狗**：新增 wall-clock 定时器，N 秒无 edge 上报/命令活动则发 `scroll` nudge，更久则 `session.should_end`，使停滞会话自愈而非等外部强杀。
- **[质量] 正文抽取选择器拓宽并同步**：`waitForNoteBody`（gate）与 `extractNoteContent`（extractor）共用同一份 body 选择器列表，覆盖 `note-scroller`/`note-content` 布局变体（仍不回退裸 `.note-content`/`[class*=content]` 以免「标题…刚刚」泄漏）；超时阈值提到 ~5-6s；超时日志区分「布局变体未命中」与真·纯图文/视频。
- **[质量] 点赞数选择器口径统一**：`feed-scroller` 去掉贪婪 `[class*=count]` 末位兜底，`note-extractor.countNear` 优先 `like-wrapper` 精确匹配，消除 feed `👍11` vs detail `👍1` 的不一致。
- **[测试] 补回归**：覆盖 `navigation.back` 无 `targetPage` 的生产路径；断言 `note-scroller`/`note-content`（无字面 `#detail-desc`）布局下正文非空。

## Capabilities

### New Capabilities
- `browse-loop-resilience`: 浏览循环的存活性与自愈契约——返回 feed 后必须续刷而非死锁、feed 重扫须等水合再判定、空扫不得静默吞掉、会话在有界 idle 内必须自愈或终止（cloud 看门狗）。
- `note-extraction-fidelity`: 详情页内容抽取保真契约——文本笔记正文须跨布局变体被抽到（不因选择器过窄而假阴性）、点赞数在 feed 卡与详情页须口径一致、抽取失败须如实记录而非谎报笔记类型。

### Modified Capabilities
<!-- 无：本 change 不修改已合并到 openspec/specs/ 的现有 spec（当前仅 command-pacing，与本变更无 spec 级交集）。 -->

## Impact

- **edge（aidcp-edge，master）**：`src/browse/browse-session.ts`（`navigateBack` / `reportVisibleCards` / `waitForNoteBody`）、`src/browse/note-extractor.ts`（body 选择器 / `countNear`）、`src/browse/feed-scroller.ts`（likes 选择器）；`test/browse/*` 补回归。
- **cloud（aidcp-cloud，master，部署在 ECS）**：`src/orchestrator/role-dispatcher.ts`（`action.completed{back}` 续刷）、`src/agents/session-monitor-role.ts`（idle wall-clock 看门狗）；改动须走部署安全序列（备份 + rsync + `systemctl restart aidcp-cloud.service` + healthcheck + 失败回滚），绝不触碰同机 isales。
- **协议**：不改 `protocol.ts` 报文形状；`navigation.back` 的 `targetPage` 字段语义保持向后兼容（缺省即按 feed 处理）。
- **验收**：重跑 5 分钟带时间戳真机验收，验证 back 后续刷触发、循环连续多篇、无 ~4min 静默、`action.completed{back}` 到下一条 `page.cards`/命令间隔 <10s。
