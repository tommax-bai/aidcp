# Tasks — fix-browse-loop-resilience

> 验收发现见 memory `deepread-back-to-feed-deadlock`；根因与方案见本 change 的 proposal.md / design.md。
> 进度回写规则：完成的 task 标 `[x]` 并在行尾加 HTML 注释 `<!-- <repo> <commit-sha> 备注 -->`（部署后追加 `<!-- <date> deployed -->`）。

## 1. aidcp-edge — back_to_feed 死锁修复（blocker, load-bearing）

- [x] 1.1 `src/browse/browse-session.ts` `navigateBack`：`undefined` 等同 `'feed'`，按 URL 严格判定是否真在 feed，不在即 `Page.navigate(exploreUrl)` 兜底 <!-- aidcp-edge 063a9f5 实测发现仅"undefined→feed 分支"不够：深读用 Page.navigate 进主页，history.back 只回到详情页(/explore/<id>)到不了 feed，过渡态 scroller 瞬时误计→跳过兜底。改为 history.back 后按 EXPLORE_FEED_RE 判定 URL，非 feed 即整页 Page.navigate(exploreUrl)+waitForCards+waitForVisibleCards -->
- [x] 1.2 `src/browse/browse-session.ts` `reportVisibleCards`：0 卡时再轮询一轮等水合，避免静默吞 0 卡 <!-- aidcp-edge 063a9f5 只做了"重轮询兜底"；"显式上报空 page.cards{cards:[]}"暂缓——前置 2.0 未核对 cloud 对空 cards[] 是否安全，且 1.1 的 URL 兜底已能可靠回到有卡 feed，显式空报暂非必需 -->
- [x] 1.3 edge `npm run typecheck` + `npm test` 通过 <!-- aidcp-edge 063a9f5 typecheck 0 err；测试 212→214（含 2 个新回归）全过 -->
- [x] 1.4 `src/browse/browse-session.ts` `ensureExplore`：同一 bug 家族第三面——启动若停在详情页，松判断 `url.includes('/explore')` 误当已在 feed → 不导航。改为按 `EXPLORE_FEED_RE` 严格判定，详情页启动时导航回 feed <!-- aidcp-edge 063a9f5 验收 run#3 启动即卡死暴露；run#4 日志确认自愈"不在 explore feed…导航到…" -->
- [x] 1.5 抽共享常量 `EXPLORE_FEED_RE`（`/explore` 列表，排除 `/explore/<noteId>` 详情），`navigateBack` 与 `ensureExplore` 复用，避免判定漂移 <!-- aidcp-edge 063a9f5 -->

## 2. aidcp-cloud — 续刷 + idle 看门狗（纵深）

- [x] 2.0 核对空 `page.cards{cards:[]}` 处理 <!-- 结论：SAFE。空卡 → page.cards.arrived → ContentEvaluator candidates=[] → content.no_valuable(all_cards_visited) → FeedScroller → feed.scrolled → scroll；从不触发 session.end（仅 SessionMonitor 经 session.should_end 才结束）。已有 role-dispatcher.test.ts 路径A 佐证。故 edge 显式空报本安全，但 1.2 仍只做重轮询不发空报（非必需，避免叠加） -->
- [~] 2.1 ~~back+ok:true 无条件续扫~~ **经 scout 分析不实装** <!-- aidcp-cloud d1d8a9b 偏离：edge navigateBack 已在 back 回执前主动 reportVisibleCards 上报 page.cards、cloud 自动 evaluate；再无条件发 scroll 会多滚一屏跳过未评估卡 + 污染 SEARCH_THRESHOLD 计数器。停滞兜底改由 2.2 看门狗承担（仅真无活动时介入），更干净 -->
- [x] 2.2 `src/agents/session-monitor-role.ts` + dispatcher 接线：wall-clock idle 看门狗 <!-- aidcp-cloud d1d8a9b 可注入 setIntervalFn/clock+unref；刷新事件 page.cards.arrived/note.detail.arrived/profile.detail.arrived/action.completed；idleNudgeMs 默认 130s(>pacing capMs 90s 防误触)→session.idle_nudge(节流)，idleEndMs 默认 240s→session.should_end；unsubscribe 清 interval。新增 RoleEventMap 'session.idle_nudge' → dispatcher 翻译为 scroll(idle_recover_nudge) -->
- [x] 2.3 cloud `npm run typecheck` + `npm test` 通过 <!-- aidcp-cloud d1d8a9b typecheck 0 err；162→167（+4 单元 +1 集成）全过；本地未起 cloud -->

## 3. aidcp-edge — 抽取质量

