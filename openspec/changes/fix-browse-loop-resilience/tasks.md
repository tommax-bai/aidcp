# Tasks — fix-browse-loop-resilience

> 验收发现见 memory `deepread-back-to-feed-deadlock`；根因与方案见本 change 的 proposal.md / design.md。
> 进度回写规则：完成的 task 标 `[x]` 并在行尾加 HTML 注释 `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。

## 1. aidcp-edge — back_to_feed 死锁修复（blocker, load-bearing）

- [ ] 1.1 `src/browse/browse-session.ts` `navigateBack`：把 `if (targetPage === 'feed')` 扩为覆盖 `targetPage === undefined`（或参数默认 `'feed'`），使无 `targetPage` 的 back 走 `waitForVisibleCards(8000)` 轮询 + `Page.navigate(exploreUrl)` 兜底，取代 `else` 分支的裸 `sleep(2000)` + 瞬时扫描
- [ ] 1.2 `src/browse/browse-session.ts` `reportVisibleCards`：0 卡时先重轮询一次；仍空则显式上报 `page.cards{cards:[]}` 而非静默 `return`（**前置依赖 2.1：若 cloud 对空 cards[] 不安全则不发空报，仅保留重轮询，靠 cloud 续扫兜底**）
- [ ] 1.3 edge `npm run typecheck` + `npm test` 通过

## 2. aidcp-cloud — 续刷 + idle 看门狗（纵深）

- [ ] 2.0 核对 `ContentEvaluator.evaluate` / `FeedScroller` 对空 `page.cards{cards:[]}` 的处理（安全 no-op / 触发 scroll / 还是误判 session.end），据此定 1.2 是否发空报
- [ ] 2.1 `src/orchestrator/role-dispatcher.ts`：`action.completed{action:'back', ok:true}` 触发一次 `sendCommand(scroll, reason='rescan_after_back')`，使 back 自驱动；避开与 `follow`/`browse_images`/`scroll_comments` 的 `noRecoverScroll` 冲突
- [ ] 2.2 `src/agents/session-monitor-role.ts`（+ dispatcher 接线）：新增 wall-clock idle 看门狗（`setInterval`），每次 edge 上报/命令刷新「最后活动时间戳」；超 N 秒发 `scroll` nudge、超 M 秒（M>N）发 `session.should_end`；会话结束/销毁时 `clearInterval`
- [ ] 2.3 cloud `npm run typecheck` + `npm test` 通过（本地仅代码级验证，不起 cloud）

## 3. aidcp-edge — 抽取质量

- [ ] 3.1 正文选择器抽成单一共享列表，`waitForNoteBody`（gate）与 `note-extractor.extractNoteContent`（extractor）复用；拓宽变体候选 `'.note-scroller .note-text'` / `'[class*="note-content"] .note-text'`，仍排除裸 `.note-content`/`[class*=content]`
- [ ] 3.2 `waitForNoteBody` 超时 3500→~5500ms；超时日志按「modal 内是否仍有文本节点」区分「布局变体未命中（需补选择器）」与真·纯图文/视频
- [ ] 3.3 点赞数选择器收紧：`feed-scroller.ts` 去掉末位 `[class*="count"]`（或约束到 `like-wrapper` 内）；`note-extractor.countNear` 先 `like-wrapper` 精确匹配再退 `like` 子串

## 4. aidcp-edge — 回归测试

- [ ] 4.1 `test/browse/browse-session.test.ts`：新增 `navigation.back` 无 `targetPage`（生产实际路径）的回归——断言走轮询分支、空扫不静默
- [ ] 4.2 `test/browse/note-extractor.test.ts`：新增 `note-scroller`/`note-content`（无字面 `#detail-desc`）布局 fixture，断言正文非空且不含 title 前缀/「刚刚」时间串
- [ ] 4.3 likes 口径一致回归：同一 fixture 下 feed 卡与 detail 点赞数口径一致

## 5. aidcp-cloud — 部署（安全序列，仅 cloud 改动后执行）

- [ ] 5.1 ECS 备份当前版本：`/opt/aidcp/cloud.bak.<ts>.tar.gz` + `.env.bak.<date>`
- [ ] 5.2 `rsync`（排除 .env/node_modules/.git）→ `systemctl restart aidcp-cloud.service` → healthcheck（active + 8787 监听 + 飞书长连 + PG `select 1`）；**绝不触碰同机 isales**
- [ ] 5.3 失败即回滚到备份并复核

## 6. 真机验收复跑（中控触发，edge 连 ECS）

- [ ] 6.1 重跑 5 分钟**带时间戳**真机验收，验证：back 后续扫触发、循环连续跑多篇笔记、无 ~4min 静默
- [ ] 6.2 验证 `action.completed{back}` → 下一条 `page.cards`/命令的间隔 <10s；并抓 cloud `[RoleDispatcher] action.completed: back ok=true` 与续扫日志
- [ ] 6.3 抽查正文抽取：长文笔记正文非空、点赞数 feed/detail 一致；验收结果回写本 tasks.md

## 7. 收尾

- [ ] 7.1 `openspec validate fix-browse-loop-resilience --strict` 通过
- [ ] 7.2 archive（delta 合并进 `openspec/specs/`）