- [x] 3.1 正文选择器抽成共享常量 `NOTE_BODY_SELECTORS`，gate(`waitForNoteBody`) 与 extractor 复用；拓宽 `.note-scroller .note-text`/`[class*="note-content"] .note-text`/`.desc`，仍排除裸 `.note-content`/`[class*=content]` <!-- aidcp-edge 0c88fdd gate 把列表 JSON.stringify 进 CDP eval -->
- [x] 3.2 `waitForNoteBody` 超时 3500→5500ms；超时日志按「modal 内 .note-scroller/[class*=note-content] 是否仍有文本」区分「布局变体未命中（需补 NOTE_BODY_SELECTORS）」与真·纯图文/视频 <!-- aidcp-edge 0c88fdd -->
- [x] 3.3 `feed-scroller.ts` 去掉贪婪 `[class*="count"]` 末位兜底（仅取 like 作用域内计数）；`note-extractor.countNear` 改两遍扫描（先 `like-wrapper` 精确再退 `like` 子串） <!-- aidcp-edge 0c88fdd -->

## 4. aidcp-edge — 回归测试

- [x] 4.1 `test/browse/browse-session.test.ts`：新增 `navigation.back` 无 `targetPage`（生产实际路径）的回归——断言走轮询分支、空扫不静默 <!-- aidcp-edge 063a9f5 另补一条：启动停在详情页 → ensureExplore 导航回 feed 的回归 -->
<!-- 注：4.1 已覆盖回 feed 的两条路径；4.2/4.3（note body 布局变体 + likes 口径）属抽取质量(task 3)，与 task 3 一起做 -->
<!-- 验收已先行（edge 修复部分）：run#4 5 分钟真机 6 篇连续闭环、5 次 back 续刷全 <10s、无可见卡片静默 0；对应 6.1/6.2 的 edge 验证。完整 6.x 验收在 cloud 纵深(2.x)部署后再跑一次。 -->

- [x] 4.2 `test/browse/note-extractor.test.ts`：新增 `note-scroller`/`note-content`（无字面 `#detail-desc`）布局 fixture，断言正文非空且不含 title 前缀/「刚刚」 <!-- aidcp-edge 0c88fdd -->
- [x] 4.3 likes 口径回归：同一 fixture 断言 `countNear` 两遍扫描取 like-wrapper(123) 而非靠前含 `like` 子串的 entry-like-tip(999) <!-- aidcp-edge 0c88fdd 注：feed/detail 严格一致需真机核对，单测覆盖选择器优先级 -->
<!-- cloud 看门狗单元测试(4)+集成测试(1) 见 aidcp-cloud d1d8a9b test/agents/session-monitor-role.test.ts + test/integration/role-dispatcher.test.ts -->


## 5. aidcp-cloud — 部署（安全序列，仅 cloud 改动后执行）

- [x] 5.1 ECS 备份 <!-- /opt/aidcp/cloud.bak.20260617-171740.tar.gz（exclude node_modules）+ .env.bak.20260617-171740 -->
- [x] 5.2 rsync src/（仅 3 文件：session-monitor-role.ts/types.ts/role-dispatcher.ts，无 --delete）→ restart → healthcheck 全绿 <!-- aidcp-cloud d1d8a9b deployed 2026-06-17 17:18：active(MainPID 1389120,NRestarts 0) + 8787 监听 + 飞书长连接已建立 + PG 锚点缓存已就绪(DB 通) + RoleDispatcher 启动无报错 + 看门狗代码 idle_nudge grep 0→2。isales 未触碰 -->
- [x] 5.3 失败回滚预案：备份在手，healthcheck 通过未触发回滚 <!-- 回滚命令：tar -xzf cloud.bak.20260617-171740.tar.gz -C /opt/aidcp && systemctl restart aidcp-cloud.service -->

## 6. 真机验收复跑（中控触发，edge 连 ECS）

- [x] 6.1 部署后 run#5（5分12秒，cloud 看门狗已生效）：note.open 7 篇连续闭环、navigation.back 6 次、page.cards 9 次、**无可见卡片静默 0**、ensureExplore 自愈 1 <!-- 2026-06-17 17:18-17:23 -->
- [x] 6.2 back→下一屏出卡间隔 10/6/5/7/6/6s 全部 ≤10s、无长静默；**★ idle_recover_nudge(看门狗误触)=0**（阈值 130s>停留上限 90s 不误触正常停留）；真异常=0（grep 命中的"失败"是笔记标题字样，非错误）
- [x] 6.3 抽取抽查：本轮 7 篇正文均非空、布局变体未命中 0、纯图文抽空 0；点赞数去贪婪后个别卡显示空（"宁空不错"预期）；feed/detail 严格一致仍需更大样本核对 <!-- 收藏 5 关注 3 -->

## 7. 收尾

- [x] 7.1 `openspec validate fix-browse-loop-resilience --strict` 通过 <!-- 4/4 artifacts complete -->
- [ ] 7.2 archive（delta 合并进 `openspec/specs/`）<!-- 全部实装+部署+验收完成，可执行 /opsx:archive；待确认 -->
